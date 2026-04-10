"""Walk-forward validation for the ETF momentum strategy.

Methodology
-----------
Uses an *expanding* training window anchored to 2007-01-01.  After each
training period the grid-search optimizer selects the best parameter set
(highest Sharpe ratio).  Those parameters are then applied to the
immediately-following out-of-sample (OOS) test window, which advances by
two years each round.

Windows
-------
  W1: Train 2007-01-01 → 2013-12-31 | Test 2014-01-01 → 2015-12-31
  W2: Train 2007-01-01 → 2015-12-31 | Test 2016-01-01 → 2017-12-31
  W3: Train 2007-01-01 → 2017-12-31 | Test 2018-01-01 → 2019-12-31
  W4: Train 2007-01-01 → 2019-12-31 | Test 2020-01-01 → 2021-12-31
  W5: Train 2007-01-01 → 2021-12-31 | Test 2022-01-01 → 2023-12-31
  W6: Train 2007-01-01 → 2023-12-31 | Test 2024-01-01 → 2026-04-08

Design notes
------------
- Price data is fetched *once* from the cache (or API) and sliced per window.
- Volatility regime switching is intentionally disabled so walk-forward
  isolates the three grid-search parameters: SMA window, ROC lookback, Top N.
- Monthly rebalancing is used for all windows (same as the original optimizer).
- The SGOV/BIL proxy fix in data_fetcher is inherited automatically.
"""

import itertools
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from . import config
from .data_fetcher import fetch_all_data, load_data_from_cache
from .etf_loader import load_universe_by_name
from .report import calculate_metrics
from .rs_engine import generate_signals, get_qualifying_etfs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Walk-forward window definitions
# ---------------------------------------------------------------------------

WINDOWS = [
    {"window": 1, "train_start": "2007-01-01", "train_end": "2013-12-31",
     "test_start": "2014-01-01", "test_end": "2015-12-31"},
    {"window": 2, "train_start": "2007-01-01", "train_end": "2015-12-31",
     "test_start": "2016-01-01", "test_end": "2017-12-31"},
    {"window": 3, "train_start": "2007-01-01", "train_end": "2017-12-31",
     "test_start": "2018-01-01", "test_end": "2019-12-31"},
    {"window": 4, "train_start": "2007-01-01", "train_end": "2019-12-31",
     "test_start": "2020-01-01", "test_end": "2021-12-31"},
    {"window": 5, "train_start": "2007-01-01", "train_end": "2021-12-31",
     "test_start": "2022-01-01", "test_end": "2023-12-31"},
    {"window": 6, "train_start": "2007-01-01", "train_end": "2023-12-31",
     "test_start": "2024-01-01", "test_end": "2026-04-08"},
]

# Parameter grid — identical to optimizer.py
SMA_WINDOWS_MONTHS = [6, 8, 10, 12]
ROC_LOOKBACKS_MONTHS = [1, 3, 6]
TOP_N_VALUES = [3, 5, 7, 10]

PARAM_GRID = list(itertools.product(
    [m * 21 for m in SMA_WINDOWS_MONTHS],
    [m * 21 for m in ROC_LOOKBACKS_MONTHS],
    TOP_N_VALUES,
))  # 48 combinations


# ---------------------------------------------------------------------------
# Parameterized signal selection (no config reads for sma/roc)
# ---------------------------------------------------------------------------

def _select_tickers(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    evaluation_date: pd.Timestamp,
    sma_window: int,
    roc_lookback: int,
    top_n: int,
) -> List[str]:
    """Select top-N ETFs using explicit parameters (no config dependency)."""
    price_slice = price_data[price_data.index <= evaluation_date]

    signals = generate_signals(
        price_data=price_slice,
        spy_ticker=config.BENCHMARK_TICKER,
        etf_tickers=etf_tickers,
        sma_window=sma_window,
        roc_lookback=roc_lookback,
    )

    qualifying = get_qualifying_etfs(signals, evaluation_date)
    selected = list(qualifying.head(top_n)["ticker"]) if not qualifying.empty else []

    if len(selected) < top_n:
        selected.append(config.BENCHMARK_TICKER)

    # SGOV comparison — replace underperformers with cash proxy
    if config.CASH_TICKER in price_slice.columns:
        sgov_prices = price_slice[config.CASH_TICKER]
        if evaluation_date in sgov_prices.index:
            sgov_roc = sgov_prices.pct_change(periods=roc_lookback).loc[evaluation_date]
            if not pd.isna(sgov_roc):
                final = []
                for ticker in selected:
                    if ticker in price_slice.columns:
                        tkr_roc = price_slice[ticker].pct_change(periods=roc_lookback).loc[evaluation_date]
                        if not pd.isna(tkr_roc) and tkr_roc < sgov_roc:
                            ticker = config.CASH_TICKER
                    final.append(ticker)
                seen: set = set()
                selected = [t for t in final if not (t in seen or seen.add(t))]  # type: ignore[func-returns-value]

    return selected


# ---------------------------------------------------------------------------
# Core simulation (no API calls, no volatility regime — param sweep only)
# ---------------------------------------------------------------------------

def _run_simulation(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    start_date: str,
    end_date: str,
    sma_window: int,
    roc_lookback: int,
    top_n: int,
    initial_capital: float = 100_000.0,
) -> Tuple[pd.Series, pd.Series]:
    """
    Run a monthly-rebalanced backtest on pre-loaded price data.

    Returns
    -------
    strategy_values : pd.Series  (daily portfolio values)
    benchmark_values : pd.Series (SPY buy-and-hold values)
    """
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    trading_dates = price_data.index[mask]

    if len(trading_dates) < 30:
        raise ValueError(f"Too few trading days ({len(trading_dates)}) for {start_date}→{end_date}")

    # Monthly rebalance dates (first trading day of each month)
    rebalance_dates = []
    current_month = None
    for d in trading_dates:
        ym = (d.year, d.month)
        if ym != current_month:
            rebalance_dates.append(d)
            current_month = ym

    # Benchmark: SPY buy-and-hold
    spy_start = price_data.loc[trading_dates[0], config.BENCHMARK_TICKER]
    spy_shares = initial_capital / spy_start
    benchmark_values = price_data.loc[trading_dates, config.BENCHMARK_TICKER] * spy_shares

    # Strategy simulation
    portfolio_value = pd.Series(index=trading_dates, dtype=float)
    portfolio_value.iloc[0] = initial_capital

    current_holdings: Dict[str, float] = {}
    stop_levels: Dict[str, float] = {}

    rebalance_set = set(rebalance_dates)
    next_reb_idx = 0
    next_reb_date = rebalance_dates[0]

    for i, date in enumerate(trading_dates):
        # Rebalance
        if date >= next_reb_date:
            selected = _select_tickers(
                price_data=price_data,
                etf_tickers=etf_tickers,
                evaluation_date=date,
                sma_window=sma_window,
                roc_lookback=roc_lookback,
                top_n=top_n,
            )
            weight = 1.0 / len(selected)
            current_holdings = {t: weight for t in selected}
            stop_levels = {}
            for ticker in current_holdings:
                if ticker in price_data.columns and pd.notna(price_data.loc[date, ticker]):
                    stop_levels[ticker] = price_data.loc[date, ticker] * config.STOP_LOSS_THRESHOLD

            next_reb_idx += 1
            next_reb_date = (rebalance_dates[next_reb_idx]
                             if next_reb_idx < len(rebalance_dates)
                             else pd.Timestamp.max)

        if i == 0:
            continue

        # Stop-loss check
        stopped_out = []
        for ticker in list(current_holdings):
            if ticker == config.CASH_TICKER:
                continue
            if ticker in stop_levels and ticker in price_data.columns:
                curr_price = price_data.loc[date, ticker]
                if pd.notna(curr_price) and curr_price < stop_levels[ticker]:
                    stopped_out.append(ticker)

        if stopped_out:
            stopped_weight = sum(current_holdings.pop(t) for t in stopped_out)
            for t in stopped_out:
                stop_levels.pop(t, None)
            current_holdings[config.CASH_TICKER] = (
                current_holdings.get(config.CASH_TICKER, 0.0) + stopped_weight
            )

        # Daily return
        prev_date = trading_dates[i - 1]
        port_ret = 0.0
        for ticker, weight in current_holdings.items():
            if ticker not in price_data.columns:
                continue
            prev_p = price_data.loc[prev_date, ticker]
            curr_p = price_data.loc[date, ticker]
            if pd.notna(prev_p) and pd.notna(curr_p) and prev_p != 0:
                port_ret += weight * (curr_p - prev_p) / prev_p

        portfolio_value.loc[date] = portfolio_value.loc[prev_date] * (1 + port_ret)

    return portfolio_value, benchmark_values


# ---------------------------------------------------------------------------
# Grid search on one training window
# ---------------------------------------------------------------------------

def _optimize_window(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    train_start: str,
    train_end: str,
) -> Tuple[int, int, int, float]:
    """
    Grid-search 48 combinations on the training window.

    Returns
    -------
    best_sma, best_roc, best_top_n, best_sharpe
    """
    best_sharpe = -np.inf
    best_params = (210, 63, 3)

    for sma_window, roc_lookback, top_n in PARAM_GRID:
        try:
            strat_vals, _ = _run_simulation(
                price_data=price_data,
                etf_tickers=etf_tickers,
                start_date=train_start,
                end_date=train_end,
                sma_window=sma_window,
                roc_lookback=roc_lookback,
                top_n=top_n,
            )
            metrics = calculate_metrics(
                portfolio_values=strat_vals,
                initial_capital=100_000.0,
                risk_free_rate=config.RISK_FREE_RATE,
            )
            if metrics["sharpe_ratio"] > best_sharpe:
                best_sharpe = metrics["sharpe_ratio"]
                best_params = (sma_window, roc_lookback, top_n)
        except Exception:
            continue

    return best_params[0], best_params[1], best_params[2], best_sharpe


# ---------------------------------------------------------------------------
# Main walk-forward runner
# ---------------------------------------------------------------------------

def run_walk_forward(
    universe: str = "sp500",
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Run full walk-forward validation.

    For each window:
      1. Optimize on the training period (48 combinations, monthly rebalance)
      2. Record in-sample Sharpe with the best parameters
      3. Apply best parameters to the test period (OOS)
      4. Record OOS Sharpe, return, and drawdown

    Also produces a continuous OOS equity curve by chaining test windows.

    Parameters
    ----------
    universe : str
        ETF universe ('sp500', 'developed', 'emerging')
    output_dir : Path, optional
        Where to save CSV and text reports. Defaults to output/walk_forward/

    Returns
    -------
    pd.DataFrame with one row per window containing IS and OOS metrics.
    """
    if output_dir is None:
        output_dir = config.OUTPUT_DIR / "walk_forward"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("WALK-FORWARD VALIDATION")
    logger.info("=" * 70)
    logger.info(f"Universe: {universe}")
    logger.info(f"Windows: {len(WINDOWS)}")
    logger.info(f"Parameter combinations per window: {len(PARAM_GRID)}")
    logger.info(f"Total backtests: {len(WINDOWS) * len(PARAM_GRID) * 2}")

    # Load ETF universe
    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())
    all_tickers = etf_tickers + [config.BENCHMARK_TICKER, config.CASH_TICKER]

    # Fetch price data once (uses BIL proxy if needed)
    logger.info("\nLoading price data...")
    if config.PRICE_DATA_CACHE.exists():
        price_data = load_data_from_cache(str(config.PRICE_DATA_CACHE))
        logger.info(f"Loaded from cache: {price_data.shape}")
    else:
        logger.info("Cache not found — fetching from API (this will take a few minutes)...")
        price_data = fetch_all_data(
            ticker_list=all_tickers,
            start_date=config.DATA_START_DATE,
            end_date="2026-04-08",
            api_key=config.FMP_API_KEY,
            api_delay=config.FMP_API_DELAY,
        )

    results = []
    oos_curves: List[pd.Series] = []  # for combined OOS equity curve

    for w in WINDOWS:
        wn = w["window"]
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Window {wn}/6")
        logger.info(f"  Train: {w['train_start']} → {w['train_end']}")
        logger.info(f"  Test:  {w['test_start']} → {w['test_end']}")

        # ---- Step 1: Optimize on training window ----
        logger.info(f"  Running grid search ({len(PARAM_GRID)} combinations)...")
        t0 = datetime.now()
        best_sma, best_roc, best_top_n, is_sharpe = _optimize_window(
            price_data=price_data,
            etf_tickers=etf_tickers,
            train_start=w["train_start"],
            train_end=w["train_end"],
        )
        elapsed = (datetime.now() - t0).total_seconds()
        logger.info(f"  Best params: SMA={best_sma//21}mo, ROC={best_roc//21}mo, TopN={best_top_n} "
                    f"| IS Sharpe={is_sharpe:.3f} | ({elapsed:.1f}s)")

        # ---- Step 2: In-sample full metrics ----
        is_strat, is_bench = _run_simulation(
            price_data=price_data,
            etf_tickers=etf_tickers,
            start_date=w["train_start"],
            end_date=w["train_end"],
            sma_window=best_sma,
            roc_lookback=best_roc,
            top_n=best_top_n,
        )
        is_metrics = calculate_metrics(is_strat, 100_000.0, config.RISK_FREE_RATE)
        is_bench_metrics = calculate_metrics(is_bench, 100_000.0, config.RISK_FREE_RATE)

        # ---- Step 3: OOS test with best params ----
        oos_strat, oos_bench = _run_simulation(
            price_data=price_data,
            etf_tickers=etf_tickers,
            start_date=w["test_start"],
            end_date=w["test_end"],
            sma_window=best_sma,
            roc_lookback=best_roc,
            top_n=best_top_n,
        )
        oos_metrics = calculate_metrics(oos_strat, 100_000.0, config.RISK_FREE_RATE)
        oos_bench_metrics = calculate_metrics(oos_bench, 100_000.0, config.RISK_FREE_RATE)

        logger.info(f"  OOS → Return={oos_metrics['total_return']*100:.1f}%  "
                    f"Sharpe={oos_metrics['sharpe_ratio']:.3f}  "
                    f"MaxDD={oos_metrics['max_drawdown']*100:.1f}%  "
                    f"vs SPY: {(oos_metrics['total_return']-oos_bench_metrics['total_return'])*100:+.1f}pp")

        # Accumulate OOS curve (normalize each segment to start at 1.0)
        oos_curves.append(oos_strat / oos_strat.iloc[0])

        results.append({
            "window": wn,
            "train_start": w["train_start"],
            "train_end": w["train_end"],
            "test_start": w["test_start"],
            "test_end": w["test_end"],
            # Best params
            "best_sma_months": best_sma // 21,
            "best_roc_months": best_roc // 21,
            "best_top_n": best_top_n,
            # In-sample
            "is_sharpe": round(is_sharpe, 3),
            "is_return_pct": round(is_metrics["total_return"] * 100, 2),
            "is_annualized_pct": round(is_metrics["annualized_return"] * 100, 2),
            "is_max_dd_pct": round(is_metrics["max_drawdown"] * 100, 2),
            "is_spy_sharpe": round(is_bench_metrics["sharpe_ratio"], 3),
            # Out-of-sample
            "oos_sharpe": round(oos_metrics["sharpe_ratio"], 3),
            "oos_return_pct": round(oos_metrics["total_return"] * 100, 2),
            "oos_annualized_pct": round(oos_metrics["annualized_return"] * 100, 2),
            "oos_max_dd_pct": round(oos_metrics["max_drawdown"] * 100, 2),
            "oos_spy_return_pct": round(oos_bench_metrics["total_return"] * 100, 2),
            "oos_spy_sharpe": round(oos_bench_metrics["sharpe_ratio"], 3),
            "oos_outperformance_pp": round(
                (oos_metrics["total_return"] - oos_bench_metrics["total_return"]) * 100, 2
            ),
            "oos_beats_spy": oos_metrics["total_return"] > oos_bench_metrics["total_return"],
        })

    df = pd.DataFrame(results)

    # ---- Build combined OOS equity curve ----
    # Chain segments: each segment picks up from the end of the previous one
    if oos_curves:
        combined_curve = oos_curves[0]
        for segment in oos_curves[1:]:
            scale = combined_curve.iloc[-1]
            combined_curve = pd.concat([combined_curve, segment * scale])
        combined_curve = (combined_curve * 100_000.0).rename("oos_portfolio_value")
        combined_curve.to_csv(output_dir / "oos_equity_curve.csv")
        logger.info(f"\nCombined OOS equity curve saved → {output_dir / 'oos_equity_curve.csv'}")

    # ---- Save results ----
    results_path = output_dir / "walk_forward_results.csv"
    df.to_csv(results_path, index=False)
    logger.info(f"Window results saved → {results_path}")

    # ---- Generate text report ----
    _generate_report(df, oos_curves, output_dir, universe)

    return df


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _generate_report(
    df: pd.DataFrame,
    oos_curves: List[pd.Series],
    output_dir: Path,
    universe: str,
) -> None:
    """Write the walk-forward summary report."""

    report_path = output_dir / "walk_forward_report.txt"

    # Aggregate OOS stats
    avg_oos_sharpe = df["oos_sharpe"].mean()
    avg_is_sharpe = df["is_sharpe"].mean()
    decay_ratio = avg_oos_sharpe / avg_is_sharpe if avg_is_sharpe > 0 else 0
    windows_beat_spy = df["oos_beats_spy"].sum()

    # Combined OOS return (chain all segments)
    if oos_curves:
        combined_final = 1.0
        for seg in oos_curves:
            combined_final *= (seg.iloc[-1] / seg.iloc[0])
        combined_oos_return = (combined_final - 1.0) * 100
    else:
        combined_oos_return = 0.0

    # Stable parameter — check if same params chosen in most windows
    most_common_sma = df["best_sma_months"].mode().iloc[0]
    most_common_roc = df["best_roc_months"].mode().iloc[0]
    most_common_topn = df["best_top_n"].mode().iloc[0]

    with open(report_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("WALK-FORWARD VALIDATION REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Universe:    {universe.upper()}\n")
        f.write(f"Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Windows:     {len(df)}\n")
        f.write(f"Grid:        {len(PARAM_GRID)} combinations "
                f"(SMA {SMA_WINDOWS_MONTHS}mo × ROC {ROC_LOOKBACKS_MONTHS}mo × TopN {TOP_N_VALUES})\n")
        f.write(f"Rebalance:   Monthly (vol-regime disabled for clean parameter isolation)\n\n")

        f.write("=" * 70 + "\n")
        f.write("AGGREGATE OOS RESULTS\n")
        f.write("=" * 70 + "\n")
        f.write(f"Combined OOS total return:    {combined_oos_return:.1f}%\n")
        f.write(f"Average OOS Sharpe ratio:     {avg_oos_sharpe:.3f}\n")
        f.write(f"Average IS  Sharpe ratio:     {avg_is_sharpe:.3f}\n")
        f.write(f"OOS/IS Sharpe decay ratio:    {decay_ratio:.2f}  "
                f"({'ROBUST' if decay_ratio >= 0.70 else 'MODERATE' if decay_ratio >= 0.50 else 'CONCERN'})\n")
        f.write(f"Windows beating SPY (OOS):    {windows_beat_spy}/{len(df)}\n\n")

        f.write("Decay ratio guide:\n")
        f.write("  >= 0.70  → Strategy is robust, parameters generalize well\n")
        f.write("  0.50-0.70 → Moderate degradation, strategy concept valid\n")
        f.write("  < 0.50   → Significant overfitting, parameters may not generalize\n\n")

        f.write("=" * 70 + "\n")
        f.write("PARAMETER STABILITY\n")
        f.write("=" * 70 + "\n")
        f.write(f"Most frequently chosen params across all windows:\n")
        f.write(f"  SMA:   {most_common_sma} months\n")
        f.write(f"  ROC:   {most_common_roc} months\n")
        f.write(f"  Top N: {most_common_topn}\n\n")
        f.write("Params chosen per window:\n")
        for _, row in df.iterrows():
            stable = (row["best_sma_months"] == most_common_sma and
                      row["best_roc_months"] == most_common_roc and
                      row["best_top_n"] == most_common_topn)
            f.write(f"  W{int(row['window'])}: SMA={row['best_sma_months']}mo "
                    f"ROC={row['best_roc_months']}mo "
                    f"TopN={row['best_top_n']}"
                    f"{'  ← matches consensus' if stable else ''}\n")

        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("WINDOW-BY-WINDOW RESULTS\n")
        f.write("=" * 70 + "\n\n")

        for _, row in df.iterrows():
            f.write(f"Window {int(row['window'])}: Train {row['train_start']}→{row['train_end']} "
                    f"| Test {row['test_start']}→{row['test_end']}\n")
            f.write(f"  Best params:  SMA={row['best_sma_months']}mo, "
                    f"ROC={row['best_roc_months']}mo, TopN={row['best_top_n']}\n")
            f.write(f"  In-sample:    Sharpe={row['is_sharpe']:.3f}  "
                    f"Return={row['is_return_pct']:.1f}%  "
                    f"MaxDD={row['is_max_dd_pct']:.1f}%\n")
            f.write(f"  Out-of-sample: Sharpe={row['oos_sharpe']:.3f}  "
                    f"Return={row['oos_return_pct']:.1f}%  "
                    f"MaxDD={row['oos_max_dd_pct']:.1f}%  "
                    f"vs SPY: {row['oos_outperformance_pp']:+.1f}pp  "
                    f"({'BEAT' if row['oos_beats_spy'] else 'MISSED'})\n\n")

        f.write("=" * 70 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 70 + "\n")
        if decay_ratio >= 0.70:
            verdict = (
                "ROBUST: The strategy's OOS Sharpe is within 30% of its IS Sharpe. "
                "Parameters generalize across market regimes. "
                "Confidence in live deployment is supported by this test."
            )
        elif decay_ratio >= 0.50:
            verdict = (
                "MODERATE: OOS Sharpe degrades noticeably vs IS but strategy still "
                "adds value. Consider using a parameter ensemble or looser settings "
                "to reduce overfitting. Strategy concept is valid."
            )
        else:
            verdict = (
                "CONCERN: OOS Sharpe is less than 50% of IS Sharpe. "
                "The parameters are likely overfit to recent history. "
                "Do not deploy without further investigation and re-optimization "
                "with walk-forward constraints."
            )
        f.write(f"\n{verdict}\n")

    print("\n" + "=" * 70)
    print("WALK-FORWARD VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Combined OOS total return:  {combined_oos_return:.1f}%")
    print(f"Avg OOS Sharpe:             {avg_oos_sharpe:.3f}")
    print(f"Avg IS  Sharpe:             {avg_is_sharpe:.3f}")
    print(f"OOS/IS decay ratio:         {decay_ratio:.2f}")
    print(f"Windows beating SPY (OOS):  {windows_beat_spy}/{len(df)}")
    print(f"\nReport → {report_path}")
    print(f"Results → {output_dir / 'walk_forward_results.csv'}")
    print("=" * 70 + "\n")

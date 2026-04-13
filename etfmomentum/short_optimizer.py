"""Grid search optimizer for the short hedge sleeve parameters.

Grid
----
  SHORT_TOP_N            : [1, 2, 3]
  SHORT_ALLOCATION       : [0.15, 0.25, 0.33]
  SHORT_STOP_LOSS        : [1.03, 1.05, 1.07, 1.10]
  qualification          : ['both_filters', 'momentum_quality_only']

Total combinations: 3 × 3 × 4 × 2 = 72

Price data is fetched once and reused across all iterations.
Baseline (long-only, ENABLE_SHORT_SELLING=False) is run first for comparison.
Results ranked by Sharpe ratio; top 10 + sensitivity analysis printed.
"""

import itertools
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd

from . import config as _config
from .backtest import run_backtest
from .data_fetcher import fetch_all_data
from .etf_loader import load_universe_by_name
from .report import calculate_metrics

logger = logging.getLogger(__name__)


def _run_combo(
    price_data: pd.DataFrame,
    universe: str,
    start_date: str,
    end_date: str,
    top_n: int,
    short_top_n: int,
    short_allocation: float,
    short_stop: float,
    qualification: str,
) -> Dict:
    """Run one backtest combo with temp config overrides. Always restores config."""
    orig_enabled = _config.ENABLE_SHORT_SELLING
    orig_universes = _config.SHORT_ENABLED_UNIVERSES
    orig_params = _config.SHORT_UNIVERSE_PARAMS.get(universe, {}).copy()

    _config.ENABLE_SHORT_SELLING = True
    if universe not in _config.SHORT_ENABLED_UNIVERSES:
        _config.SHORT_ENABLED_UNIVERSES = list(_config.SHORT_ENABLED_UNIVERSES) + [universe]
    _config.SHORT_UNIVERSE_PARAMS[universe] = {
        'top_n':         short_top_n,
        'allocation':    short_allocation,
        'stop_loss':     short_stop,
        'qualification': qualification,
    }

    try:
        strategy_df, benchmark_df, rebalance_log, short_stats = run_backtest(
            universe=universe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=_config.INITIAL_CAPITAL,
            top_n=top_n,
            rebalance_frequency=_config.REBALANCE_FREQUENCY,
            price_data=price_data,
        )
    finally:
        _config.ENABLE_SHORT_SELLING = orig_enabled
        _config.SHORT_ENABLED_UNIVERSES = orig_universes
        if orig_params:
            _config.SHORT_UNIVERSE_PARAMS[universe] = orig_params
        elif universe in _config.SHORT_UNIVERSE_PARAMS:
            del _config.SHORT_UNIVERSE_PARAMS[universe]

    metrics = calculate_metrics(
        portfolio_values=strategy_df['portfolio_value'],
        initial_capital=_config.INITIAL_CAPITAL,
        risk_free_rate=_config.RISK_FREE_RATE,
    )
    bench_metrics = calculate_metrics(
        portfolio_values=benchmark_df['portfolio_value'],
        initial_capital=_config.INITIAL_CAPITAL,
        risk_free_rate=_config.RISK_FREE_RATE,
    )

    total_rebalances = short_stats['total_rebalances']
    weeks_active = short_stats['weeks_with_shorts']

    return {
        'short_top_n': short_top_n,
        'short_allocation_pct': round(short_allocation * 100),
        'short_stop_pct': round((short_stop - 1) * 100, 0),
        'qualification': qualification,
        'total_return': metrics['total_return'],
        'annualized_return': metrics['annualized_return'],
        'sharpe_ratio': metrics['sharpe_ratio'],
        'max_drawdown': metrics['max_drawdown'],
        'outperformance_vs_spy': metrics['total_return'] - bench_metrics['total_return'],
        'short_activation_pct': round(weeks_active / total_rebalances * 100) if total_rebalances else 0,
        'short_stop_triggers': short_stats['stop_triggers'],
        'avg_gross_exposure': short_stats['avg_gross_exposure'],
    }


def run_short_optimization(
    universe: str = 'emerging',
    start_date: str = '2016-01-01',
    end_date: str = '2026-04-08',
) -> pd.DataFrame:
    """
    Run 72-combo grid search over short sleeve parameters.

    Args:
        universe: ETF universe to test against
        start_date: Backtest start date
        end_date: Backtest end date

    Returns:
        DataFrame of all results ranked by Sharpe ratio
    """
    logger.info("=" * 70)
    logger.info("SHORT SLEEVE PARAMETER OPTIMIZATION")
    logger.info("=" * 70)
    logger.info(f"Universe  : {universe.upper()}")
    logger.info(f"Period    : {start_date} to {end_date}")
    logger.info(f"Grid      : TOP_N×3  ALLOC×3  STOP×4  QUAL×2 = 72 combos")
    logger.info("=" * 70)

    params = _config.UNIVERSE_PARAMS.get(universe, _config.UNIVERSE_PARAMS['sp500'])
    top_n = params['top_n']

    # --- Fetch price data once ---
    etf_universe = load_universe_by_name(universe, _config.ETFLIST_DIR)
    all_tickers = list(etf_universe.keys()) + [_config.BENCHMARK_TICKER, _config.CASH_TICKER]
    logger.info("Fetching price data (once for all combos)...")
    price_data = fetch_all_data(
        ticker_list=all_tickers,
        start_date=_config.DATA_START_DATE,
        end_date=end_date,
        api_key=_config.FMP_API_KEY,
        api_delay=_config.FMP_API_DELAY,
    )
    logger.info(f"Price data ready: {len(price_data)} days, {len(price_data.columns)} tickers")

    # --- Baseline: long-only ---
    logger.info("\nRunning baseline (long-only, no shorts)...")
    orig_enabled = _config.ENABLE_SHORT_SELLING
    _config.ENABLE_SHORT_SELLING = False
    try:
        base_strategy, base_bench, _log, _ss = run_backtest(
            universe=universe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=_config.INITIAL_CAPITAL,
            top_n=top_n,
            rebalance_frequency=_config.REBALANCE_FREQUENCY,
            price_data=price_data,
        )
    finally:
        _config.ENABLE_SHORT_SELLING = orig_enabled  # restore; grid search combos set their own overrides

    baseline = calculate_metrics(
        portfolio_values=base_strategy['portfolio_value'],
        initial_capital=_config.INITIAL_CAPITAL,
        risk_free_rate=_config.RISK_FREE_RATE,
    )
    logger.info(
        f"Baseline — Return: {baseline['total_return']*100:.1f}%  "
        f"Sharpe: {baseline['sharpe_ratio']:.3f}  "
        f"MaxDD: {baseline['max_drawdown']*100:.2f}%"
    )

    # --- Grid search ---
    short_top_n_values = [1, 2, 3]
    short_alloc_values = [0.15, 0.25, 0.33]
    short_stop_values = [1.03, 1.05, 1.07, 1.10]
    qualification_values = ['both_filters', 'momentum_quality_only']

    total = (
        len(short_top_n_values) * len(short_alloc_values)
        * len(short_stop_values) * len(qualification_values)
    )

    results: List[Dict] = []
    n = 0
    start_time = datetime.now()

    for short_top_n, short_alloc, short_stop, qual in itertools.product(
        short_top_n_values, short_alloc_values, short_stop_values, qualification_values
    ):
        n += 1
        logger.info(
            f"[{n:2d}/{total}] TOP_N={short_top_n}  ALLOC={short_alloc*100:.0f}%  "
            f"STOP={short_stop-1:.0%}  QUAL={qual}"
        )
        try:
            result = _run_combo(
                price_data=price_data,
                universe=universe,
                start_date=start_date,
                end_date=end_date,
                top_n=top_n,
                short_top_n=short_top_n,
                short_allocation=short_alloc,
                short_stop=short_stop,
                qualification=qual,
            )
            results.append(result)
            logger.info(
                f"         → Return: {result['total_return']*100:.1f}%  "
                f"Sharpe: {result['sharpe_ratio']:.3f}  "
                f"MaxDD: {result['max_drawdown']*100:.2f}%  "
                f"Active: {result['short_activation_pct']}%  "
                f"Stops: {result['short_stop_triggers']}"
            )
        except Exception as e:
            logger.error(f"         → ERROR: {e}")

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\nCompleted {len(results)}/{total} combos in {elapsed/60:.1f} min")

    df = pd.DataFrame(results)
    df = df.sort_values('sharpe_ratio', ascending=False).reset_index(drop=True)
    df.insert(0, 'rank', range(1, len(df) + 1))

    # --- Output ---
    output_dir = _config.OUTPUT_DIR / universe
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / 'short_optimization_results.csv'
    df.to_csv(results_path, index=False)

    _print_report(df, baseline, universe, start_date, end_date, results_path)

    return df


def _print_report(
    df: pd.DataFrame,
    baseline: Dict,
    universe: str,
    start_date: str,
    end_date: str,
    results_path: Path,
):
    """Print optimization summary to console."""
    print("\n" + "=" * 70)
    print("SHORT SLEEVE OPTIMIZATION RESULTS")
    print("=" * 70)
    print(f"Universe : {universe.upper()}  |  Period: {start_date} → {end_date}")
    print(f"Baseline : Return {baseline['total_return']*100:.1f}%  "
          f"Sharpe {baseline['sharpe_ratio']:.3f}  "
          f"MaxDD {baseline['max_drawdown']*100:.2f}%")
    print("=" * 70)

    # Top 10
    print("\nTOP 10 COMBINATIONS (ranked by Sharpe):\n")
    cols = ['rank', 'short_top_n', 'short_allocation_pct', 'short_stop_pct',
            'qualification', 'sharpe_ratio', 'annualized_return', 'max_drawdown',
            'short_activation_pct', 'short_stop_triggers']
    top10 = df.head(10)[cols].copy()
    top10['annualized_return'] = (top10['annualized_return'] * 100).round(2)
    top10['max_drawdown'] = (top10['max_drawdown'] * 100).round(2)
    top10['sharpe_ratio'] = top10['sharpe_ratio'].round(3)
    top10.columns = ['Rank', 'TopN', 'Alloc%', 'Stop%', 'Qual',
                     'Sharpe', 'Ann%', 'MaxDD%', 'Active%', 'Stops']
    print(top10.to_string(index=False))

    # Best combo delta vs baseline
    best = df.iloc[0]
    print(f"\nBest vs Baseline:")
    print(f"  Sharpe  : {baseline['sharpe_ratio']:.3f} → {best['sharpe_ratio']:.3f}  "
          f"({best['sharpe_ratio'] - baseline['sharpe_ratio']:+.3f})")
    print(f"  Ann Ret : {baseline['annualized_return']*100:.2f}% → "
          f"{best['annualized_return']*100:.2f}%  "
          f"({(best['annualized_return'] - baseline['annualized_return'])*100:+.2f}pp)")
    print(f"  MaxDD   : {baseline['max_drawdown']*100:.2f}% → "
          f"{best['max_drawdown']*100:.2f}%  "
          f"({(best['max_drawdown'] - baseline['max_drawdown'])*100:+.2f}pp)")

    # Sensitivity analysis
    print("\nSENSITIVITY — Avg Sharpe by parameter value:\n")

    for param, label in [
        ('short_top_n', 'SHORT_TOP_N'),
        ('short_allocation_pct', 'ALLOCATION %'),
        ('short_stop_pct', 'STOP %'),
        ('qualification', 'QUALIFICATION'),
    ]:
        print(f"  {label}:")
        for val in sorted(df[param].unique()):
            avg = df[df[param] == val]['sharpe_ratio'].mean()
            best_val = df[df[param] == val]['sharpe_ratio'].max()
            print(f"    {val!s:>25} → avg Sharpe {avg:.3f}  best {best_val:.3f}")
        print()

    print(f"Full results saved to: {results_path}")
    print("=" * 70 + "\n")

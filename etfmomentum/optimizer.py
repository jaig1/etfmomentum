"""Automated parameter optimization for ETF momentum strategy."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime
import itertools

from .config import (
    BACKTEST_START_DATE,
    BACKTEST_END_DATE,
    INITIAL_CAPITAL,
    BENCHMARK_TICKER,
    RISK_FREE_RATE,
    OUTPUT_DIR,
    ETFLIST_DIR,
    DATA_DIR,
    PRICE_DATA_CACHE,
)
from .etf_loader import load_universe_by_name
from .data_fetcher import load_data_from_cache
from .rs_engine import generate_signals
from .backtest import run_backtest
from .report import calculate_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_single_backtest(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    spy_ticker: str,
    sma_window: int,
    roc_lookback: int,
    top_n: int,
) -> Dict[str, float]:
    """
    Run a single backtest with specific parameters.

    Args:
        price_data: Price data DataFrame
        etf_tickers: List of ETF tickers
        spy_ticker: Benchmark ticker
        sma_window: SMA window in days
        roc_lookback: RS ROC lookback in days
        top_n: Number of top holdings

    Returns:
        Dictionary of performance metrics
    """
    # Generate signals with specific parameters
    signals = generate_signals(
        price_data=price_data,
        spy_ticker=spy_ticker,
        etf_tickers=etf_tickers,
        sma_window=sma_window,
        roc_lookback=roc_lookback,
    )

    # Run backtest
    strategy_df, benchmark_df, rebalance_log = run_backtest(
        signals=signals,
        price_data=price_data,
        spy_ticker=spy_ticker,
        start_date=BACKTEST_START_DATE,
        end_date=BACKTEST_END_DATE,
        initial_capital=INITIAL_CAPITAL,
        top_n=top_n,
    )

    # Calculate metrics
    strategy_metrics = calculate_metrics(
        portfolio_values=strategy_df['portfolio_value'],
        initial_capital=INITIAL_CAPITAL,
        risk_free_rate=RISK_FREE_RATE,
    )

    benchmark_metrics = calculate_metrics(
        portfolio_values=benchmark_df['portfolio_value'],
        initial_capital=INITIAL_CAPITAL,
        risk_free_rate=RISK_FREE_RATE,
    )

    # Calculate number of trades
    num_rebalances = len(rebalance_log)

    # Calculate outperformance vs SPY
    outperformance = strategy_metrics['total_return'] - benchmark_metrics['total_return']

    return {
        'total_return': strategy_metrics['total_return'],
        'annualized_return': strategy_metrics['annualized_return'],
        'sharpe_ratio': strategy_metrics['sharpe_ratio'],
        'max_drawdown': strategy_metrics['max_drawdown'],
        'final_value': strategy_metrics['final_value'],
        'num_rebalances': num_rebalances,
        'outperformance_vs_spy': outperformance,
        'spy_total_return': benchmark_metrics['total_return'],
        'spy_sharpe_ratio': benchmark_metrics['sharpe_ratio'],
    }


def optimize_parameters(
    universe: str = 'sp500',
    output_subdir: str = 'sp500',
) -> pd.DataFrame:
    """
    Run grid search optimization across parameter space.

    Args:
        universe: Universe name (sp500, developed, emerging)
        output_subdir: Output subdirectory name

    Returns:
        DataFrame with optimization results
    """
    logger.info("="*80)
    logger.info("STARTING AUTOMATED PARAMETER OPTIMIZATION")
    logger.info("="*80)
    logger.info(f"Universe: {universe}")
    logger.info(f"Backtest period: {BACKTEST_START_DATE} to {BACKTEST_END_DATE}")

    # Define parameter grid
    # Convert months to days (assuming 21 trading days per month)
    sma_windows_months = [6, 8, 10, 12]  # months
    sma_windows = [m * 21 for m in sma_windows_months]  # Convert to days

    roc_lookbacks_months = [1, 3, 6]  # months
    roc_lookbacks = [m * 21 for m in roc_lookbacks_months]  # Convert to days

    top_n_values = [3, 5, 7, 10]

    logger.info(f"\nParameter Grid:")
    logger.info(f"  SMA Windows (months): {sma_windows_months}")
    logger.info(f"  SMA Windows (days): {sma_windows}")
    logger.info(f"  ROC Lookbacks (months): {roc_lookbacks_months}")
    logger.info(f"  ROC Lookbacks (days): {roc_lookbacks}")
    logger.info(f"  Top N Holdings: {top_n_values}")

    total_combinations = len(sma_windows) * len(roc_lookbacks) * len(top_n_values)
    logger.info(f"\nTotal combinations to test: {total_combinations}")

    # Load ETF universe
    logger.info(f"\nLoading ETF universe: {universe}")
    etf_universe = load_universe_by_name(universe, ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())
    logger.info(f"Loaded {len(etf_tickers)} ETFs")

    # Load price data
    logger.info(f"\nLoading price data from cache: {PRICE_DATA_CACHE}")
    if not PRICE_DATA_CACHE.exists():
        raise FileNotFoundError(
            f"Price data cache not found at {PRICE_DATA_CACHE}. "
            f"Please run a backtest first to generate cached data."
        )

    price_data = load_data_from_cache(str(PRICE_DATA_CACHE))
    logger.info(f"Loaded price data: {len(price_data)} days, {len(price_data.columns)} tickers")

    # Create output directory
    output_dir = OUTPUT_DIR / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run optimization
    results = []
    combination_num = 0

    logger.info("\n" + "="*80)
    logger.info("RUNNING BACKTESTS")
    logger.info("="*80 + "\n")

    start_time = datetime.now()

    for sma_window, roc_lookback, top_n in itertools.product(sma_windows, roc_lookbacks, top_n_values):
        combination_num += 1

        # Convert days back to months for display
        sma_months = sma_window // 21
        roc_months = roc_lookback // 21

        logger.info(f"[{combination_num}/{total_combinations}] Testing: "
                   f"SMA={sma_months}mo ({sma_window}d), "
                   f"ROC={roc_months}mo ({roc_lookback}d), "
                   f"Top N={top_n}")

        try:
            metrics = run_single_backtest(
                price_data=price_data,
                etf_tickers=etf_tickers,
                spy_ticker=BENCHMARK_TICKER,
                sma_window=sma_window,
                roc_lookback=roc_lookback,
                top_n=top_n,
            )

            # Add parameters to results
            result = {
                'sma_window_months': sma_months,
                'sma_window_days': sma_window,
                'roc_lookback_months': roc_months,
                'roc_lookback_days': roc_lookback,
                'top_n_holdings': top_n,
                **metrics
            }

            results.append(result)

            logger.info(f"  → Total Return: {metrics['total_return']*100:.2f}%, "
                       f"Sharpe: {metrics['sharpe_ratio']:.3f}, "
                       f"Max DD: {metrics['max_drawdown']*100:.2f}%, "
                       f"vs SPY: {metrics['outperformance_vs_spy']*100:+.2f}%")

        except Exception as e:
            logger.error(f"  → ERROR: {str(e)}")
            continue

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    logger.info("\n" + "="*80)
    logger.info("OPTIMIZATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    logger.info(f"Successful backtests: {len(results)}/{total_combinations}")

    # Create results DataFrame
    df_results = pd.DataFrame(results)

    # Sort by Sharpe ratio (primary optimization metric)
    df_results = df_results.sort_values('sharpe_ratio', ascending=False).reset_index(drop=True)
    df_results.insert(0, 'rank', range(1, len(df_results) + 1))

    # Save full results
    results_path = output_dir / 'optimization_results.csv'
    df_results.to_csv(results_path, index=False)
    logger.info(f"\nSaved full results to: {results_path}")

    # Generate summary report
    generate_summary_report(df_results, output_dir, universe)

    return df_results


def generate_summary_report(df_results: pd.DataFrame, output_dir: Path, universe: str):
    """Generate and save optimization summary report."""

    summary_path = output_dir / 'optimization_summary.txt'

    with open(summary_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("ETF MOMENTUM STRATEGY - OPTIMIZATION SUMMARY\n")
        f.write("="*80 + "\n\n")

        f.write(f"Universe: {universe.upper()}\n")
        f.write(f"Backtest Period: {BACKTEST_START_DATE} to {BACKTEST_END_DATE}\n")
        f.write(f"Optimization Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Combinations Tested: {len(df_results)}\n\n")

        f.write("="*80 + "\n")
        f.write("CURRENT IMPLEMENTATION (BASELINE)\n")
        f.write("="*80 + "\n")
        f.write("Parameters:\n")
        f.write("  - SMA Window: 10 months (~200 days)\n")
        f.write("  - ROC Lookback: 1 month (~21 days)\n")
        f.write("  - Top N Holdings: 5\n\n")

        # Find current implementation in results
        current = df_results[
            (df_results['sma_window_months'] == 10) &
            (df_results['roc_lookback_months'] == 1) &
            (df_results['top_n_holdings'] == 5)
        ]

        if not current.empty:
            current_row = current.iloc[0]
            f.write(f"Performance:\n")
            f.write(f"  - Total Return: {current_row['total_return']*100:.2f}%\n")
            f.write(f"  - Annualized Return: {current_row['annualized_return']*100:.2f}%\n")
            f.write(f"  - Sharpe Ratio: {current_row['sharpe_ratio']:.3f}\n")
            f.write(f"  - Max Drawdown: {current_row['max_drawdown']*100:.2f}%\n")
            f.write(f"  - vs SPY: {current_row['outperformance_vs_spy']*100:+.2f}%\n")
            f.write(f"  - Rank: {current_row['rank']}/{len(df_results)}\n\n")

        f.write("="*80 + "\n")
        f.write("OPTIMAL PARAMETERS (Best Sharpe Ratio)\n")
        f.write("="*80 + "\n")

        best = df_results.iloc[0]
        f.write("Parameters:\n")
        f.write(f"  - SMA Window: {best['sma_window_months']} months ({best['sma_window_days']} days)\n")
        f.write(f"  - ROC Lookback: {best['roc_lookback_months']} months ({best['roc_lookback_days']} days)\n")
        f.write(f"  - Top N Holdings: {best['top_n_holdings']}\n\n")

        f.write(f"Performance:\n")
        f.write(f"  - Total Return: {best['total_return']*100:.2f}%\n")
        f.write(f"  - Annualized Return: {best['annualized_return']*100:.2f}%\n")
        f.write(f"  - Sharpe Ratio: {best['sharpe_ratio']:.3f}\n")
        f.write(f"  - Max Drawdown: {best['max_drawdown']*100:.2f}%\n")
        f.write(f"  - vs SPY: {best['outperformance_vs_spy']*100:+.2f}%\n")
        f.write(f"  - Number of Rebalances: {best['num_rebalances']}\n\n")

        if not current.empty:
            f.write("Improvement vs Current:\n")
            ret_improvement = (best['total_return'] - current_row['total_return']) * 100
            sharpe_improvement = ((best['sharpe_ratio'] - current_row['sharpe_ratio']) / current_row['sharpe_ratio']) * 100
            dd_improvement = (best['max_drawdown'] - current_row['max_drawdown']) * 100

            f.write(f"  - Total Return: {ret_improvement:+.2f} percentage points\n")
            f.write(f"  - Sharpe Ratio: {sharpe_improvement:+.1f}%\n")
            f.write(f"  - Max Drawdown: {dd_improvement:+.2f} percentage points ")
            f.write("(better)\n" if dd_improvement > 0 else "(worse)\n")
            f.write("\n")

        f.write("="*80 + "\n")
        f.write("TOP 5 PARAMETER COMBINATIONS\n")
        f.write("="*80 + "\n\n")

        top5 = df_results.head(5)
        for idx, row in top5.iterrows():
            f.write(f"Rank {row['rank']}:\n")
            f.write(f"  Parameters: SMA={row['sma_window_months']}mo, "
                   f"ROC={row['roc_lookback_months']}mo, Top N={row['top_n_holdings']}\n")
            f.write(f"  Return: {row['total_return']*100:.2f}%, "
                   f"Sharpe: {row['sharpe_ratio']:.3f}, "
                   f"Max DD: {row['max_drawdown']*100:.2f}%, "
                   f"vs SPY: {row['outperformance_vs_spy']*100:+.2f}%\n\n")

        f.write("="*80 + "\n")
        f.write("PARAMETER SENSITIVITY ANALYSIS\n")
        f.write("="*80 + "\n\n")

        # Analyze by each parameter
        f.write("Average Sharpe Ratio by SMA Window:\n")
        for sma in sorted(df_results['sma_window_months'].unique()):
            avg_sharpe = df_results[df_results['sma_window_months'] == sma]['sharpe_ratio'].mean()
            f.write(f"  {sma} months: {avg_sharpe:.3f}\n")

        f.write("\nAverage Sharpe Ratio by ROC Lookback:\n")
        for roc in sorted(df_results['roc_lookback_months'].unique()):
            avg_sharpe = df_results[df_results['roc_lookback_months'] == roc]['sharpe_ratio'].mean()
            f.write(f"  {roc} months: {avg_sharpe:.3f}\n")

        f.write("\nAverage Sharpe Ratio by Top N Holdings:\n")
        for n in sorted(df_results['top_n_holdings'].unique()):
            avg_sharpe = df_results[df_results['top_n_holdings'] == n]['sharpe_ratio'].mean()
            f.write(f"  {n} holdings: {avg_sharpe:.3f}\n")

        f.write("\n" + "="*80 + "\n")
        f.write("RECOMMENDATIONS\n")
        f.write("="*80 + "\n\n")

        f.write(f"1. Update config.py with optimal parameters:\n")
        f.write(f"   SMA_LOOKBACK_DAYS = {best['sma_window_days']}  # {best['sma_window_months']} months\n")
        f.write(f"   RS_ROC_LOOKBACK_DAYS = {best['roc_lookback_days']}  # {best['roc_lookback_months']} months\n")
        f.write(f"   TOP_N_HOLDINGS = {best['top_n_holdings']}\n\n")

        f.write(f"2. Expected performance improvement:\n")
        if not current.empty:
            f.write(f"   - Sharpe ratio: {current_row['sharpe_ratio']:.3f} → {best['sharpe_ratio']:.3f}\n")
            f.write(f"   - Total return: {current_row['total_return']*100:.2f}% → {best['total_return']*100:.2f}%\n")

        f.write(f"\n3. Review top 5 combinations for robustness\n")
        f.write(f"4. Consider walk-forward optimization for validation\n")
        f.write(f"5. Test optimized parameters on other universes\n")

    logger.info(f"Saved summary report to: {summary_path}")

    # Print summary to console
    print("\n" + "="*80)
    print("OPTIMIZATION SUMMARY")
    print("="*80)
    print(f"\nOptimal Parameters (Best Sharpe Ratio):")
    print(f"  SMA Window: {best['sma_window_months']} months")
    print(f"  ROC Lookback: {best['roc_lookback_months']} months")
    print(f"  Top N Holdings: {best['top_n_holdings']}")
    print(f"\nPerformance:")
    print(f"  Total Return: {best['total_return']*100:.2f}%")
    print(f"  Sharpe Ratio: {best['sharpe_ratio']:.3f}")
    print(f"  Max Drawdown: {best['max_drawdown']*100:.2f}%")
    print(f"  vs SPY: {best['outperformance_vs_spy']*100:+.2f}%")

    if not current.empty:
        print(f"\nCurrent Implementation:")
        print(f"  Total Return: {current_row['total_return']*100:.2f}%")
        print(f"  Sharpe Ratio: {current_row['sharpe_ratio']:.3f}")
        print(f"  Rank: {current_row['rank']}/{len(df_results)}")

    print("\n" + "="*80)
    print(f"Full results saved to: {output_dir / 'optimization_results.csv'}")
    print(f"Summary report saved to: {summary_path}")
    print("="*80 + "\n")


if __name__ == '__main__':
    # Run optimization for S&P 500 sectors
    results = optimize_parameters(universe='sp500', output_subdir='sp500')
    print(f"\nOptimization complete! {len(results)} combinations tested.")

"""
Defensive Strategy Tester
Tests different defensive allocation strategies during high volatility regimes.
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple
from pathlib import Path

from . import config
from .data_fetcher import fetch_all_data, save_data_to_cache, load_data_from_cache
from .signal_generator import generate_signals
from .backtest import run_backtest
from .report import calculate_metrics
from .volatility_regime import VolatilityRegimeDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_single_strategy_test(
    strategy_name: str,
    defensive_mode: str,
    price_data: pd.DataFrame,
    signals: pd.DataFrame,
    etf_tickers: List[str],
    spy_ticker: str,
    initial_capital: float = 500000.0,
) -> Dict:
    """
    Run backtest for a single defensive strategy.

    Args:
        strategy_name: Name of the strategy
        defensive_mode: One of: 'baseline', 'defensive_sectors', 'tbills', 'hybrid', 'tiered'
        price_data: Historical price data
        signals: ETF signals
        etf_tickers: List of ETF tickers
        spy_ticker: SPY ticker
        initial_capital: Starting capital

    Returns:
        Dictionary with performance metrics
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Running Strategy: {strategy_name}")
    logger.info(f"Defensive Mode: {defensive_mode}")
    logger.info(f"{'='*70}")

    # Create regime detector based on strategy
    if defensive_mode == 'baseline':
        # Use current behavior - no special defensive allocation
        regime_detector = VolatilityRegimeDetector(
            lookback_days=config.VOLATILITY_LOOKBACK_DAYS,
            low_vol_threshold=config.LOW_VOL_THRESHOLD,
            high_vol_threshold=config.HIGH_VOL_THRESHOLD,
            low_vol_top_n=config.LOW_VOL_TOP_N,
            medium_vol_top_n=config.MEDIUM_VOL_TOP_N,
            high_vol_top_n=config.HIGH_VOL_TOP_N,
            high_vol_spy_allocation=config.HIGH_VOL_SPY_MIN_ALLOCATION,
            use_vix=config.USE_VIX_FOR_REGIME,
            defensive_mode=None  # No defensive override
        )
    else:
        # Use defensive allocation strategy
        regime_detector = VolatilityRegimeDetector(
            lookback_days=config.VOLATILITY_LOOKBACK_DAYS,
            low_vol_threshold=config.LOW_VOL_THRESHOLD,
            high_vol_threshold=config.HIGH_VOL_THRESHOLD,
            low_vol_top_n=config.LOW_VOL_TOP_N,
            medium_vol_top_n=config.MEDIUM_VOL_TOP_N,
            high_vol_top_n=config.HIGH_VOL_TOP_N,
            high_vol_spy_allocation=config.HIGH_VOL_SPY_MIN_ALLOCATION,
            use_vix=config.USE_VIX_FOR_REGIME,
            defensive_mode=defensive_mode,
            defensive_sectors=config.HIGH_VOL_DEFENSIVE_SECTORS,
            tbill_ticker=config.HIGH_VOL_TBILL_ETF,
            tbill_allocation=config.HIGH_VOL_TBILL_ALLOCATION,
            extreme_vol_threshold=config.EXTREME_VOL_THRESHOLD,
        )

    # Run backtest
    strategy_df, benchmark_df, rebalance_log = run_backtest(
        signals=signals,
        price_data=price_data,
        spy_ticker=spy_ticker,
        start_date=config.BACKTEST_START_DATE,
        end_date=config.BACKTEST_END_DATE,
        initial_capital=initial_capital,
        top_n=config.TOP_N_HOLDINGS,
        regime_detector=regime_detector,
    )

    # Extract portfolio values Series
    strategy_values = strategy_df['portfolio_value']
    benchmark_values = benchmark_df['portfolio_value']

    # Calculate metrics for strategy
    strategy_metrics = calculate_metrics(
        strategy_values,
        initial_capital,
        config.RISK_FREE_RATE,
    )

    # Calculate metrics for benchmark
    benchmark_metrics = calculate_metrics(
        benchmark_values,
        initial_capital,
        config.RISK_FREE_RATE,
    )

    # Add strategy info
    result = {
        'strategy_name': strategy_name,
        'defensive_mode': defensive_mode,
        'total_return': strategy_metrics['total_return'] * 100,  # Convert to percentage
        'annualized_return': strategy_metrics['annualized_return'] * 100,
        'sharpe_ratio': strategy_metrics['sharpe_ratio'],
        'max_drawdown': strategy_metrics['max_drawdown'] * 100,
        'final_value': strategy_metrics['final_value'],
        'benchmark_return': benchmark_metrics['total_return'] * 100,
        'outperformance': (strategy_metrics['total_return'] - benchmark_metrics['total_return']) * 100,
    }

    logger.info(f"Total Return: {result['total_return']:.2f}%")
    logger.info(f"Sharpe Ratio: {result['sharpe_ratio']:.3f}")
    logger.info(f"Final Value: ${result['final_value']:,.2f}")

    return result


def run_all_defensive_tests(
    universe: str = 'sp500',
    initial_capital: float = 500000.0,
    refresh_data: bool = False,
) -> pd.DataFrame:
    """
    Run all 5 defensive strategy tests and compare results.

    Args:
        universe: ETF universe to test (sp500, developed, emerging)
        initial_capital: Starting capital
        refresh_data: Whether to refresh price data from API

    Returns:
        DataFrame with comparative results
    """
    logger.info("="*70)
    logger.info("DEFENSIVE STRATEGY COMPARISON TEST")
    logger.info("="*70)
    logger.info(f"Universe: {universe}")
    logger.info(f"Initial Capital: ${initial_capital:,.2f}")
    logger.info(f"Test Period: {config.BACKTEST_START_DATE} to {config.BACKTEST_END_DATE}")
    logger.info("="*70)

    # Load ETF universe
    etflist_file = config.ETFLIST_DIR / f"{universe}_sector_etfs.csv"
    etf_df = pd.read_csv(etflist_file)
    etf_tickers = etf_df['Ticker'].tolist()
    spy_ticker = config.BENCHMARK_TICKER

    # Add T-Bill ETF to ticker list
    tbill_ticker = config.HIGH_VOL_TBILL_ETF
    all_tickers = etf_tickers + [spy_ticker, tbill_ticker]

    logger.info(f"ETFs: {len(etf_tickers)}")
    logger.info(f"Benchmark: {spy_ticker}")
    logger.info(f"T-Bill ETF: {tbill_ticker}")

    # Fetch or load price data
    if refresh_data:
        logger.info("\nFetching fresh price data from API...")
        price_data = fetch_all_data(
            all_tickers,
            config.DATA_START_DATE,
            config.BACKTEST_END_DATE,
            config.FMP_API_KEY,
            config.FMP_API_DELAY,
        )
        save_data_to_cache(price_data, config.PRICE_DATA_CACHE)
    else:
        logger.info("\nLoading data from cache...")
        price_data = load_data_from_cache(config.PRICE_DATA_CACHE)

        # Check if T-Bill data is available
        if tbill_ticker not in price_data.columns:
            logger.info(f"{tbill_ticker} not in cache, fetching...")
            tbill_data = fetch_all_data(
                [tbill_ticker],
                config.DATA_START_DATE,
                config.BACKTEST_END_DATE,
                config.FMP_API_KEY,
                config.FMP_API_DELAY,
            )
            price_data = pd.concat([price_data, tbill_data], axis=1)
            save_data_to_cache(price_data, config.PRICE_DATA_CACHE)

    logger.info(f"Price data loaded: {len(price_data)} days, {len(price_data.columns)} tickers")

    # Generate signals
    logger.info("\nGenerating signals...")
    signals = generate_signals(
        price_data,
        spy_ticker,
        etf_tickers,
        config.SMA_LOOKBACK_DAYS,
        config.RS_ROC_LOOKBACK_DAYS,
    )

    # Define test strategies
    strategies = [
        {
            'name': 'Test 1: Baseline (Current)',
            'mode': 'baseline',
            'description': 'HIGH vol → 100% SPY if no ETFs qualify'
        },
        {
            'name': 'Test 2: Defensive Sectors',
            'mode': 'defensive_sectors',
            'description': 'HIGH vol → Top 3 defensive sectors (XLP, XLU, XLV) by RS rank'
        },
        {
            'name': 'Test 3: T-Bills Only',
            'mode': 'tbills',
            'description': f'HIGH vol → 100% {tbill_ticker} (capital preservation)'
        },
        {
            'name': 'Test 4: Hybrid Defensive',
            'mode': 'hybrid',
            'description': f'HIGH vol → 50% {tbill_ticker} + 50% defensive sectors'
        },
        {
            'name': 'Test 5: Tiered Approach',
            'mode': 'tiered',
            'description': f'HIGH vol (25-35%) → Defensive sectors, EXTREME vol (>35%) → {tbill_ticker}'
        },
    ]

    # Run all tests
    results = []
    for strategy in strategies:
        result = run_single_strategy_test(
            strategy_name=strategy['name'],
            defensive_mode=strategy['mode'],
            price_data=price_data,
            signals=signals,
            etf_tickers=etf_tickers,
            spy_ticker=spy_ticker,
            initial_capital=initial_capital,
        )
        result['description'] = strategy['description']
        results.append(result)

    # Create comparison DataFrame
    df_results = pd.DataFrame(results)

    # Reorder columns
    df_results = df_results[[
        'strategy_name',
        'description',
        'total_return',
        'annualized_return',
        'sharpe_ratio',
        'max_drawdown',
        'final_value',
        'benchmark_return',
        'outperformance',
    ]]

    # Sort by Sharpe ratio (risk-adjusted returns)
    df_results = df_results.sort_values('sharpe_ratio', ascending=False)

    return df_results


def print_comparison_summary(df_results: pd.DataFrame) -> None:
    """Print formatted comparison summary."""
    print("\n" + "="*100)
    print("DEFENSIVE STRATEGY COMPARISON SUMMARY")
    print("="*100)
    print("\nRanked by Sharpe Ratio (Risk-Adjusted Returns):\n")

    for idx, row in df_results.iterrows():
        print(f"{row['strategy_name']}")
        print(f"  Description: {row['description']}")
        print(f"  Total Return: {row['total_return']:.2f}%")
        print(f"  Annualized: {row['annualized_return']:.2f}%")
        print(f"  Sharpe Ratio: {row['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {row['max_drawdown']:.2f}%")
        print(f"  Final Value: ${row['final_value']:,.2f}")
        print(f"  Outperformance vs SPY: {row['outperformance']:.2f}%")
        print()

    print("="*100)

    # Find best strategy
    best = df_results.iloc[0]
    print(f"\n🏆 BEST STRATEGY (by Sharpe Ratio): {best['strategy_name']}")
    print(f"   Sharpe: {best['sharpe_ratio']:.3f} | Return: {best['total_return']:.2f}% | Final: ${best['final_value']:,.2f}")
    print()


if __name__ == "__main__":
    # Run all tests
    results_df = run_all_defensive_tests(
        universe='sp500',
        initial_capital=500000.0,
        refresh_data=False,
    )

    # Print summary
    print_comparison_summary(results_df)

    # Save results
    output_dir = config.OUTPUT_DIR / 'sp500'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'defensive_strategy_comparison.csv'
    results_df.to_csv(output_file, index=False)
    logger.info(f"\nResults saved to: {output_file}")

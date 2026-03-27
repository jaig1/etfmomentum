"""Main CLI orchestrator for ETF Relative Strength Framework."""

import argparse
import logging
import sys
from pathlib import Path

from . import config
from .data_fetcher import get_price_data
from .rs_engine import generate_signals
from .backtest import run_backtest, get_rebalance_dates
from .etf_loader import load_universe_by_name
from .volatility_regime import create_regime_detector
from .report import (
    calculate_metrics,
    generate_performance_summary,
    generate_monthly_returns_table,
    generate_yearly_summary_table,
    generate_portfolio_composition_log,
    generate_signal_status_report,
    print_performance_summary,
    print_monthly_returns,
    print_yearly_summary,
    print_portfolio_composition,
)
from .signal_generator import (
    calculate_signal_data_dates,
    generate_current_signals,
    select_current_portfolio,
    get_all_etf_current_status,
)
from .signal_report import (
    generate_signal_report,
    generate_detailed_status_report,
    print_signal_report,
    print_detailed_status,
    print_summary_stats,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='ETF Relative Strength Framework - Backtest & Signal Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='mode', help='Mode to run')

    # Backtest mode
    backtest_parser = subparsers.add_parser('backtest', help='Run historical backtest')
    backtest_parser.add_argument('--universe', type=str, default='emerging',
                                 choices=['emerging', 'developed', 'sp500'],
                                 help='ETF universe to use (default: emerging)')
    backtest_parser.add_argument('--refresh', action='store_true', help='Force re-download data')
    backtest_parser.add_argument('--start-date', type=str, default=config.BACKTEST_START_DATE,
                                 help=f'Backtest start date (default: {config.BACKTEST_START_DATE})')
    backtest_parser.add_argument('--end-date', type=str, default=config.BACKTEST_END_DATE,
                                 help=f'Backtest end date (default: {config.BACKTEST_END_DATE})')
    backtest_parser.add_argument('--top-n', type=int, default=config.TOP_N_HOLDINGS,
                                 help=f'Number of top ETFs (default: {config.TOP_N_HOLDINGS})')
    backtest_parser.add_argument('--initial-capital', type=float, default=config.INITIAL_CAPITAL,
                                 help=f'Initial capital (default: {config.INITIAL_CAPITAL})')

    # Signal mode
    signal_parser = subparsers.add_parser('signal', help='Generate current month signals')
    signal_parser.add_argument('--universe', type=str, default='emerging',
                               choices=['emerging', 'developed', 'sp500'],
                               help='ETF universe to use (default: emerging)')
    signal_parser.add_argument('--refresh', action='store_true', help='Force re-download data')
    signal_parser.add_argument('--detailed', action='store_true', help='Show detailed status for all ETFs')
    signal_parser.add_argument('--top-n', type=int, default=config.TOP_N_HOLDINGS,
                               help=f'Number of top ETFs (default: {config.TOP_N_HOLDINGS})')

    return parser.parse_args()


def run_backtest_mode(args):
    """Run backtest mode."""
    logger.info("="*70)
    logger.info("ETF RELATIVE STRENGTH BACKTEST")
    logger.info("="*70)

    # Load ETF universe
    try:
        etf_universe = load_universe_by_name(args.universe, config.ETFLIST_DIR)
    except Exception as e:
        logger.error(f"Error loading ETF universe: {e}")
        sys.exit(1)

    # Create universe-specific output directory
    universe_output_dir = config.OUTPUT_DIR / args.universe
    universe_output_dir.mkdir(exist_ok=True, parents=True)

    logger.info(f"Universe: {args.universe.upper()}")
    logger.info(f"Backtest Period: {args.start_date} to {args.end_date}")
    logger.info(f"Initial Capital: ${args.initial_capital:,.2f}")
    logger.info(f"Top N Holdings: {args.top_n}")
    logger.info(f"Number of ETFs: {len(etf_universe)}")
    logger.info(f"Benchmark: {config.BENCHMARK_TICKER}")
    logger.info(f"Volatility Regime Switching: {'ENABLED' if config.ENABLE_VOLATILITY_REGIME_SWITCHING else 'DISABLED'}")
    logger.info("="*70)

    try:
        # Run backtest — signals and price data are fetched internally
        logger.info("\n[1/3] Running backtest...")
        logger.info(f"Rebalance Frequency: {config.REBALANCE_FREQUENCY}")
        strategy_values, benchmark_values, rebalance_log = run_backtest(
            universe=args.universe,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.initial_capital,
            top_n=args.top_n,
            rebalance_frequency=config.REBALANCE_FREQUENCY,
        )

        # Calculate metrics
        logger.info("\n[2/3] Calculating performance metrics...")
        strategy_metrics = calculate_metrics(
            portfolio_values=strategy_values['portfolio_value'],
            initial_capital=args.initial_capital,
            risk_free_rate=config.RISK_FREE_RATE,
        )

        benchmark_metrics = calculate_metrics(
            portfolio_values=benchmark_values['portfolio_value'],
            initial_capital=args.initial_capital,
            risk_free_rate=config.RISK_FREE_RATE,
        )

        # Generate and display reports
        logger.info("\n[3/3] Generating reports...")

        perf_summary = generate_performance_summary(
            strategy_metrics=strategy_metrics,
            benchmark_metrics=benchmark_metrics,
            output_dir=universe_output_dir,
        )

        monthly_returns, monthly_win_rate = generate_monthly_returns_table(
            strategy_values=strategy_values['portfolio_value'],
            benchmark_values=benchmark_values['portfolio_value'],
            output_dir=universe_output_dir,
        )

        yearly_returns, yearly_win_rate = generate_yearly_summary_table(
            strategy_values=strategy_values['portfolio_value'],
            benchmark_values=benchmark_values['portfolio_value'],
            output_dir=universe_output_dir,
        )

        portfolio_comp = generate_portfolio_composition_log(
            rebalance_log=rebalance_log,
            output_dir=universe_output_dir,
            top_n=args.top_n,
        )

        # Print to console
        print_performance_summary(perf_summary, monthly_win_rate)
        print_yearly_summary(yearly_returns, yearly_win_rate)
        print_monthly_returns(monthly_returns)
        print_portfolio_composition(portfolio_comp)

        logger.info("="*70)
        logger.info(f"Backtest complete! All reports saved to output/{args.universe}/")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"Error during backtest: {e}", exc_info=True)
        sys.exit(1)


def run_signal_mode(args):
    """Run signal generation mode."""
    logger.info("="*70)
    logger.info("ETF RELATIVE STRENGTH - SIGNAL GENERATION")
    logger.info("="*70)

    # Load ETF universe
    try:
        etf_universe = load_universe_by_name(args.universe, config.ETFLIST_DIR)
    except Exception as e:
        logger.error(f"Error loading ETF universe: {e}")
        sys.exit(1)

    # Create universe-specific output directory
    universe_output_dir = config.OUTPUT_DIR / args.universe
    universe_output_dir.mkdir(exist_ok=True, parents=True)

    logger.info(f"Universe: {args.universe.upper()}")
    logger.info(f"Top N Holdings: {args.top_n}")
    logger.info(f"Number of ETFs: {len(etf_universe)}")
    logger.info(f"Benchmark: {config.BENCHMARK_TICKER}")
    logger.info("="*70)

    try:
        # Calculate data dates
        start_date, end_date = calculate_signal_data_dates(config.SIGNAL_DATA_LOOKBACK_DAYS)

        # Fetch price data
        logger.info("\n[1/3] Fetching recent price data...")
        all_tickers = list(etf_universe.keys()) + [config.BENCHMARK_TICKER]

        price_data = get_price_data(
            ticker_list=all_tickers,
            start_date=start_date,
            end_date=end_date,
            api_key=config.FMP_API_KEY,
            cache_path=str(config.PRICE_DATA_CACHE),
            force_refresh=True,  # Always fetch fresh data (no caching)
            api_delay=config.FMP_API_DELAY,
        )

        logger.info(f"Price data loaded: {price_data.shape[0]} days, {price_data.shape[1]} tickers")

        # Generate current signals
        logger.info("\n[2/3] Generating current signals...")
        etf_tickers = list(etf_universe.keys())

        signals, latest_date = generate_current_signals(
            price_data=price_data,
            etf_tickers=etf_tickers,
            spy_ticker=config.BENCHMARK_TICKER,
            sma_window=config.SMA_LOOKBACK_DAYS,
            roc_lookback=config.RS_ROC_LOOKBACK_DAYS,
        )

        # Select current portfolio
        portfolio = select_current_portfolio(
            signals=signals,
            latest_date=latest_date,
            top_n=args.top_n,
            spy_ticker=config.BENCHMARK_TICKER,
        )

        # Generate reports
        logger.info("\n[3/3] Generating reports...")

        signal_df = generate_signal_report(portfolio, universe_output_dir, etf_universe)

        # Print results
        print_signal_report(portfolio, signal_df)
        print_summary_stats(portfolio, signals)

        # Detailed status if requested
        if args.detailed:
            status = get_all_etf_current_status(signals, latest_date)
            detailed_df = generate_detailed_status_report(status, universe_output_dir, etf_universe)
            print_detailed_status(detailed_df, top_n=15)

        logger.info("="*70)
        logger.info(f"Signal generation complete! Reports saved to output/{args.universe}/:")
        logger.info(f"  - current_signals.csv")
        if args.detailed:
            logger.info(f"  - all_etf_status.csv")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"Error during signal generation: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main execution function."""
    args = parse_arguments()

    if args.mode == 'backtest':
        run_backtest_mode(args)
    elif args.mode == 'signal':
        run_signal_mode(args)
    else:
        logger.error("Please specify a mode: 'backtest' or 'signal'")
        logger.info("Examples:")
        logger.info("  uv run python -m etfmomentum backtest")
        logger.info("  uv run python -m etfmomentum signal")
        logger.info("  uv run python -m etfmomentum backtest --refresh")
        logger.info("  uv run python -m etfmomentum signal --detailed")
        sys.exit(1)


if __name__ == "__main__":
    main()

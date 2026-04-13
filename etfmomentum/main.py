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
    get_all_etf_current_status,
    _compute_tickers,
    build_portfolio_from_tickers,
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
                                 choices=['emerging', 'developed', 'sp500', 'commodity', 'multi_asset', 'factor', 'bond'],
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

    # Short-optimize mode
    so_parser = subparsers.add_parser('short-optimize', help='Grid search over short sleeve parameters')
    so_parser.add_argument('--universe', type=str, default='emerging',
                           choices=['emerging', 'developed', 'sp500', 'commodity', 'multi_asset', 'factor', 'bond'],
                           help='ETF universe to optimize against (default: emerging)')
    so_parser.add_argument('--start-date', type=str, default='2016-01-01',
                           help='Backtest start date (default: 2016-01-01)')
    so_parser.add_argument('--end-date', type=str, default='2026-04-08',
                           help='Backtest end date (default: 2026-04-08)')

    # Walk-forward mode
    wf_parser = subparsers.add_parser('walk-forward', help='Run walk-forward validation')
    wf_parser.add_argument('--universe', type=str, default='sp500',
                           choices=['emerging', 'developed', 'sp500', 'commodity', 'multi_asset', 'factor', 'bond'],
                           help='ETF universe to use (default: sp500)')
    wf_parser.add_argument('--refresh', action='store_true', help='Force re-download data')

    # Signal mode
    signal_parser = subparsers.add_parser('signal', help='Generate current month signals')
    signal_parser.add_argument('--universe', type=str, default='emerging',
                               choices=['emerging', 'developed', 'sp500', 'commodity', 'multi_asset', 'factor', 'bond'],
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
        strategy_values, benchmark_values, rebalance_log, short_stats = run_backtest(
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

        # Short sleeve summary (only shown when feature is enabled)
        if short_stats.get('enabled'):
            total = short_stats['total_rebalances']
            active = short_stats['weeks_with_shorts']
            logger.info("=" * 70)
            logger.info("SHORT SLEEVE SUMMARY")
            logger.info("=" * 70)
            logger.info(f"  Activation rate : {active}/{total} weeks ({active/total*100:.0f}%)")
            logger.info(f"  Avg gross exp   : {short_stats['avg_gross_exposure']:.1%}")
            logger.info(f"  Stop triggers   : {short_stats['stop_triggers']}")
            logger.info("=" * 70)

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

        # Fetch price data — include SGOV so breadth filter and cash replacement work
        logger.info("\n[1/3] Fetching recent price data...")
        etf_tickers = list(etf_universe.keys())
        all_tickers = etf_tickers + [config.BENCHMARK_TICKER, config.CASH_TICKER]

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

        # Generate current signals — use per-universe params (same as backtest + run_signals)
        logger.info("\n[2/3] Generating current signals...")
        params = config.UNIVERSE_PARAMS.get(args.universe, config.UNIVERSE_PARAMS["sp500"])

        signals, latest_date = generate_current_signals(
            price_data=price_data,
            etf_tickers=etf_tickers,
            spy_ticker=config.BENCHMARK_TICKER,
            sma_window=params["sma_lookback_days"],
            roc_lookback=params["roc_lookback_days"],
        )

        # Select portfolio through the full pipeline (breadth filter, correlation filter,
        # SGOV replacement) — identical path to backtest and third-party run_signals()
        selected_tickers = _compute_tickers(price_data, etf_tickers, latest_date, args.top_n, args.universe)
        portfolio = build_portfolio_from_tickers(selected_tickers, signals, latest_date, args.top_n)

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
    elif args.mode == 'walk-forward':
        from .walk_forward import run_walk_forward
        run_walk_forward(universe=args.universe, force_refresh=getattr(args, 'refresh', False))
    elif args.mode == 'short-optimize':
        from .short_optimizer import run_short_optimization
        run_short_optimization(
            universe=args.universe,
            start_date=args.start_date,
            end_date=args.end_date,
        )
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

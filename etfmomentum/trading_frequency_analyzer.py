"""
Trading Frequency Analyzer for Weekly Monitoring
Analyzes how many weeks actually required trades vs stayed unchanged.
"""

import pandas as pd
import logging
from typing import Dict, List
from collections import defaultdict

from . import config
from .data_fetcher import load_data_from_cache
from .signal_generator import generate_signals
from .backtest import run_backtest
from .volatility_regime import create_regime_detector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_trading_frequency(rebalance_log: List[Dict]) -> Dict:
    """
    Analyze how many rebalances resulted in actual trades.

    Args:
        rebalance_log: List of rebalance events from backtest

    Returns:
        Dictionary with trading frequency analysis
    """
    total_rebalances = len(rebalance_log)
    trades_executed = 0
    no_trades = 0

    # Track by year
    yearly_stats = defaultdict(lambda: {
        'weeks_checked': 0,
        'weeks_with_trades': 0,
        'weeks_no_trades': 0,
    })

    prev_holdings = None

    for i, event in enumerate(rebalance_log):
        date = event['date']
        year = date.year
        current_holdings = set(event['weights'].keys())

        yearly_stats[year]['weeks_checked'] += 1

        # First rebalance is always a trade (entering positions)
        if prev_holdings is None:
            trades_executed += 1
            yearly_stats[year]['weeks_with_trades'] += 1
        else:
            # Check if portfolio changed
            if current_holdings != prev_holdings:
                # Holdings changed - trade executed
                trades_executed += 1
                yearly_stats[year]['weeks_with_trades'] += 1
            else:
                # Check if weights changed even if same tickers
                prev_weights = rebalance_log[i-1]['weights']
                curr_weights = event['weights']

                weights_changed = False
                for ticker in current_holdings:
                    prev_w = prev_weights.get(ticker, 0)
                    curr_w = curr_weights.get(ticker, 0)
                    # Consider changed if difference > 1%
                    if abs(prev_w - curr_w) > 0.01:
                        weights_changed = True
                        break

                if weights_changed:
                    trades_executed += 1
                    yearly_stats[year]['weeks_with_trades'] += 1
                else:
                    # No change - no trade
                    no_trades += 1
                    yearly_stats[year]['weeks_no_trades'] += 1

        prev_holdings = current_holdings

    return {
        'total_rebalances': total_rebalances,
        'trades_executed': trades_executed,
        'no_trades': no_trades,
        'yearly_stats': dict(yearly_stats),
    }


def run_weekly_trading_analysis(
    universe: str = 'sp500',
    initial_capital: float = 500000.0,
) -> Dict:
    """
    Run full backtest and analyze trading frequency.

    Returns:
        Dictionary with analysis results
    """
    logger.info("="*70)
    logger.info("WEEKLY TRADING FREQUENCY ANALYSIS")
    logger.info("="*70)

    # Load data
    price_data = load_data_from_cache(config.PRICE_DATA_CACHE)

    # Load ETF universe
    etflist_file = config.ETFLIST_DIR / f"{universe}_sector_etfs.csv"
    etf_df = pd.read_csv(etflist_file)
    etf_tickers = etf_df['Ticker'].tolist()
    spy_ticker = config.BENCHMARK_TICKER

    # Generate signals
    logger.info("\nGenerating signals...")
    signals = generate_signals(
        price_data,
        spy_ticker,
        etf_tickers,
        config.SMA_LOOKBACK_DAYS,
        config.RS_ROC_LOOKBACK_DAYS,
    )

    # Create regime detector
    regime_detector = create_regime_detector(config)

    # Run backtest with weekly monitoring
    logger.info(f"\nRunning backtest with {config.REBALANCE_FREQUENCY} monitoring...")
    strategy_df, benchmark_df, rebalance_log = run_backtest(
        signals=signals,
        price_data=price_data,
        spy_ticker=spy_ticker,
        start_date=config.BACKTEST_START_DATE,
        end_date=config.BACKTEST_END_DATE,
        initial_capital=initial_capital,
        top_n=config.TOP_N_HOLDINGS,
        regime_detector=regime_detector,
        rebalance_frequency=config.REBALANCE_FREQUENCY,
    )

    # Analyze trading frequency
    logger.info("\nAnalyzing trading frequency...")
    analysis = analyze_trading_frequency(rebalance_log)

    return {
        'analysis': analysis,
        'rebalance_log': rebalance_log,
        'strategy_df': strategy_df,
        'benchmark_df': benchmark_df,
    }


def print_trading_frequency_report(analysis: Dict):
    """Print formatted trading frequency report."""

    total_rebalances = analysis['total_rebalances']
    trades_executed = analysis['trades_executed']
    no_trades = analysis['no_trades']
    yearly_stats = analysis['yearly_stats']

    print("\n" + "="*80)
    print("TRADING FREQUENCY ANALYSIS - WEEKLY MONITORING")
    print("="*80)

    print(f"\n📊 OVERALL STATISTICS (10 Years)")
    print(f"   Total weekly checks: {total_rebalances}")
    print(f"   Weeks with trades: {trades_executed} ({trades_executed/total_rebalances*100:.1f}%)")
    print(f"   Weeks NO trades needed: {no_trades} ({no_trades/total_rebalances*100:.1f}%)")
    print(f"\n   Average trades per year: {trades_executed/10:.1f}")
    print(f"   Average no-trade weeks per year: {no_trades/10:.1f}")

    print("\n" + "="*80)
    print("YEAR-BY-YEAR BREAKDOWN")
    print("="*80)
    print()

    # Create summary table
    summary_data = []
    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        weeks_checked = stats['weeks_checked']
        weeks_with_trades = stats['weeks_with_trades']
        weeks_no_trades = stats['weeks_no_trades']

        trade_pct = (weeks_with_trades / weeks_checked * 100) if weeks_checked > 0 else 0

        summary_data.append({
            'Year': year,
            'Weeks Checked': weeks_checked,
            'Weeks WITH Trades': weeks_with_trades,
            'Weeks NO Trades': weeks_no_trades,
            'Trading %': f"{trade_pct:.1f}%",
        })

    df = pd.DataFrame(summary_data)
    print(df.to_string(index=False))

    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)

    # Find year with most/least trading
    max_trades_year = max(yearly_stats.items(), key=lambda x: x[1]['weeks_with_trades'])
    min_trades_year = min(yearly_stats.items(), key=lambda x: x[1]['weeks_with_trades'])

    print(f"\n📈 Most Active Year: {max_trades_year[0]}")
    print(f"   {max_trades_year[1]['weeks_with_trades']} weeks with trades")
    print(f"   {max_trades_year[1]['weeks_no_trades']} weeks with no trades")

    print(f"\n📉 Least Active Year: {min_trades_year[0]}")
    print(f"   {min_trades_year[1]['weeks_with_trades']} weeks with trades")
    print(f"   {min_trades_year[1]['weeks_no_trades']} weeks with no trades")

    # Average trading frequency
    avg_trade_pct = (trades_executed / total_rebalances * 100)
    print(f"\n💡 On Average:")
    print(f"   {avg_trade_pct:.1f}% of weeks require trading")
    print(f"   {100-avg_trade_pct:.1f}% of weeks portfolio stays unchanged")

    print("\n" + "="*80)


if __name__ == "__main__":
    results = run_weekly_trading_analysis(
        universe='sp500',
        initial_capital=500000.0,
    )

    print_trading_frequency_report(results['analysis'])

    # Save detailed results
    output_dir = config.OUTPUT_DIR / 'sp500'
    output_dir.mkdir(exist_ok=True)

    # Save yearly summary
    yearly_stats = results['analysis']['yearly_stats']
    summary_data = []
    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        summary_data.append({
            'year': year,
            'weeks_checked': stats['weeks_checked'],
            'weeks_with_trades': stats['weeks_with_trades'],
            'weeks_no_trades': stats['weeks_no_trades'],
            'trading_percentage': stats['weeks_with_trades'] / stats['weeks_checked'] * 100 if stats['weeks_checked'] > 0 else 0,
        })

    df = pd.DataFrame(summary_data)
    output_file = output_dir / 'weekly_trading_frequency.csv'
    df.to_csv(output_file, index=False)
    logger.info(f"\n💾 Results saved to: {output_file}")

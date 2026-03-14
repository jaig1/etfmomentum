"""
Volatility Timing Analysis
Analyzes whether monthly volatility checks are too slow to detect and respond to market crashes.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from . import config
from .data_fetcher import load_data_from_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_daily_volatility(prices: pd.Series, lookback_days: int = 30) -> pd.Series:
    """
    Calculate rolling volatility for each day.

    Args:
        prices: Daily price series
        lookback_days: Rolling window for volatility calculation

    Returns:
        Series of annualized volatility for each day
    """
    # Calculate daily returns
    returns = prices.pct_change().dropna()

    # Calculate rolling volatility
    rolling_vol = returns.rolling(window=lookback_days).std() * np.sqrt(252)

    return rolling_vol


def classify_regime(volatility: float, low_threshold: float = 0.10, high_threshold: float = 0.25) -> str:
    """Classify volatility into regime."""
    if pd.isna(volatility):
        return 'UNKNOWN'
    elif volatility < low_threshold:
        return 'LOW'
    elif volatility > high_threshold:
        return 'HIGH'
    else:
        return 'MEDIUM'


def get_monthly_rebalance_dates(start_date: str, end_date: str, price_data: pd.DataFrame) -> List[pd.Timestamp]:
    """
    Get first trading day of each month (monthly rebalance dates).

    Args:
        start_date: Start date
        end_date: End date
        price_data: Price data with dates as index

    Returns:
        List of monthly rebalance dates
    """
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    # Get all trading dates in range
    trading_dates = price_data.loc[start:end].index

    # Group by month and get first trading day of each month
    monthly_dates = []
    for date in trading_dates:
        # Check if this is the first trading day of the month
        if date.day <= 7:  # Within first week
            # Check if it's the first in this month
            month_key = (date.year, date.month)
            if not any((d.year, d.month) == month_key for d in monthly_dates):
                monthly_dates.append(date)

    return sorted(monthly_dates)


def find_regime_changes(daily_regimes: pd.Series) -> List[Dict]:
    """
    Find all regime changes in the time series.

    Args:
        daily_regimes: Series of daily regime classifications

    Returns:
        List of regime change events
    """
    changes = []
    prev_regime = None

    for date, regime in daily_regimes.items():
        if regime == 'UNKNOWN':
            continue

        if prev_regime is not None and regime != prev_regime:
            changes.append({
                'date': date,
                'from_regime': prev_regime,
                'to_regime': regime,
                'change_type': f"{prev_regime} → {regime}"
            })

        prev_regime = regime

    return changes


def analyze_detection_lag(
    regime_changes: List[Dict],
    monthly_rebalance_dates: List[pd.Timestamp],
    spy_prices: pd.Series,
) -> pd.DataFrame:
    """
    Analyze how long it would take for monthly checks to detect regime changes.

    Args:
        regime_changes: List of regime change events
        monthly_rebalance_dates: Monthly rebalance dates
        spy_prices: SPY price series

    Returns:
        DataFrame with lag analysis
    """
    analysis = []

    for change in regime_changes:
        change_date = change['date']

        # Find next monthly rebalance after the change
        next_rebalance = None
        for rebal_date in monthly_rebalance_dates:
            if rebal_date > change_date:
                next_rebalance = rebal_date
                break

        if next_rebalance is None:
            continue

        # Calculate lag in trading days
        lag_days = len(spy_prices.loc[change_date:next_rebalance]) - 1

        # Calculate price change during lag period
        if change_date in spy_prices.index and next_rebalance in spy_prices.index:
            price_at_change = spy_prices.loc[change_date]
            price_at_detection = spy_prices.loc[next_rebalance]
            price_change_pct = ((price_at_detection - price_at_change) / price_at_change) * 100
        else:
            price_change_pct = np.nan

        analysis.append({
            'regime_change_date': change_date,
            'change_type': change['change_type'],
            'from_regime': change['from_regime'],
            'to_regime': change['to_regime'],
            'monthly_detection_date': next_rebalance,
            'lag_days': lag_days,
            'spy_price_change_during_lag': price_change_pct,
        })

    return pd.DataFrame(analysis)


def identify_major_crashes(
    spy_prices: pd.Series,
    daily_volatility: pd.Series,
) -> List[Dict]:
    """
    Identify major crash events.

    Args:
        spy_prices: SPY price series
        daily_volatility: Daily volatility series

    Returns:
        List of crash events
    """
    crashes = []

    # Calculate daily returns
    daily_returns = spy_prices.pct_change()

    # Find days with extreme moves
    for date, ret in daily_returns.items():
        if pd.isna(ret):
            continue

        # Major single-day drop (>3%)
        if ret < -0.03:
            vol = daily_volatility.loc[date] if date in daily_volatility.index else np.nan
            crashes.append({
                'date': date,
                'type': 'Single-day drop',
                'spy_return': ret * 100,
                'volatility': vol,
                'severity': 'High' if ret < -0.05 else 'Medium',
            })

    return crashes


def analyze_crash_periods(
    spy_prices: pd.Series,
    daily_regimes: pd.Series,
    monthly_rebalance_dates: List[pd.Timestamp],
) -> Dict:
    """
    Analyze specific known crash periods.

    Args:
        spy_prices: SPY price series
        daily_regimes: Daily regime classifications
        monthly_rebalance_dates: Monthly rebalance dates

    Returns:
        Dictionary with crash period analysis
    """
    crash_periods = {
        'COVID_2020': {
            'name': 'COVID Crash (Feb-Mar 2020)',
            'start': '2020-02-01',
            'end': '2020-04-01',
        },
        'BEAR_2022': {
            'name': '2022 Bear Market',
            'start': '2022-01-01',
            'end': '2022-10-31',
        },
        'SELLOFF_2018': {
            'name': 'Late 2018 Selloff',
            'start': '2018-10-01',
            'end': '2018-12-31',
        },
    }

    results = {}

    for key, period in crash_periods.items():
        start = pd.Timestamp(period['start'])
        end = pd.Timestamp(period['end'])

        # Get data for this period
        period_prices = spy_prices.loc[start:end]
        period_regimes = daily_regimes.loc[start:end]

        if len(period_prices) == 0:
            continue

        # Find when regime first hit HIGH
        first_high = None
        for date, regime in period_regimes.items():
            if regime == 'HIGH':
                first_high = date
                break

        # Find when monthly check would have detected it
        monthly_detection = None
        if first_high is not None:
            for rebal_date in monthly_rebalance_dates:
                if rebal_date >= first_high:
                    monthly_detection = rebal_date
                    break

        # Calculate drawdown
        peak = period_prices.max()
        trough = period_prices.min()
        drawdown = ((trough - peak) / peak) * 100

        results[key] = {
            'period_name': period['name'],
            'start_date': start,
            'end_date': end,
            'first_high_vol_date': first_high,
            'monthly_detection_date': monthly_detection,
            'detection_lag_days': (monthly_detection - first_high).days if first_high and monthly_detection else None,
            'max_drawdown': drawdown,
            'peak_price': peak,
            'trough_price': trough,
        }

    return results


def run_volatility_timing_analysis() -> Dict:
    """
    Run complete volatility timing analysis.

    Returns:
        Dictionary with all analysis results
    """
    logger.info("="*70)
    logger.info("VOLATILITY TIMING ANALYSIS")
    logger.info("Analyzing if monthly volatility checks are too slow")
    logger.info("="*70)

    # Load price data
    logger.info("\nLoading price data...")
    price_data = load_data_from_cache(config.PRICE_DATA_CACHE)
    spy_prices = price_data['SPY']

    # Calculate daily volatility
    logger.info("Calculating daily 30-day rolling volatility...")
    daily_volatility = calculate_daily_volatility(spy_prices, lookback_days=30)

    # Classify into regimes
    logger.info("Classifying daily regimes...")
    daily_regimes = daily_volatility.apply(
        lambda v: classify_regime(v, config.LOW_VOL_THRESHOLD, config.HIGH_VOL_THRESHOLD)
    )

    # Get monthly rebalance dates
    monthly_rebalance_dates = get_monthly_rebalance_dates(
        config.BACKTEST_START_DATE,
        config.BACKTEST_END_DATE,
        price_data
    )

    logger.info(f"Found {len(monthly_rebalance_dates)} monthly rebalance dates")

    # Find all regime changes
    logger.info("\nFinding regime changes...")
    regime_changes = find_regime_changes(daily_regimes)
    logger.info(f"Found {len(regime_changes)} regime changes")

    # Analyze detection lag
    logger.info("\nAnalyzing detection lag for regime changes...")
    lag_analysis = analyze_detection_lag(regime_changes, monthly_rebalance_dates, spy_prices)

    # Identify major crashes
    logger.info("\nIdentifying major crash events...")
    crashes = identify_major_crashes(spy_prices, daily_volatility)
    logger.info(f"Found {len(crashes)} major single-day drops (>3%)")

    # Analyze specific crash periods
    logger.info("\nAnalyzing specific crash periods...")
    crash_periods = analyze_crash_periods(spy_prices, daily_regimes, monthly_rebalance_dates)

    return {
        'daily_volatility': daily_volatility,
        'daily_regimes': daily_regimes,
        'regime_changes': regime_changes,
        'lag_analysis': lag_analysis,
        'crashes': crashes,
        'crash_periods': crash_periods,
        'monthly_rebalance_dates': monthly_rebalance_dates,
    }


def print_analysis_summary(results: Dict):
    """Print formatted analysis summary."""

    print("\n" + "="*80)
    print("REGIME CHANGE DETECTION LAG ANALYSIS")
    print("="*80)

    lag_df = results['lag_analysis']

    # Filter for important changes (to HIGH volatility)
    to_high = lag_df[lag_df['to_regime'] == 'HIGH'].copy()

    if len(to_high) > 0:
        print(f"\n📈 TRANSITIONS TO HIGH VOLATILITY ({len(to_high)} events):")
        print("\nHow long did monthly checks delay detection?\n")

        for _, row in to_high.iterrows():
            print(f"  {row['regime_change_date'].strftime('%Y-%m-%d')}: {row['change_type']}")
            print(f"    ⏱️  Detection lag: {row['lag_days']} trading days")
            print(f"    📉 SPY change during lag: {row['spy_price_change_during_lag']:.2f}%")
            print()

        # Summary statistics
        avg_lag = to_high['lag_days'].mean()
        max_lag = to_high['lag_days'].max()
        avg_spy_change = to_high['spy_price_change_during_lag'].mean()
        worst_spy_change = to_high['spy_price_change_during_lag'].min()

        print(f"  📊 STATISTICS:")
        print(f"    Average lag: {avg_lag:.1f} days")
        print(f"    Maximum lag: {max_lag:.0f} days")
        print(f"    Average SPY change during lag: {avg_spy_change:.2f}%")
        print(f"    Worst SPY change during lag: {worst_spy_change:.2f}%")

    print("\n" + "="*80)
    print("SPECIFIC CRASH PERIOD ANALYSIS")
    print("="*80)

    for key, period in results['crash_periods'].items():
        print(f"\n📌 {period['period_name']}")
        print(f"   Period: {period['start_date'].strftime('%Y-%m-%d')} to {period['end_date'].strftime('%Y-%m-%d')}")

        if period['first_high_vol_date']:
            print(f"   🔴 High volatility first detected: {period['first_high_vol_date'].strftime('%Y-%m-%d')}")
            print(f"   📅 Monthly check would detect: {period['monthly_detection_date'].strftime('%Y-%m-%d')}")
            print(f"   ⏱️  Detection lag: {period['detection_lag_days']} days")
        else:
            print(f"   ✅ No HIGH volatility regime during this period")

        print(f"   📉 Maximum drawdown: {period['max_drawdown']:.2f}%")

    print("\n" + "="*80)
    print("MAJOR SINGLE-DAY DROPS (>3%)")
    print("="*80)

    crash_df = pd.DataFrame(results['crashes'])
    if len(crash_df) > 0:
        severe_crashes = crash_df[crash_df['severity'] == 'High'].sort_values('spy_return')

        print(f"\n🔻 Found {len(severe_crashes)} severe single-day drops (>5%):\n")

        for _, crash in severe_crashes.head(10).iterrows():
            print(f"  {crash['date'].strftime('%Y-%m-%d')}: {crash['spy_return']:.2f}% | Vol: {crash['volatility']:.1%}")

    print("\n" + "="*80)


if __name__ == "__main__":
    results = run_volatility_timing_analysis()
    print_analysis_summary(results)

    # Save results
    output_dir = config.OUTPUT_DIR / 'sp500'
    output_dir.mkdir(exist_ok=True)

    # Save lag analysis
    lag_file = output_dir / 'volatility_timing_lag_analysis.csv'
    results['lag_analysis'].to_csv(lag_file, index=False)
    logger.info(f"\n💾 Lag analysis saved to: {lag_file}")

    # Save crash analysis
    crash_file = output_dir / 'major_crashes.csv'
    pd.DataFrame(results['crashes']).to_csv(crash_file, index=False)
    logger.info(f"💾 Crash analysis saved to: {crash_file}")

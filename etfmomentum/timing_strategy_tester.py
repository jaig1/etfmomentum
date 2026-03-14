"""
Timing Strategy Tester
Tests different volatility monitoring frequencies and emergency response systems.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from . import config
from .data_fetcher import load_data_from_cache
from .signal_generator import generate_signals
from .backtest import get_qualifying_etfs, select_portfolio
from .report import calculate_metrics
from .volatility_regime import VolatilityRegime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CircuitBreakerDetector:
    """Detects emergency market conditions requiring immediate defensive action."""

    def __init__(
        self,
        single_day_drop_threshold: float = -0.05,  # -5%
        rolling_vol_threshold: float = 0.30,  # 30% annualized
        rolling_vol_days: int = 3,
        vix_threshold: float = 40.0,
        vix_consecutive_days: int = 2,
    ):
        self.single_day_drop_threshold = single_day_drop_threshold
        self.rolling_vol_threshold = rolling_vol_threshold
        self.rolling_vol_days = rolling_vol_days
        self.vix_threshold = vix_threshold
        self.vix_consecutive_days = vix_consecutive_days
        self.vix_high_days = 0  # Track consecutive high VIX days

    def check_emergency(
        self,
        spy_prices: pd.Series,
        date: pd.Timestamp,
        vix_prices: Optional[pd.Series] = None,
    ) -> Tuple[bool, str]:
        """
        Check if emergency conditions are met.

        Returns:
            (is_emergency, trigger_reason)
        """
        # Get data up to date
        spy_data = spy_prices.loc[:date]

        if len(spy_data) < 2:
            return False, None

        # Check 1: Single-day drop >5%
        daily_return = (spy_data.iloc[-1] - spy_data.iloc[-2]) / spy_data.iloc[-2]
        if daily_return < self.single_day_drop_threshold:
            return True, f"Single-day drop {daily_return*100:.2f}%"

        # Check 2: 3-day rolling volatility >30%
        if len(spy_data) >= self.rolling_vol_days + 1:
            recent_returns = spy_data.tail(self.rolling_vol_days + 1).pct_change().dropna()
            if len(recent_returns) >= self.rolling_vol_days:
                rolling_vol = recent_returns.std() * np.sqrt(252)
                if rolling_vol > self.rolling_vol_threshold:
                    return True, f"3-day rolling vol {rolling_vol*100:.1f}%"

        # Check 3: VIX >40 for 2 consecutive days
        if vix_prices is not None and date in vix_prices.index:
            current_vix = vix_prices.loc[date]

            if current_vix > self.vix_threshold:
                self.vix_high_days += 1
                if self.vix_high_days >= self.vix_consecutive_days:
                    return True, f"VIX {current_vix:.1f} for {self.vix_high_days} days"
            else:
                self.vix_high_days = 0

        return False, None


def run_circuit_breaker_backtest(
    signals: Dict[str, pd.DataFrame],
    price_data: pd.DataFrame,
    spy_ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    top_n: int,
) -> Tuple[pd.Series, pd.Series, List[Dict]]:
    """
    Run backtest with circuit breaker emergency system.

    Monthly rebalancing + daily emergency checks.
    """
    logger.info("Running Circuit Breaker Strategy...")

    # Get date range
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    trading_dates = price_data.loc[start:end].index

    # Monthly rebalance dates
    monthly_rebalance_dates = []
    for date in trading_dates:
        if date.day <= 7:
            month_key = (date.year, date.month)
            if not any((d.year, d.month) == month_key for d in monthly_rebalance_dates):
                monthly_rebalance_dates.append(date)

    # Initialize circuit breaker
    circuit_breaker = CircuitBreakerDetector()

    # Get VIX data if available
    vix_prices = price_data['^VIX'] if '^VIX' in price_data.columns else None

    # Portfolio tracking
    portfolio_value = pd.Series(index=trading_dates, dtype=float)
    portfolio_value.iloc[0] = initial_capital
    current_holdings = {}
    rebalance_log = []
    emergency_active = False
    next_monthly_rebalance_idx = 0
    next_monthly_rebalance = monthly_rebalance_dates[0]

    # Benchmark
    spy_prices = price_data[spy_ticker]
    spy_start_price = spy_prices.loc[trading_dates[0]]
    spy_shares = initial_capital / spy_start_price
    benchmark_value = spy_prices.loc[trading_dates] * spy_shares

    for i, date in enumerate(trading_dates):
        # Daily emergency check
        if not emergency_active:
            is_emergency, trigger = circuit_breaker.check_emergency(spy_prices, date, vix_prices)

            if is_emergency:
                logger.info(f"🚨 EMERGENCY TRIGGERED on {date.date()}: {trigger}")
                emergency_active = True

                # Go 100% SPY immediately
                current_holdings = {spy_ticker: 1.0}

                rebalance_log.append({
                    'date': date,
                    'type': 'EMERGENCY',
                    'trigger': trigger,
                    'selected': [spy_ticker],
                    'weights': {spy_ticker: 1.0},
                })

        # Monthly rebalancing (resume normal strategy after emergency)
        if date >= next_monthly_rebalance:
            qualifying = get_qualifying_etfs(signals, date)
            new_holdings = select_portfolio(qualifying, top_n, spy_ticker)

            # Exit emergency mode
            if emergency_active:
                logger.info(f"📅 Monthly rebalance on {date.date()}: Exiting emergency mode")
                emergency_active = False

            rebalance_log.append({
                'date': date,
                'type': 'MONTHLY',
                'qualifying_count': len(qualifying),
                'selected': list(new_holdings.keys()),
                'weights': new_holdings.copy(),
            })

            current_holdings = new_holdings

            # Move to next monthly rebalance
            next_monthly_rebalance_idx += 1
            if next_monthly_rebalance_idx < len(monthly_rebalance_dates):
                next_monthly_rebalance = monthly_rebalance_dates[next_monthly_rebalance_idx]
            else:
                next_monthly_rebalance = pd.Timestamp.max

        # Calculate portfolio value
        if i == 0:
            continue

        prev_date = trading_dates[i - 1]
        portfolio_return = 0.0

        for ticker, weight in current_holdings.items():
            if ticker not in price_data.columns:
                continue

            prev_price = price_data.loc[prev_date, ticker]
            curr_price = price_data.loc[date, ticker]

            if pd.notna(prev_price) and pd.notna(curr_price) and prev_price != 0:
                asset_return = (curr_price - prev_price) / prev_price
                portfolio_return += weight * asset_return

        portfolio_value.loc[date] = portfolio_value.loc[prev_date] * (1 + portfolio_return)

    return portfolio_value, benchmark_value, rebalance_log


def run_weekly_monitoring_backtest(
    signals: Dict[str, pd.DataFrame],
    price_data: pd.DataFrame,
    spy_ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    top_n: int,
) -> Tuple[pd.Series, pd.Series, List[Dict]]:
    """
    Run backtest with weekly volatility monitoring and rebalancing.
    """
    logger.info("Running Weekly Monitoring Strategy...")

    # Get date range
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    trading_dates = price_data.loc[start:end].index

    # Weekly rebalance dates (every Monday, or first trading day of week)
    weekly_rebalance_dates = []
    current_week = None
    for date in trading_dates:
        week_key = (date.year, date.isocalendar()[1])  # (year, week_number)
        if week_key != current_week:
            weekly_rebalance_dates.append(date)
            current_week = week_key

    logger.info(f"Weekly rebalances: {len(weekly_rebalance_dates)} dates")

    # Initialize regime detector
    regime_detector = VolatilityRegime(
        lookback_days=config.VOLATILITY_LOOKBACK_DAYS,
        low_vol_threshold=config.LOW_VOL_THRESHOLD,
        high_vol_threshold=config.HIGH_VOL_THRESHOLD,
        low_vol_top_n=config.LOW_VOL_TOP_N,
        medium_vol_top_n=config.MEDIUM_VOL_TOP_N,
        high_vol_top_n=config.HIGH_VOL_TOP_N,
        high_vol_spy_allocation=config.HIGH_VOL_SPY_MIN_ALLOCATION,
    )

    # Portfolio tracking
    portfolio_value = pd.Series(index=trading_dates, dtype=float)
    portfolio_value.iloc[0] = initial_capital
    current_holdings = {}
    rebalance_log = []
    next_rebalance_idx = 0
    next_rebalance = weekly_rebalance_dates[0]

    # Benchmark
    spy_prices = price_data[spy_ticker]
    spy_start_price = spy_prices.loc[trading_dates[0]]
    spy_shares = initial_capital / spy_start_price
    benchmark_value = spy_prices.loc[trading_dates] * spy_shares

    for i, date in enumerate(trading_dates):
        # Weekly rebalancing
        if date >= next_rebalance:
            # Detect regime
            regime = regime_detector.detect_regime(spy_prices, date)
            regime_params = regime_detector.get_regime_parameters(regime)
            active_top_n = regime_params['top_n']

            # Select portfolio
            qualifying = get_qualifying_etfs(signals, date)
            new_holdings = select_portfolio(qualifying, active_top_n, spy_ticker)

            # Adjust for regime
            new_holdings = regime_detector.adjust_portfolio_for_regime(
                new_holdings, regime_params, spy_ticker
            )

            rebalance_log.append({
                'date': date,
                'type': 'WEEKLY',
                'regime': regime_params['regime'],
                'qualifying_count': len(qualifying),
                'selected': list(new_holdings.keys()),
                'weights': new_holdings.copy(),
            })

            current_holdings = new_holdings

            # Move to next weekly rebalance
            next_rebalance_idx += 1
            if next_rebalance_idx < len(weekly_rebalance_dates):
                next_rebalance = weekly_rebalance_dates[next_rebalance_idx]
            else:
                next_rebalance = pd.Timestamp.max

        # Calculate portfolio value
        if i == 0:
            continue

        prev_date = trading_dates[i - 1]
        portfolio_return = 0.0

        for ticker, weight in current_holdings.items():
            if ticker not in price_data.columns:
                continue

            prev_price = price_data.loc[prev_date, ticker]
            curr_price = price_data.loc[date, ticker]

            if pd.notna(prev_price) and pd.notna(curr_price) and prev_price != 0:
                asset_return = (curr_price - prev_price) / prev_price
                portfolio_return += weight * asset_return

        portfolio_value.loc[date] = portfolio_value.loc[prev_date] * (1 + portfolio_return)

    return portfolio_value, benchmark_value, rebalance_log


def run_hybrid_backtest(
    signals: Dict[str, pd.DataFrame],
    price_data: pd.DataFrame,
    spy_ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    top_n: int,
) -> Tuple[pd.Series, pd.Series, List[Dict]]:
    """
    Run backtest with hybrid approach: Monthly + Emergency Override.

    - Monthly rebalancing for normal conditions
    - Daily monitoring for sudden regime spikes
    - Emergency override: 50% cash, 50% current positions
    """
    logger.info("Running Hybrid Strategy (Monthly + Emergency)...")

    # Get date range
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    trading_dates = price_data.loc[start:end].index

    # Monthly rebalance dates
    monthly_rebalance_dates = []
    for date in trading_dates:
        if date.day <= 7:
            month_key = (date.year, date.month)
            if not any((d.year, d.month) == month_key for d in monthly_rebalance_dates):
                monthly_rebalance_dates.append(date)

    # Initialize regime detector and circuit breaker
    regime_detector = VolatilityRegime(
        lookback_days=config.VOLATILITY_LOOKBACK_DAYS,
        low_vol_threshold=config.LOW_VOL_THRESHOLD,
        high_vol_threshold=config.HIGH_VOL_THRESHOLD,
        low_vol_top_n=config.LOW_VOL_TOP_N,
        medium_vol_top_n=config.MEDIUM_VOL_TOP_N,
        high_vol_top_n=config.HIGH_VOL_TOP_N,
        high_vol_spy_allocation=config.HIGH_VOL_SPY_MIN_ALLOCATION,
    )

    circuit_breaker = CircuitBreakerDetector()
    vix_prices = price_data['^VIX'] if '^VIX' in price_data.columns else None

    # Portfolio tracking
    portfolio_value = pd.Series(index=trading_dates, dtype=float)
    portfolio_value.iloc[0] = initial_capital
    current_holdings = {}
    base_holdings = {}  # Holdings before emergency override
    emergency_active = False
    rebalance_log = []
    next_monthly_rebalance_idx = 0
    next_monthly_rebalance = monthly_rebalance_dates[0]

    # Benchmark
    spy_prices = price_data[spy_ticker]
    spy_start_price = spy_prices.loc[trading_dates[0]]
    spy_shares = initial_capital / spy_start_price
    benchmark_value = spy_prices.loc[trading_dates] * spy_shares

    for i, date in enumerate(trading_dates):
        # Daily emergency check
        if not emergency_active:
            is_emergency, trigger = circuit_breaker.check_emergency(spy_prices, date, vix_prices)

            if is_emergency:
                logger.info(f"🚨 EMERGENCY OVERRIDE on {date.date()}: {trigger}")
                emergency_active = True

                # Emergency override: 50% cash (SPY), 50% current positions
                base_holdings = current_holdings.copy()
                emergency_holdings = {}

                for ticker, weight in base_holdings.items():
                    emergency_holdings[ticker] = weight * 0.5

                emergency_holdings[spy_ticker] = emergency_holdings.get(spy_ticker, 0) + 0.5

                current_holdings = emergency_holdings

                rebalance_log.append({
                    'date': date,
                    'type': 'EMERGENCY_OVERRIDE',
                    'trigger': trigger,
                    'selected': list(current_holdings.keys()),
                    'weights': current_holdings.copy(),
                })

        # Monthly rebalancing
        if date >= next_monthly_rebalance:
            # Detect regime
            regime = regime_detector.detect_regime(spy_prices, date)
            regime_params = regime_detector.get_regime_parameters(regime)
            active_top_n = regime_params['top_n']

            # Select portfolio
            qualifying = get_qualifying_etfs(signals, date)
            new_holdings = select_portfolio(qualifying, active_top_n, spy_ticker)

            # Adjust for regime
            new_holdings = regime_detector.adjust_portfolio_for_regime(
                new_holdings, regime_params, spy_ticker
            )

            # Exit emergency mode
            if emergency_active:
                logger.info(f"📅 Monthly rebalance on {date.date()}: Exiting emergency override")
                emergency_active = False

            rebalance_log.append({
                'date': date,
                'type': 'MONTHLY',
                'regime': regime_params['regime'],
                'qualifying_count': len(qualifying),
                'selected': list(new_holdings.keys()),
                'weights': new_holdings.copy(),
            })

            current_holdings = new_holdings
            base_holdings = new_holdings.copy()

            # Move to next monthly rebalance
            next_monthly_rebalance_idx += 1
            if next_monthly_rebalance_idx < len(monthly_rebalance_dates):
                next_monthly_rebalance = monthly_rebalance_dates[next_monthly_rebalance_idx]
            else:
                next_monthly_rebalance = pd.Timestamp.max

        # Calculate portfolio value
        if i == 0:
            continue

        prev_date = trading_dates[i - 1]
        portfolio_return = 0.0

        for ticker, weight in current_holdings.items():
            if ticker not in price_data.columns:
                continue

            prev_price = price_data.loc[prev_date, ticker]
            curr_price = price_data.loc[date, ticker]

            if pd.notna(prev_price) and pd.notna(curr_price) and prev_price != 0:
                asset_return = (curr_price - prev_price) / prev_price
                portfolio_return += weight * asset_return

        portfolio_value.loc[date] = portfolio_value.loc[prev_date] * (1 + portfolio_return)

    return portfolio_value, benchmark_value, rebalance_log


def run_baseline_monthly_backtest(
    signals: Dict[str, pd.DataFrame],
    price_data: pd.DataFrame,
    spy_ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    top_n: int,
) -> Tuple[pd.Series, pd.Series, List[Dict]]:
    """Run baseline monthly rebalancing (current approach)."""
    logger.info("Running Baseline Monthly Strategy...")

    from .backtest import run_backtest
    from .volatility_regime import create_regime_detector

    regime_detector = create_regime_detector(config)

    strategy_df, benchmark_df, rebalance_log = run_backtest(
        signals=signals,
        price_data=price_data,
        spy_ticker=spy_ticker,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        top_n=top_n,
        regime_detector=regime_detector,
    )

    return strategy_df['portfolio_value'], benchmark_df['portfolio_value'], rebalance_log


def run_all_timing_tests(
    universe: str = 'sp500',
    initial_capital: float = 500000.0,
) -> pd.DataFrame:
    """
    Run all timing strategy tests and compare results.
    """
    logger.info("="*70)
    logger.info("VOLATILITY TIMING STRATEGY COMPARISON")
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

    # Define tests
    tests = [
        {
            'name': 'Baseline: Monthly Rebalancing',
            'function': run_baseline_monthly_backtest,
        },
        {
            'name': 'Option A: Circuit Breaker System',
            'function': run_circuit_breaker_backtest,
        },
        {
            'name': 'Option B: Weekly Monitoring',
            'function': run_weekly_monitoring_backtest,
        },
        {
            'name': 'Option C: Hybrid (Monthly + Emergency)',
            'function': run_hybrid_backtest,
        },
    ]

    results = []

    for test in tests:
        logger.info(f"\n{'='*70}")
        logger.info(f"Running: {test['name']}")
        logger.info(f"{'='*70}")

        strategy_values, benchmark_values, rebalance_log = test['function'](
            signals=signals,
            price_data=price_data,
            spy_ticker=spy_ticker,
            start_date=config.BACKTEST_START_DATE,
            end_date=config.BACKTEST_END_DATE,
            initial_capital=initial_capital,
            top_n=config.TOP_N_HOLDINGS,
        )

        # Calculate metrics
        strategy_metrics = calculate_metrics(strategy_values, initial_capital, config.RISK_FREE_RATE)
        benchmark_metrics = calculate_metrics(benchmark_values, initial_capital, config.RISK_FREE_RATE)

        # Count rebalances
        total_rebalances = len(rebalance_log)
        emergency_rebalances = len([r for r in rebalance_log if r.get('type') in ['EMERGENCY', 'EMERGENCY_OVERRIDE']])

        result = {
            'strategy': test['name'],
            'total_return': strategy_metrics['total_return'] * 100,
            'annualized_return': strategy_metrics['annualized_return'] * 100,
            'sharpe_ratio': strategy_metrics['sharpe_ratio'],
            'max_drawdown': strategy_metrics['max_drawdown'] * 100,
            'final_value': strategy_metrics['final_value'],
            'total_rebalances': total_rebalances,
            'emergency_rebalances': emergency_rebalances,
            'outperformance': (strategy_metrics['total_return'] - benchmark_metrics['total_return']) * 100,
        }

        results.append(result)

        logger.info(f"Total Return: {result['total_return']:.2f}%")
        logger.info(f"Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        logger.info(f"Max Drawdown: {result['max_drawdown']:.2f}%")
        logger.info(f"Rebalances: {total_rebalances} (Emergency: {emergency_rebalances})")

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('sharpe_ratio', ascending=False)

    return df_results


def print_comparison_summary(df_results: pd.DataFrame):
    """Print formatted comparison summary."""
    print("\n" + "="*100)
    print("VOLATILITY TIMING STRATEGY COMPARISON - FINAL RESULTS")
    print("="*100)
    print("\n📊 Ranked by Sharpe Ratio (Risk-Adjusted Returns):\n")

    for idx, row in df_results.iterrows():
        print(f"{'🏆 ' if idx == df_results.index[0] else '   '}{row['strategy']}")
        print(f"    Total Return: {row['total_return']:.2f}%")
        print(f"    Annualized: {row['annualized_return']:.2f}%")
        print(f"    Sharpe Ratio: {row['sharpe_ratio']:.3f}")
        print(f"    Max Drawdown: {row['max_drawdown']:.2f}%")
        print(f"    Final Value: ${row['final_value']:,.2f}")
        print(f"    Rebalances: {row['total_rebalances']} total ({row['emergency_rebalances']} emergency)")
        print(f"    vs SPY: +{row['outperformance']:.2f}%")
        print()

    print("="*100)

    # Highlight best
    best = df_results.iloc[0]
    print(f"\n🏆 WINNER: {best['strategy']}")
    print(f"   Sharpe: {best['sharpe_ratio']:.3f} | Return: {best['total_return']:.2f}% | Drawdown: {best['max_drawdown']:.2f}%")
    print()


if __name__ == "__main__":
    results_df = run_all_timing_tests(universe='sp500', initial_capital=500000.0)
    print_comparison_summary(results_df)

    # Save results
    output_dir = config.OUTPUT_DIR / 'sp500'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'timing_strategy_comparison.csv'
    results_df.to_csv(output_file, index=False)
    logger.info(f"\n💾 Results saved to: {output_file}")

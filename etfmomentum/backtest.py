"""Portfolio simulation and backtesting engine."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

from .rs_engine import get_qualifying_etfs

logger = logging.getLogger(__name__)


def get_rebalance_dates(
    price_data: pd.DataFrame,
    start_date: str,
    end_date: str,
    frequency: str = "monthly",
) -> List[pd.Timestamp]:
    """
    Identify rebalance dates within the backtest period.

    Args:
        price_data: DataFrame with dates as index
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        frequency: "weekly" or "monthly" (default: "monthly")

    Returns:
        List of rebalance dates
    """
    # Filter to backtest period
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    backtest_dates = price_data.index[mask]

    if len(backtest_dates) == 0:
        raise ValueError(f"No trading dates found between {start_date} and {end_date}")

    rebalance_dates = []

    if frequency == "weekly":
        # First trading day of each week
        current_week = None
        for date in backtest_dates:
            week_key = (date.year, date.isocalendar()[1])  # (year, week_number)
            if week_key != current_week:
                rebalance_dates.append(date)
                current_week = week_key

    elif frequency == "monthly":
        # First trading day of each month
        current_month = None
        for date in backtest_dates:
            year_month = (date.year, date.month)
            if year_month != current_month:
                rebalance_dates.append(date)
                current_month = year_month

    else:
        raise ValueError(f"Invalid frequency: {frequency}. Must be 'weekly' or 'monthly'")

    logger.info(f"Found {len(rebalance_dates)} {frequency} rebalance dates")
    return rebalance_dates


def select_defensive_portfolio(
    defensive_allocation: Dict,
    signals: Dict[str, pd.DataFrame],
    date: pd.Timestamp,
    top_n: int = 3,
) -> Dict[str, float]:
    """
    Select defensive portfolio based on defensive allocation strategy.

    Args:
        defensive_allocation: Defensive allocation dict from regime detector
        signals: All ETF signals
        date: Current date
        top_n: Number of defensive ETFs to hold (if ranking)

    Returns:
        Dictionary mapping ticker to allocation weight
    """
    mode = defensive_allocation.get('mode')

    if mode == 'defensive_sectors':
        # Rank defensive sectors by RS and select top N
        defensive_tickers = defensive_allocation['tickers']

        # Get RS values for defensive sectors
        defensive_rs = []
        for ticker in defensive_tickers:
            if ticker in signals:
                ticker_signals = signals[ticker]
                if date in ticker_signals.index:
                    row = ticker_signals.loc[date]
                    defensive_rs.append({
                        'ticker': ticker,
                        'rs_roc': row.get('rs_roc', 0),
                    })

        # Sort by RS ROC
        defensive_rs = sorted(defensive_rs, key=lambda x: x['rs_roc'], reverse=True)

        # Select top N
        selected_n = min(top_n, len(defensive_rs))
        if selected_n == 0:
            # No defensive sectors available, return empty
            return {}

        weight = 1.0 / selected_n
        portfolio = {}
        for i in range(selected_n):
            portfolio[defensive_rs[i]['ticker']] = weight

        return portfolio

    elif mode == 'tbills':
        # 100% T-Bills
        return defensive_allocation.get('allocation', {})

    elif mode == 'hybrid':
        # Split between T-Bills and defensive sectors
        tbill_ticker = defensive_allocation['tbill_ticker']
        tbill_allocation = defensive_allocation['tbill_allocation']
        defensive_sectors = defensive_allocation['defensive_sectors']
        sector_allocation = defensive_allocation['sector_allocation']

        portfolio = {tbill_ticker: tbill_allocation}

        # Equal-weight defensive sectors with remaining allocation
        if len(defensive_sectors) > 0:
            sector_weight = sector_allocation / len(defensive_sectors)
            for ticker in defensive_sectors:
                portfolio[ticker] = sector_weight

        return portfolio

    elif mode in ['tiered_extreme', 'tiered_high']:
        # Tiered mode
        if mode == 'tiered_extreme':
            # Extreme vol: 100% T-Bills
            return defensive_allocation.get('allocation', {})
        else:
            # High vol: Defensive sectors ranked by RS
            return select_defensive_portfolio(
                {
                    'mode': 'defensive_sectors',
                    'tickers': defensive_allocation['tickers']
                },
                signals,
                date,
                top_n,
            )

    return {}


def select_portfolio(
    qualifying_etfs: pd.DataFrame,
    top_n: int,
    spy_ticker: str,
) -> Dict[str, float]:
    """
    Select top N ETFs and calculate allocation weights.

    Args:
        qualifying_etfs: DataFrame of ETFs that pass both filters, sorted by RS ROC
        top_n: Number of ETFs to hold
        spy_ticker: Benchmark ticker (SPY)

    Returns:
        Dictionary mapping ticker to allocation weight (as decimal, e.g., 0.20 for 20%)
    """
    portfolio = {}

    if len(qualifying_etfs) >= top_n:
        # Full allocation to top N ETFs
        selected = qualifying_etfs.head(top_n)
        weight = 1.0 / top_n
        for ticker in selected['ticker']:
            portfolio[ticker] = weight
    elif len(qualifying_etfs) > 0:
        # Partial allocation to qualifying ETFs + remainder to SPY
        n_selected = len(qualifying_etfs)
        weight = 1.0 / top_n  # Equal weight per position
        etf_allocation = weight * n_selected
        spy_allocation = 1.0 - etf_allocation

        for ticker in qualifying_etfs['ticker']:
            portfolio[ticker] = weight

        portfolio[spy_ticker] = spy_allocation
    else:
        # No qualifying ETFs - 100% to SPY
        portfolio[spy_ticker] = 1.0

    return portfolio


def run_backtest(
    signals: Dict[str, pd.DataFrame],
    price_data: pd.DataFrame,
    spy_ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    top_n: int,
    regime_detector: Optional[any] = None,
    rebalance_frequency: str = "monthly",
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
    """
    Run the full backtest simulation with configurable rebalancing frequency.

    Args:
        signals: Dictionary of signals DataFrames for each ETF
        price_data: DataFrame with dates as index and tickers as columns
        spy_ticker: Benchmark ticker (SPY)
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_capital: Starting capital
        top_n: Number of ETFs to hold (default, overridden by regime if detector provided)
        regime_detector: Optional VolatilityRegime instance for regime-based adjustments
        rebalance_frequency: "weekly" or "monthly" (default: "monthly")

    Returns:
        Tuple of:
        - strategy_returns: DataFrame with daily portfolio values
        - benchmark_returns: DataFrame with daily SPY buy-and-hold values
        - rebalance_log: List of dicts with rebalance details
    """
    # Get rebalance dates
    rebalance_dates = get_rebalance_dates(price_data, start_date, end_date, rebalance_frequency)

    # Get all trading dates in backtest period
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    trading_dates = price_data.index[mask]

    # Initialize tracking
    portfolio_value = pd.Series(index=trading_dates, dtype=float)
    portfolio_value.iloc[0] = initial_capital

    current_holdings = {}  # {ticker: weight}
    rebalance_log = []

    # Benchmark: SPY buy-and-hold
    spy_prices = price_data[spy_ticker]
    spy_start_price = spy_prices.loc[trading_dates[0]]
    spy_shares = initial_capital / spy_start_price
    benchmark_value = spy_prices.loc[trading_dates] * spy_shares

    # Track current rebalance index
    next_rebalance_idx = 0
    next_rebalance_date = rebalance_dates[next_rebalance_idx]

    # Iterate through each trading day
    for i, date in enumerate(trading_dates):
        # Check if it's a rebalance date
        if date >= next_rebalance_date:
            # Determine parameters based on regime (if enabled)
            active_top_n = top_n
            regime_info = None

            if regime_detector is not None:
                # Detect volatility regime
                spy_prices_series = price_data[spy_ticker]

                # Check if VIX is available and needed
                vix_prices = None
                if regime_detector.use_vix and '^VIX' in price_data.columns:
                    vix_prices = price_data['^VIX']

                regime = regime_detector.detect_regime(spy_prices_series, date, vix_prices)
                regime_params = regime_detector.get_regime_parameters(regime)
                active_top_n = regime_params['top_n']
                regime_info = regime_params['regime']

                logger.info(f"{date.date()}: Regime={regime_info}, Top N={active_top_n}")

            # Get qualifying ETFs
            qualifying = get_qualifying_etfs(signals, date)

            # Check for defensive portfolio override
            defensive_allocation = None
            if regime_detector is not None:
                spy_prices_series = price_data[spy_ticker]
                defensive_allocation = regime_detector.get_defensive_portfolio_allocation(
                    regime, qualifying, spy_prices_series, date
                )

            # Select portfolio
            if defensive_allocation is not None:
                # Use defensive allocation strategy
                new_holdings = select_defensive_portfolio(
                    defensive_allocation, signals, date, top_n=3
                )
                logger.info(f"  Using defensive allocation: {defensive_allocation.get('mode')}")
            else:
                # Normal portfolio selection with regime-adjusted top_n
                new_holdings = select_portfolio(qualifying, active_top_n, spy_ticker)

                # Adjust portfolio for regime constraints (e.g., min SPY allocation)
                if regime_detector is not None:
                    new_holdings = regime_detector.adjust_portfolio_for_regime(
                        new_holdings, regime_params, spy_ticker
                    )

            # Log rebalance
            rebalance_info = {
                'date': date,
                'qualifying_count': len(qualifying),
                'selected': list(new_holdings.keys()),
                'weights': new_holdings.copy(),
                'qualifying_etfs': qualifying.to_dict('records') if not qualifying.empty else [],
                'regime': regime_info,
                'top_n_used': active_top_n,
            }
            rebalance_log.append(rebalance_info)

            logger.info(f"Rebalance on {date.date()}: {len(new_holdings)} positions")

            # Update holdings
            current_holdings = new_holdings

            # Move to next rebalance date
            next_rebalance_idx += 1
            if next_rebalance_idx < len(rebalance_dates):
                next_rebalance_date = rebalance_dates[next_rebalance_idx]
            else:
                next_rebalance_date = pd.Timestamp.max

        # Calculate portfolio value based on current holdings
        if i == 0:
            # First day - already set to initial capital
            continue

        # Calculate return since previous day
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

        # Update portfolio value
        portfolio_value.loc[date] = portfolio_value.loc[prev_date] * (1 + portfolio_return)

    # Create results DataFrames
    strategy_df = pd.DataFrame({
        'date': portfolio_value.index,
        'portfolio_value': portfolio_value.values,
    }).set_index('date')

    benchmark_df = pd.DataFrame({
        'date': benchmark_value.index,
        'portfolio_value': benchmark_value.values,
    }).set_index('date')

    logger.info(f"Backtest complete. Final portfolio value: ${portfolio_value.iloc[-1]:,.2f}")
    logger.info(f"Benchmark final value: ${benchmark_value.iloc[-1]:,.2f}")

    return strategy_df, benchmark_df, rebalance_log

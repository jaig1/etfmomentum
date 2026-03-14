"""Portfolio simulation and backtesting engine."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import logging

from .rs_engine import get_qualifying_etfs

logger = logging.getLogger(__name__)


def get_rebalance_dates(
    price_data: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> List[pd.Timestamp]:
    """
    Identify the first trading day of each month within the backtest period.

    Args:
        price_data: DataFrame with dates as index
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)

    Returns:
        List of rebalance dates (first trading day of each month)
    """
    # Filter to backtest period
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    backtest_dates = price_data.index[mask]

    if len(backtest_dates) == 0:
        raise ValueError(f"No trading dates found between {start_date} and {end_date}")

    # Group by year-month and get first date in each group
    rebalance_dates = []
    current_month = None

    for date in backtest_dates:
        year_month = (date.year, date.month)
        if year_month != current_month:
            rebalance_dates.append(date)
            current_month = year_month

    logger.info(f"Found {len(rebalance_dates)} rebalance dates")
    return rebalance_dates


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
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
    """
    Run the full backtest simulation with monthly rebalancing.

    Args:
        signals: Dictionary of signals DataFrames for each ETF
        price_data: DataFrame with dates as index and tickers as columns
        spy_ticker: Benchmark ticker (SPY)
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_capital: Starting capital
        top_n: Number of ETFs to hold

    Returns:
        Tuple of:
        - strategy_returns: DataFrame with daily portfolio values
        - benchmark_returns: DataFrame with daily SPY buy-and-hold values
        - rebalance_log: List of dicts with rebalance details
    """
    # Get rebalance dates
    rebalance_dates = get_rebalance_dates(price_data, start_date, end_date)

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
            # Get qualifying ETFs
            qualifying = get_qualifying_etfs(signals, date)

            # Select portfolio
            new_holdings = select_portfolio(qualifying, top_n, spy_ticker)

            # Log rebalance
            rebalance_info = {
                'date': date,
                'qualifying_count': len(qualifying),
                'selected': list(new_holdings.keys()),
                'weights': new_holdings.copy(),
                'qualifying_etfs': qualifying.to_dict('records') if not qualifying.empty else [],
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

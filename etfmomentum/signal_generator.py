"""Signal generation for live monthly recommendations."""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

from .rs_engine import generate_signals, get_qualifying_etfs

logger = logging.getLogger(__name__)


def get_latest_trading_date(price_data: pd.DataFrame) -> pd.Timestamp:
    """
    Get the most recent trading date from price data.

    Args:
        price_data: DataFrame with dates as index

    Returns:
        Latest trading date
    """
    return price_data.index[-1]


def calculate_signal_data_dates(lookback_days: int = 250) -> Tuple[str, str]:
    """
    Calculate start and end dates for signal data fetching.

    Args:
        lookback_days: Number of days to look back (for SMA calculation)

    Returns:
        Tuple of (start_date, end_date) as strings
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days + 100)  # Extra buffer for weekends/holidays

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def generate_current_signals(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    spy_ticker: str,
    sma_window: int,
    roc_lookback: int,
) -> Tuple[Dict, pd.Timestamp]:
    """
    Generate signals for the current/latest trading date.

    Args:
        price_data: DataFrame with historical price data
        etf_tickers: List of ETF tickers to analyze
        spy_ticker: Benchmark ticker
        sma_window: SMA lookback window
        roc_lookback: RS ROC lookback period

    Returns:
        Tuple of (signals dict, latest_date)
    """
    # Generate signals for all dates
    signals = generate_signals(
        price_data=price_data,
        spy_ticker=spy_ticker,
        etf_tickers=etf_tickers,
        sma_window=sma_window,
        roc_lookback=roc_lookback,
    )

    # Get latest trading date
    latest_date = get_latest_trading_date(price_data)

    logger.info(f"Generated signals for latest date: {latest_date.date()}")

    return signals, latest_date


def select_current_portfolio(
    signals: Dict[str, pd.DataFrame],
    latest_date: pd.Timestamp,
    top_n: int,
    spy_ticker: str,
) -> Dict:
    """
    Select current portfolio based on latest signals.

    Args:
        signals: Dictionary of signals DataFrames
        latest_date: Latest trading date
        top_n: Number of top ETFs to select
        spy_ticker: Benchmark ticker

    Returns:
        Dictionary with portfolio recommendations
    """
    # Get qualifying ETFs for latest date
    qualifying = get_qualifying_etfs(signals, latest_date)

    # Determine portfolio allocation
    portfolio = {
        'date': latest_date,
        'selected_etfs': [],
        'weights': {},
        'spy_allocation': 0.0,
        'qualifying_count': len(qualifying),
    }

    if len(qualifying) >= top_n:
        # Full allocation to top N ETFs
        selected = qualifying.head(top_n)
        weight = 1.0 / top_n

        for _, row in selected.iterrows():
            ticker = row['ticker']
            portfolio['selected_etfs'].append({
                'ticker': ticker,
                'rank': int(row['rank']),
                'rs_roc': row['rs_roc'],
                'rs_ratio': row['rs_ratio'],
                'weight': weight,
            })
            portfolio['weights'][ticker] = weight

    elif len(qualifying) > 0:
        # Partial allocation to qualifying ETFs + SPY
        weight = 1.0 / top_n
        etf_allocation = weight * len(qualifying)
        spy_allocation = 1.0 - etf_allocation

        for _, row in qualifying.iterrows():
            ticker = row['ticker']
            portfolio['selected_etfs'].append({
                'ticker': ticker,
                'rank': int(row['rank']),
                'rs_roc': row['rs_roc'],
                'rs_ratio': row['rs_ratio'],
                'weight': weight,
            })
            portfolio['weights'][ticker] = weight

        portfolio['spy_allocation'] = spy_allocation
        portfolio['weights'][spy_ticker] = spy_allocation

    else:
        # No qualifying ETFs - 100% SPY
        portfolio['spy_allocation'] = 1.0
        portfolio['weights'][spy_ticker] = 1.0

    logger.info(f"Selected {len(portfolio['selected_etfs'])} ETFs for current month")

    return portfolio


def get_all_etf_current_status(
    signals: Dict[str, pd.DataFrame],
    latest_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Get current status of all ETFs for detailed reporting.

    Args:
        signals: Dictionary of signals DataFrames
        latest_date: Latest trading date

    Returns:
        DataFrame with all ETF status
    """
    from .rs_engine import get_all_etf_status

    status = get_all_etf_status(signals, latest_date)

    # Sort by rank (nulls last)
    status = status.sort_values('rank', na_position='last')

    return status

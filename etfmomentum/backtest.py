"""Portfolio simulation and backtesting engine."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

from .signal_generator import _run_signals_with_data
from .rs_engine import calculate_sector_breadth

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
                        'momentum_quality': row.get('momentum_quality', 0),
                    })

        # Sort by momentum quality (risk-adjusted momentum)
        defensive_rs = sorted(defensive_rs, key=lambda x: x['momentum_quality'], reverse=True)

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
    universe: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    top_n: int,
    rebalance_frequency: str = "monthly",
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
    """
    Run the full backtest simulation.

    Fetches price data from FMP for portfolio valuation. On each rebalance
    date, delegates to run_signals() for ticker selection. Tracks daily
    portfolio value using the fetched price data.

    Args:
        universe: ETF universe name ('sp500', 'developed', 'emerging')
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_capital: Starting capital
        top_n: Number of ETFs to hold
        rebalance_frequency: "weekly" or "monthly"

    Returns:
        Tuple of:
        - strategy_df: DataFrame with daily portfolio values
        - benchmark_df: DataFrame with daily SPY buy-and-hold values
        - rebalance_log: List of dicts with rebalance details
    """
    from . import config
    from .etf_loader import load_universe_by_name
    from .data_fetcher import fetch_all_data

    # Load universe to know which tickers to fetch for portfolio valuation
    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    all_tickers = list(etf_universe.keys()) + [config.BENCHMARK_TICKER, config.CASH_TICKER]

    # Fetch price data from FMP for portfolio valuation
    logger.info("Fetching price data for portfolio valuation...")
    price_data = fetch_all_data(
        ticker_list=all_tickers,
        start_date=config.DATA_START_DATE,
        end_date=end_date,
        api_key=config.FMP_API_KEY,
        api_delay=config.FMP_API_DELAY,
    )

    # Get rebalance dates
    rebalance_dates = get_rebalance_dates(price_data, start_date, end_date, rebalance_frequency)

    # Get all trading dates in backtest period
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    trading_dates = price_data.index[mask]

    # Initialize tracking
    portfolio_value = pd.Series(index=trading_dates, dtype=float)
    portfolio_value.iloc[0] = initial_capital

    current_holdings = {}
    stop_levels = {}  # {ticker: stop_price} — 95% of entry price at rebalance
    rebalance_log = []

    # Benchmark: SPY buy-and-hold
    spy_prices = price_data[config.BENCHMARK_TICKER]
    spy_start_price = spy_prices.loc[trading_dates[0]]
    spy_shares = initial_capital / spy_start_price
    benchmark_value = spy_prices.loc[trading_dates] * spy_shares

    next_rebalance_idx = 0
    next_rebalance_date = rebalance_dates[next_rebalance_idx]

    for i, date in enumerate(trading_dates):
        # On rebalance dates, delegate to signals module for ticker selection
        if date >= next_rebalance_date:
            # Breadth filter: reduce concentration when broad participation is collapsing
            effective_top_n = top_n
            if config.ENABLE_BREADTH_FILTER:
                price_slice = price_data[price_data.index <= date]
                breadth = calculate_sector_breadth(price_slice, list(etf_universe.keys()), config.SMA_LOOKBACK_DAYS)
                if breadth < config.BREADTH_FILTER_THRESHOLD:
                    effective_top_n = config.BREADTH_TOP_N_OVERRIDE
                    logger.info(f"Breadth filter triggered on {date.date()}: {breadth:.1%} of sectors above SMA → top_n reduced to {effective_top_n}")

            selected_tickers = _run_signals_with_data(universe=universe, price_data=price_data, date=date, top_n=effective_top_n)
            weight = 1.0 / len(selected_tickers)
            new_holdings = {ticker: weight for ticker in selected_tickers}

            # Set stop levels at 95% of entry price for each holding
            stop_levels = {}
            for ticker in new_holdings:
                if ticker in price_data.columns and pd.notna(price_data.loc[date, ticker]):
                    stop_levels[ticker] = price_data.loc[date, ticker] * config.STOP_LOSS_THRESHOLD

            rebalance_log.append({
                'date': date,
                'selected': list(new_holdings.keys()),
                'weights': new_holdings.copy(),
                'qualifying_count': len(selected_tickers),
                'qualifying_etfs': [],
                'regime': None,
                'top_n_used': top_n,
            })

            logger.info(f"Rebalance on {date.date()}: {selected_tickers}")
            current_holdings = new_holdings

            next_rebalance_idx += 1
            if next_rebalance_idx < len(rebalance_dates):
                next_rebalance_date = rebalance_dates[next_rebalance_idx]
            else:
                next_rebalance_date = pd.Timestamp.max

        if i == 0:
            continue

        # Check stop orders before calculating daily return
        stopped_out = []
        for ticker in list(current_holdings.keys()):
            if ticker == config.CASH_TICKER:
                continue  # SGOV is the safe haven, no stop needed
            if ticker in stop_levels and ticker in price_data.columns:
                curr_price = price_data.loc[date, ticker]
                if pd.notna(curr_price) and curr_price < stop_levels[ticker]:
                    stopped_out.append(ticker)
                    logger.info(f"Stop triggered on {date.date()}: {ticker} @ {curr_price:.2f} < stop {stop_levels[ticker]:.2f}")

        # Move stopped-out positions to SGOV
        if stopped_out:
            stopped_weight = sum(current_holdings.pop(ticker) for ticker in stopped_out)
            del_stops = [stop_levels.pop(ticker, None) for ticker in stopped_out]  # noqa
            current_holdings[config.CASH_TICKER] = current_holdings.get(config.CASH_TICKER, 0.0) + stopped_weight

        # Calculate daily portfolio return using valuation price data
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

"""Signal generation for live monthly recommendations."""

import pandas as pd
from typing import Dict, List, Optional, Tuple
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


def calculate_signal_data_dates(
    lookback_days: int = 250,
    end_date: Optional[datetime] = None,
) -> Tuple[str, str]:
    """
    Calculate start and end dates for signal data fetching.

    Args:
        lookback_days: Number of days to look back (for SMA calculation)
        end_date: End date to fetch up to (None = today)

    Returns:
        Tuple of (start_date, end_date) as strings
    """
    if end_date is None:
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


def _compute_tickers(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    evaluation_date: pd.Timestamp,
    top_n: int,
) -> List[str]:
    """
    Core signal selection logic — shared by both public and internal interfaces.

    Runs momentum signals, applies SPY fallback, and replaces underperformers
    with SGOV. Not intended for direct external use.

    Args:
        price_data: Price DataFrame containing ETF, SPY and SGOV columns
        etf_tickers: List of ETF tickers to evaluate
        evaluation_date: Date to evaluate signals on
        top_n: Number of top ETFs to select

    Returns:
        List of selected tickers with SGOV replacing any underperformers
    """
    from . import config
    from .rs_engine import get_qualifying_etfs

    signals, latest_date = generate_current_signals(
        price_data=price_data,
        etf_tickers=etf_tickers,
        spy_ticker=config.BENCHMARK_TICKER,
        sma_window=config.SMA_LOOKBACK_DAYS,
        roc_lookback=config.RS_ROC_LOOKBACK_DAYS,
    )

    qualifying = get_qualifying_etfs(signals, evaluation_date)
    selected = list(qualifying.head(top_n)['ticker']) if not qualifying.empty else []

    if len(selected) < top_n:
        selected.append(config.BENCHMARK_TICKER)

    # SGOV comparison — replace underperformers with SGOV, then deduplicate
    sgov_roc = None
    if config.CASH_TICKER in price_data.columns:
        sgov_prices = price_data[config.CASH_TICKER]
        if evaluation_date in sgov_prices.index:
            sgov_roc = sgov_prices.pct_change(periods=config.RS_ROC_LOOKBACK_DAYS).loc[evaluation_date]

    if sgov_roc is not None and not pd.isna(sgov_roc):
        final = []
        for ticker in selected:
            if ticker in price_data.columns and evaluation_date in price_data.index:
                ticker_roc = price_data[ticker].pct_change(periods=config.RS_ROC_LOOKBACK_DAYS).loc[evaluation_date]
                if not pd.isna(ticker_roc) and ticker_roc < sgov_roc:
                    ticker = config.CASH_TICKER
            final.append(ticker)
        seen = set()
        selected = [t for t in final if not (t in seen or seen.add(t))]

    return selected


def run_signals(
    universe: str,
    date: Optional[pd.Timestamp] = None,
    top_n: Optional[int] = None,
) -> List[str]:
    """
    Public interface for live signal generation.

    Always fetches fresh price data from FMP — no caching. Intended for
    third-party use. For backtest use, call _run_signals_with_data instead.

    Args:
        universe: ETF universe name ('sp500', 'developed', 'emerging')
        date: Date to evaluate signals (None = today)
        top_n: Number of top ETFs to select (None = use config.TOP_N_HOLDINGS)

    Returns:
        List of selected ETF tickers, with SGOV replacing any underperformers
    """
    from . import config
    from .etf_loader import load_universe_by_name
    from .data_fetcher import fetch_all_data

    if top_n is None:
        top_n = config.TOP_N_HOLDINGS

    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())
    all_tickers = etf_tickers + [config.BENCHMARK_TICKER, config.CASH_TICKER]

    end_dt = date.to_pydatetime() if date is not None else None
    start_date_str, end_date_str = calculate_signal_data_dates(
        config.SIGNAL_DATA_LOOKBACK_DAYS, end_date=end_dt
    )

    price_data = fetch_all_data(
        ticker_list=all_tickers,
        start_date=start_date_str,
        end_date=end_date_str,
        api_key=config.FMP_API_KEY,
        api_delay=config.FMP_API_DELAY,
    )

    evaluation_date = date if date is not None else price_data.index[-1]
    return _compute_tickers(price_data, etf_tickers, evaluation_date, top_n)


def _run_signals_with_data(
    universe: str,
    price_data: pd.DataFrame,
    date: pd.Timestamp,
    top_n: Optional[int] = None,
) -> List[str]:
    """
    Internal interface for backtest use only. Not exported publicly.

    Uses pre-fetched price data instead of calling FMP, slicing it to the
    given date to avoid lookahead bias. Runs the same signal logic as
    run_signals.

    Args:
        universe: ETF universe name ('sp500', 'developed', 'emerging')
        price_data: Full pre-fetched price DataFrame from the backtest
        date: Rebalance date to evaluate signals on
        top_n: Number of top ETFs to select (None = use config.TOP_N_HOLDINGS)

    Returns:
        List of selected ETF tickers, with SGOV replacing any underperformers
    """
    from . import config
    from .etf_loader import load_universe_by_name

    if top_n is None:
        top_n = config.TOP_N_HOLDINGS

    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())

    # Slice to rebalance date to avoid lookahead bias
    price_data_slice = price_data[price_data.index <= date]

    return _compute_tickers(price_data_slice, etf_tickers, date, top_n)


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

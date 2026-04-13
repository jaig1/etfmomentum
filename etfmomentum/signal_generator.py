"""Signal generation for live monthly recommendations."""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .rs_engine import generate_signals, get_qualifying_etfs, apply_correlation_filter, calculate_sector_breadth

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
                'momentum_quality': row['momentum_quality'],
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
                'momentum_quality': row['momentum_quality'],
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
    universe: str = "sp500",
) -> List[str]:
    """
    Core signal selection logic — shared by both public and internal interfaces.

    Applies breadth filter, correlation filter, SPY fallback, and replaces
    underperformers with SGOV. Not intended for direct external use.

    Args:
        price_data: Price DataFrame containing ETF, SPY and SGOV columns
        etf_tickers: List of ETF tickers to evaluate
        evaluation_date: Date to evaluate signals on
        top_n: Number of top ETFs to select
        universe: Universe name used to resolve per-universe optimal parameters

    Returns:
        List of selected tickers with SGOV replacing any underperformers
    """
    from . import config

    params = config.UNIVERSE_PARAMS.get(universe, config.UNIVERSE_PARAMS["sp500"])

    # Breadth filter — check before running signals; same logic for live and backtest
    effective_top_n = top_n
    cash_prefix: List[str] = []
    if config.ENABLE_BREADTH_FILTER:
        breadth = calculate_sector_breadth(price_data, etf_tickers, params["sma_lookback_days"])
        if breadth < config.BREADTH_FILTER_THRESHOLD:
            logger.info(f"Breadth filter triggered on {evaluation_date.date()}: {breadth:.1%} of sectors above SMA (cash={config.BREADTH_CASH_ALLOCATION:.0%})")
            if config.BREADTH_CASH_ALLOCATION == 1.0:
                return [config.CASH_TICKER]
            elif config.BREADTH_CASH_ALLOCATION == 0.5:
                effective_top_n = 1
                cash_prefix = [config.CASH_TICKER]
            else:
                effective_top_n = config.BREADTH_TOP_N_OVERRIDE

    signals, latest_date = generate_current_signals(
        price_data=price_data,
        etf_tickers=etf_tickers,
        spy_ticker=config.BENCHMARK_TICKER,
        sma_window=params["sma_lookback_days"],
        roc_lookback=params["roc_lookback_days"],
    )

    qualifying = get_qualifying_etfs(signals, evaluation_date)

    if config.ENABLE_CORRELATION_FILTER and not qualifying.empty:
        qualifying = apply_correlation_filter(
            qualifying,
            price_data,
            effective_top_n,
            config.CORRELATION_LOOKBACK_DAYS,
            config.CORRELATION_FILTER_THRESHOLD,
        )

    selected = list(qualifying.head(effective_top_n)['ticker']) if not qualifying.empty else []

    if len(selected) < effective_top_n:
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
        seen: set = set()
        selected = [t for t in final if not (t in seen or seen.add(t))]

    if cash_prefix:
        selected = cash_prefix + [t for t in selected if t != config.CASH_TICKER]

    return selected


def build_portfolio_from_tickers(
    selected_tickers: List[str],
    signals: Dict[str, pd.DataFrame],
    latest_date: pd.Timestamp,
    top_n: int,
) -> Dict:
    """
    Build portfolio dict (for CLI reporting) from a list of selected tickers.

    Looks up metadata (rank, rs_roc, momentum_quality) from signals for ETFs
    that qualified. SGOV and SPY holdings get None metadata and are tracked
    via cash_allocation / spy_allocation.

    Args:
        selected_tickers: Tickers returned by _compute_tickers
        signals: Signals dict from generate_current_signals
        latest_date: Evaluation date
        top_n: Originally requested number of holdings

    Returns:
        Portfolio dict compatible with signal reporting functions
    """
    from . import config

    qualifying = get_qualifying_etfs(signals, latest_date)
    qualifying_map = (
        {row['ticker']: row for _, row in qualifying.iterrows()}
        if not qualifying.empty
        else {}
    )

    weight = 1.0 / len(selected_tickers) if selected_tickers else 0.0

    portfolio: Dict = {
        'date': latest_date,
        'selected_etfs': [],
        'weights': {},
        'spy_allocation': 0.0,
        'cash_allocation': 0.0,
        'qualifying_count': len(qualifying),
    }

    for ticker in selected_tickers:
        portfolio['weights'][ticker] = weight
        if ticker == config.BENCHMARK_TICKER:
            portfolio['spy_allocation'] += weight
        elif ticker == config.CASH_TICKER:
            portfolio['cash_allocation'] += weight
        else:
            etf_entry: Dict = {
                'ticker': ticker,
                'rank': '-',
                'rs_roc': None,
                'momentum_quality': None,
                'rs_ratio': None,
                'weight': weight,
            }
            if ticker in qualifying_map:
                row = qualifying_map[ticker]
                etf_entry['rank'] = int(row['rank'])
                etf_entry['rs_roc'] = row['rs_roc']
                etf_entry['momentum_quality'] = row['momentum_quality']
                etf_entry['rs_ratio'] = row['rs_ratio']
            portfolio['selected_etfs'].append(etf_entry)

    return portfolio


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
        universe: ETF universe name ('sp500', 'developed', 'emerging', 'commodity')
        date: Date to evaluate signals (None = today)
        top_n: Number of top ETFs to select (None = use config.TOP_N_HOLDINGS)

    Returns:
        List of selected ETF tickers, with SGOV replacing any underperformers
    """
    from . import config
    from .etf_loader import load_universe_by_name
    from .data_fetcher import fetch_all_data

    params = config.UNIVERSE_PARAMS.get(universe, config.UNIVERSE_PARAMS["sp500"])
    if top_n is None:
        top_n = params["top_n"]

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
    return _compute_tickers(price_data, etf_tickers, evaluation_date, top_n, universe)


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

    params = config.UNIVERSE_PARAMS.get(universe, config.UNIVERSE_PARAMS["sp500"])
    if top_n is None:
        top_n = params["top_n"]

    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())

    # Slice to rebalance date to avoid lookahead bias
    price_data_slice = price_data[price_data.index <= date]

    return _compute_tickers(price_data_slice, etf_tickers, date, top_n, universe)


def run_short_signals(universe: str) -> List[str]:
    """
    Public interface for live short signal generation.

    Returns tickers to short for the given universe. Only universes listed in
    config.SHORT_ENABLED_UNIVERSES return candidates — all others return [].
    Returns [] when the breadth filter is triggered (defensive mode).

    Internally fetches fresh FMP price data and excludes any ticker already
    selected by the long signal pipeline to avoid long/short conflicts.

    Args:
        universe: ETF universe name ('emerging', 'sp500', etc.)

    Returns:
        List of tickers to short. Empty list if universe not enabled,
        master switch off, or breadth filter triggered.
    """
    from . import config
    from .etf_loader import load_universe_by_name
    from .data_fetcher import fetch_all_data
    from .rs_engine import get_short_candidates, calculate_sector_breadth

    if not config.ENABLE_SHORT_SELLING:
        return []
    if universe not in config.SHORT_ENABLED_UNIVERSES:
        return []

    long_params  = config.UNIVERSE_PARAMS.get(universe, config.UNIVERSE_PARAMS['sp500'])
    short_params = config.SHORT_UNIVERSE_PARAMS[universe]  # guaranteed present — checked above

    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())
    all_tickers = etf_tickers + [config.BENCHMARK_TICKER, config.CASH_TICKER]

    start_date_str, end_date_str = calculate_signal_data_dates(config.SIGNAL_DATA_LOOKBACK_DAYS)
    price_data = fetch_all_data(
        ticker_list=all_tickers,
        start_date=start_date_str,
        end_date=end_date_str,
        api_key=config.FMP_API_KEY,
        api_delay=config.FMP_API_DELAY,
    )

    evaluation_date = price_data.index[-1]

    # Breadth check — return [] when market is in defensive mode
    breadth = calculate_sector_breadth(price_data, etf_tickers, long_params['sma_lookback_days'])
    if config.ENABLE_BREADTH_FILTER and breadth < config.BREADTH_FILTER_THRESHOLD:
        logger.info(f"run_short_signals({universe}): breadth filter triggered ({breadth:.1%}) — returning []")
        return []

    # Get current long tickers to exclude from short candidates
    long_tickers = _compute_tickers(price_data, etf_tickers, evaluation_date, long_params['top_n'], universe)

    # Generate signals and select short candidates using per-universe short params
    signals, _ = generate_current_signals(
        price_data=price_data,
        etf_tickers=etf_tickers,
        spy_ticker=config.BENCHMARK_TICKER,
        sma_window=long_params['sma_lookback_days'],
        roc_lookback=long_params['roc_lookback_days'],
    )

    candidates = get_short_candidates(
        signals,
        evaluation_date,
        short_params['top_n'],
        exclude_tickers=long_tickers,
        qualification=short_params['qualification'],
    )

    return list(candidates['ticker']) if not candidates.empty else []


def _run_short_signals_with_data(
    universe: str,
    price_data: pd.DataFrame,
    date: pd.Timestamp,
    long_tickers: List[str],
    n: Optional[int] = None,
) -> List[str]:
    """
    Internal interface for short candidate selection in backtest.

    Mirrors _run_signals_with_data but returns the bottom N ETFs that fail
    both filters, sorted by momentum_quality ascending (worst trend first).
    Excludes any ticker already held long to avoid conflicts.

    Args:
        universe: ETF universe name
        price_data: Full pre-fetched price DataFrame from the backtest
        date: Rebalance date to evaluate signals on
        long_tickers: Tickers currently held long — excluded from short candidates
        n: Number of short candidates (None = use SHORT_UNIVERSE_PARAMS[universe]['top_n'])

    Returns:
        List of tickers to short (0 to n tickers)
    """
    from . import config
    from .etf_loader import load_universe_by_name
    from .rs_engine import get_short_candidates

    long_params  = config.UNIVERSE_PARAMS.get(universe, config.UNIVERSE_PARAMS["sp500"])
    short_params = config.SHORT_UNIVERSE_PARAMS.get(universe, {})

    if n is None:
        n = short_params.get('top_n', 2)

    etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
    etf_tickers = list(etf_universe.keys())

    # Slice to rebalance date to avoid lookahead bias
    price_data_slice = price_data[price_data.index <= date]

    signals, _ = generate_current_signals(
        price_data=price_data_slice,
        etf_tickers=etf_tickers,
        spy_ticker=config.BENCHMARK_TICKER,
        sma_window=long_params["sma_lookback_days"],
        roc_lookback=long_params["roc_lookback_days"],
    )

    candidates = get_short_candidates(
        signals, date, n,
        exclude_tickers=long_tickers,
        qualification=short_params.get('qualification', 'both_filters'),
    )

    return list(candidates['ticker']) if not candidates.empty else []


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

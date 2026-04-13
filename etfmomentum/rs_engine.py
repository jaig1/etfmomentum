"""Relative Strength calculation and signal generation engine."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_rs_ratio(etf_prices: pd.Series, spy_prices: pd.Series) -> pd.Series:
    """
    Calculate Relative Strength ratio.

    RS Ratio = ETF Price / SPY Price

    Args:
        etf_prices: Series of ETF adjusted close prices
        spy_prices: Series of SPY adjusted close prices

    Returns:
        Series of RS ratio values
    """
    return etf_prices / spy_prices


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """
    Calculate Simple Moving Average.

    Args:
        series: Input price or ratio series
        window: Lookback window in days

    Returns:
        Series of SMA values
    """
    return series.rolling(window=window, min_periods=window).mean()


def apply_rs_filter(rs_ratio: pd.Series, rs_sma: pd.Series) -> pd.Series:
    """
    Apply RS filter: RS Ratio must be above its SMA.

    Args:
        rs_ratio: RS ratio series
        rs_sma: SMA of RS ratio

    Returns:
        Boolean series (True = passes filter)
    """
    return rs_ratio > rs_sma


def apply_absolute_filter(etf_prices: pd.Series, price_sma: pd.Series) -> pd.Series:
    """
    Apply absolute trend filter: ETF price must be above its SMA.

    Args:
        etf_prices: ETF price series
        price_sma: SMA of ETF prices

    Returns:
        Boolean series (True = passes filter)
    """
    return etf_prices > price_sma


def calculate_rs_roc(rs_ratio: pd.Series, lookback: int) -> pd.Series:
    """
    Calculate Rate of Change of RS Ratio.

    RS_ROC = (RS_Ratio_today - RS_Ratio_N_days_ago) / RS_Ratio_N_days_ago

    Args:
        rs_ratio: RS ratio series
        lookback: Lookback period in days

    Returns:
        Series of RS ROC values
    """
    rs_ratio_lagged = rs_ratio.shift(lookback)
    return (rs_ratio - rs_ratio_lagged) / rs_ratio_lagged


def calculate_momentum_quality(rs_ratio: pd.Series, lookback: int) -> pd.Series:
    """
    Calculate Risk-Adjusted Momentum (Information Ratio of the RS trend).

    momentum_quality = RS_ROC(lookback) / StdDev(daily RS ratio returns, lookback)

    Penalizes erratic movers and rewards smooth, persistent trends.
    A sector that gaps up once scores lower than one that trends up steadily.

    Args:
        rs_ratio: RS ratio series (ETF / SPY)
        lookback: Lookback period in days (same window for ROC and std)

    Returns:
        Series of risk-adjusted momentum values
    """
    rs_roc = calculate_rs_roc(rs_ratio, lookback)
    daily_rs_returns = rs_ratio.pct_change()
    rs_std = daily_rs_returns.rolling(window=lookback, min_periods=lookback).std()
    return rs_roc / rs_std


def apply_correlation_filter(
    qualifying_etfs: pd.DataFrame,
    price_data: pd.DataFrame,
    top_n: int,
    lookback: int,
    threshold: float,
) -> pd.DataFrame:
    """
    Greedy correlation-filtered selection from a ranked qualifying list.

    Iterates through ETFs in momentum-quality rank order. Takes the top-ranked
    unconditionally. Skips any subsequent candidate whose rolling daily-return
    correlation exceeds the threshold with *any* already-selected ETF.

    Prevents hidden concentration (e.g. SMH + XLK both in top-3 when they are
    driven by the same mega-cap tech factor).

    Args:
        qualifying_etfs: DataFrame ranked by momentum_quality (descending)
        price_data: Price DataFrame sliced to the evaluation date (no lookahead)
        top_n: Maximum number of ETFs to select
        lookback: Rolling window in days for correlation calculation
        threshold: Correlation threshold above which a candidate is skipped

    Returns:
        Filtered DataFrame with at most top_n rows, index reset.
    """
    selected_rows = []
    selected_tickers = []

    for _, row in qualifying_etfs.iterrows():
        if len(selected_rows) >= top_n:
            break

        ticker = row['ticker']

        if not selected_tickers:
            # Always take the top-ranked ETF unconditionally
            selected_rows.append(row)
            selected_tickers.append(ticker)
            continue

        if ticker not in price_data.columns:
            continue

        candidate_returns = price_data[ticker].pct_change().dropna().tail(lookback)

        too_correlated = False
        for held_ticker in selected_tickers:
            if held_ticker not in price_data.columns:
                continue
            held_returns = price_data[held_ticker].pct_change().dropna().tail(lookback)
            aligned = pd.concat([candidate_returns, held_returns], axis=1).dropna()
            if len(aligned) < lookback // 2:
                continue
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            if not pd.isna(corr) and corr > threshold:
                logger.debug(f"Correlation filter: skipping {ticker} (corr={corr:.2f} with {held_ticker})")
                too_correlated = True
                break

        if not too_correlated:
            selected_rows.append(row)
            selected_tickers.append(ticker)

    if not selected_rows:
        return pd.DataFrame()

    return pd.DataFrame(selected_rows).reset_index(drop=True)


def get_short_candidates(
    signals: Dict[str, pd.DataFrame],
    date: pd.Timestamp,
    n: int = 2,
    exclude_tickers: Optional[List[str]] = None,
    qualification: str = 'both_filters',
) -> pd.DataFrame:
    """
    Get bottom N ETFs ranked by momentum_quality ascending (worst trend first).

    These are short candidates — smooth, persistent downtrends relative to SPY.
    Mirror of get_qualifying_etfs() but inverted.

    Args:
        signals: Dictionary of signals DataFrames for each ETF
        date: Date to evaluate
        n: Maximum number of short candidates to return
        exclude_tickers: Tickers already held long — skipped to avoid conflicts
        qualification: 'both_filters' — must fail both rs_filter and abs_filter;
                       'momentum_quality_only' — bottom N by score regardless of filters

    Returns:
        DataFrame sorted by momentum_quality ascending (worst trend first),
        up to n rows. Empty DataFrame if no candidates qualify.
    """
    if exclude_tickers is None:
        exclude_tickers = []

    candidates = []

    for ticker, df in signals.items():
        if ticker in exclude_tickers:
            continue
        if date not in df.index:
            continue

        row = df.loc[date]

        if pd.isna(row['momentum_quality']):
            continue

        if qualification == 'both_filters':
            qualifies = not row['both_filters']
        else:  # 'momentum_quality_only' — no filter gate, pure signal ranking
            qualifies = True

        if qualifies:
            candidates.append({
                'ticker': ticker,
                'price': row['price'],
                'rs_ratio': row['rs_ratio'],
                'rs_roc': row['rs_roc'],
                'momentum_quality': row['momentum_quality'],
                'rs_filter': row['rs_filter'],
                'abs_filter': row['abs_filter'],
            })

    if not candidates:
        return pd.DataFrame()

    df_candidates = pd.DataFrame(candidates)
    # Ascending sort: most negative momentum quality = smoothest downtrend = best short
    df_candidates = df_candidates.sort_values('momentum_quality', ascending=True).reset_index(drop=True)

    return df_candidates.head(n)


def calculate_sector_breadth(
    price_data: pd.DataFrame,
    etf_tickers: List[str],
    sma_window: int,
) -> float:
    """
    Calculate sector breadth: fraction of ETFs above their SMA.

    Used as a leading defensive indicator. When broad market participation
    is collapsing (few sectors above their long-term trend), concentration
    risk increases significantly.

    Args:
        price_data: Price DataFrame already sliced to the evaluation date
        etf_tickers: Sector ETF tickers to include (exclude SPY, SGOV, BIL)
        sma_window: SMA lookback window in days (matches strategy SMA)

    Returns:
        Fraction of ETFs above their SMA (0.0 to 1.0).
        Returns 1.0 (no filter) when insufficient data is available.
    """
    above = 0
    total = 0

    for ticker in etf_tickers:
        if ticker not in price_data.columns:
            continue
        prices = price_data[ticker].dropna()
        if len(prices) < sma_window:
            continue
        sma = prices.rolling(window=sma_window, min_periods=sma_window).mean().iloc[-1]
        current = prices.iloc[-1]
        if pd.notna(sma) and pd.notna(current):
            total += 1
            if current > sma:
                above += 1

    return above / total if total > 0 else 1.0


def generate_signals(
    price_data: pd.DataFrame,
    spy_ticker: str,
    etf_tickers: List[str],
    sma_window: int,
    roc_lookback: int,
) -> Dict[str, pd.DataFrame]:
    """
    Generate all signals, filters, and rankings for all ETFs.

    Args:
        price_data: DataFrame with dates as index and tickers as columns
        spy_ticker: Benchmark ticker (SPY)
        etf_tickers: List of ETF tickers to analyze
        sma_window: SMA lookback window (e.g., 200 days)
        roc_lookback: RS ROC lookback period (e.g., 21 days)

    Returns:
        Dictionary mapping each ETF ticker to its signals DataFrame with columns:
        - price: ETF adjusted close
        - price_sma: SMA of ETF price
        - rs_ratio: RS ratio vs SPY
        - rs_sma: SMA of RS ratio
        - rs_filter: Boolean (True if RS ratio > RS SMA)
        - abs_filter: Boolean (True if price > price SMA)
        - both_filters: Boolean (True if both filters pass)
        - rs_roc: Rate of change of RS ratio
    """
    if spy_ticker not in price_data.columns:
        raise ValueError(f"Benchmark ticker {spy_ticker} not found in price data")

    spy_prices = price_data[spy_ticker]
    signals = {}

    for ticker in etf_tickers:
        if ticker not in price_data.columns:
            logger.warning(f"Ticker {ticker} not found in price data, skipping")
            continue

        etf_prices = price_data[ticker]

        # Skip if ETF has all NaN values
        if etf_prices.isna().all():
            logger.warning(f"Ticker {ticker} has no valid data, skipping")
            continue

        # Calculate RS ratio
        rs_ratio = calculate_rs_ratio(etf_prices, spy_prices)

        # Calculate SMAs
        price_sma = calculate_sma(etf_prices, sma_window)
        rs_sma = calculate_sma(rs_ratio, sma_window)

        # Apply filters
        rs_filter = apply_rs_filter(rs_ratio, rs_sma)
        abs_filter = apply_absolute_filter(etf_prices, price_sma)
        both_filters = rs_filter & abs_filter

        # Calculate RS ROC and risk-adjusted momentum
        rs_roc = calculate_rs_roc(rs_ratio, roc_lookback)
        momentum_quality = calculate_momentum_quality(rs_ratio, roc_lookback)

        # Combine into DataFrame
        df = pd.DataFrame({
            'price': etf_prices,
            'price_sma': price_sma,
            'rs_ratio': rs_ratio,
            'rs_sma': rs_sma,
            'rs_filter': rs_filter,
            'abs_filter': abs_filter,
            'both_filters': both_filters,
            'rs_roc': rs_roc,
            'momentum_quality': momentum_quality,
        })

        signals[ticker] = df

    logger.info(f"Generated signals for {len(signals)} ETFs")
    return signals


def get_qualifying_etfs(
    signals: Dict[str, pd.DataFrame],
    date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Get all ETFs that pass both filters on a specific date, ranked by RS ROC.

    Args:
        signals: Dictionary of signals DataFrames for each ETF
        date: Date to evaluate

    Returns:
        DataFrame with columns: ticker, price, rs_ratio, rs_roc, rank
        Sorted by rs_roc descending (highest momentum first)
    """
    qualifying = []

    for ticker, df in signals.items():
        if date not in df.index:
            continue

        row = df.loc[date]

        # Check if both filters pass
        if row['both_filters'] and not pd.isna(row['momentum_quality']):
            qualifying.append({
                'ticker': ticker,
                'price': row['price'],
                'price_sma': row['price_sma'],
                'rs_ratio': row['rs_ratio'],
                'rs_sma': row['rs_sma'],
                'rs_filter': row['rs_filter'],
                'abs_filter': row['abs_filter'],
                'rs_roc': row['rs_roc'],
                'momentum_quality': row['momentum_quality'],
            })

    if not qualifying:
        return pd.DataFrame()

    # Create DataFrame and sort by momentum quality descending (smooth trends first)
    df_qualifying = pd.DataFrame(qualifying)
    df_qualifying = df_qualifying.sort_values('momentum_quality', ascending=False).reset_index(drop=True)
    df_qualifying['rank'] = range(1, len(df_qualifying) + 1)

    return df_qualifying


def get_all_etf_status(
    signals: Dict[str, pd.DataFrame],
    date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Get status of all ETFs on a specific date for reporting.

    Args:
        signals: Dictionary of signals DataFrames for each ETF
        date: Date to evaluate

    Returns:
        DataFrame with all ETF metrics and filter status
    """
    status_list = []

    for ticker, df in signals.items():
        if date not in df.index:
            status_list.append({
                'ticker': ticker,
                'price': np.nan,
                'price_sma': np.nan,
                'rs_ratio': np.nan,
                'rs_sma': np.nan,
                'rs_filter': False,
                'abs_filter': False,
                'rs_roc': np.nan,
                'momentum_quality': np.nan,
                'rank': np.nan,
            })
            continue

        row = df.loc[date]

        status_list.append({
            'ticker': ticker,
            'price': row['price'],
            'price_sma': row['price_sma'],
            'rs_ratio': row['rs_ratio'],
            'rs_sma': row['rs_sma'],
            'rs_filter': row['rs_filter'],
            'abs_filter': row['abs_filter'],
            'rs_roc': row['rs_roc'],
            'momentum_quality': row['momentum_quality'],
            'rank': np.nan,  # Will be filled for qualifying ETFs
        })

    df_status = pd.DataFrame(status_list)

    # Calculate ranks for qualifying ETFs
    qualifying = df_status[(df_status['rs_filter']) & (df_status['abs_filter']) & (~df_status['momentum_quality'].isna())]
    if not qualifying.empty:
        qualifying_sorted = qualifying.sort_values('momentum_quality', ascending=False)
        ranks = {ticker: rank for rank, ticker in enumerate(qualifying_sorted['ticker'], 1)}
        df_status['rank'] = df_status['ticker'].map(ranks)

    return df_status

"""Data fetcher module for retrieving historical price data from Financial Modeling Prep API."""

import time
import requests
import pandas as pd
from typing import List, Dict
from datetime import datetime
import logging

from . import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_historical_data(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: str,
) -> pd.DataFrame:
    """
    Fetch historical price data for a single ticker from FMP API.

    Args:
        ticker: Stock/ETF ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: FMP API key

    Returns:
        DataFrame with columns: date, adjusted_close
    """
    url = config.FMP_HISTORICAL_PRICE_ENDPOINT
    params = {
        "symbol": ticker,
        "from": start_date,
        "to": end_date,
        "apikey": api_key,
    }

    try:
        logger.info(f"Fetching data for {ticker}...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Stable endpoint returns a list directly
        if not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No historical data found for {ticker}")
            return pd.DataFrame()

        # Convert list to DataFrame
        df = pd.DataFrame(data)

        # Select and rename columns (stable endpoint uses 'close' instead of 'adjClose')
        if "date" in df.columns and "close" in df.columns:
            df = df[["date", "close"]].copy()
            df.columns = ["date", "adjusted_close"]
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            logger.info(f"Successfully fetched {len(df)} records for {ticker}")
            return df
        else:
            logger.warning(f"Missing required columns for {ticker}")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error for {ticker}: {e}")
        return pd.DataFrame()


def fetch_all_data(
    ticker_list: List[str],
    start_date: str,
    end_date: str,
    api_key: str,
    api_delay: float = 0.5,
) -> pd.DataFrame:
    """
    Fetch historical data for all tickers and combine into a single DataFrame.

    Args:
        ticker_list: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: FMP API key
        api_delay: Delay between API calls in seconds

    Returns:
        DataFrame with dates as index and tickers as columns
    """
    all_data = {}

    for i, ticker in enumerate(ticker_list):
        df = fetch_historical_data(ticker, start_date, end_date, api_key)

        if not df.empty:
            # Set date as index and store the adjusted close series
            df = df.set_index("date")
            all_data[ticker] = df["adjusted_close"]
        else:
            logger.warning(f"Skipping {ticker} due to missing data")

        # Add delay to respect rate limits (except for last ticker)
        if i < len(ticker_list) - 1:
            time.sleep(api_delay)

    if not all_data:
        raise ValueError("No data was successfully fetched for any ticker")

    # Combine all series into a single DataFrame
    combined_df = pd.DataFrame(all_data)
    combined_df.index.name = "date"

    # Sort by date
    combined_df = combined_df.sort_index()

    logger.info(f"Combined data shape: {combined_df.shape}")
    logger.info(f"Date range: {combined_df.index.min()} to {combined_df.index.max()}")

    return combined_df


def save_data_to_cache(df: pd.DataFrame, cache_path: str) -> None:
    """Save DataFrame to CSV cache."""
    df.to_csv(cache_path)
    logger.info(f"Data cached to {cache_path}")


def load_data_from_cache(cache_path: str) -> pd.DataFrame:
    """Load DataFrame from CSV cache."""
    df = pd.read_csv(cache_path, index_col="date", parse_dates=True)
    logger.info(f"Loaded cached data from {cache_path}")
    logger.info(f"Cached data shape: {df.shape}")
    return df


def get_price_data(
    ticker_list: List[str],
    start_date: str,
    end_date: str,
    api_key: str,
    cache_path: str,
    force_refresh: bool = False,
    api_delay: float = 0.5,
) -> pd.DataFrame:
    """
    Get price data either from cache or by fetching from API.

    Args:
        ticker_list: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: FMP API key
        cache_path: Path to cache file
        force_refresh: If True, force re-download from API
        api_delay: Delay between API calls in seconds

    Returns:
        DataFrame with dates as index and tickers as columns
    """
    import os

    # Check if cache exists and we're not forcing refresh
    if os.path.exists(cache_path) and not force_refresh:
        logger.info("Loading data from cache...")
        return load_data_from_cache(cache_path)

    # Fetch fresh data
    logger.info("Fetching fresh data from FMP API...")
    df = fetch_all_data(ticker_list, start_date, end_date, api_key, api_delay)

    # Save to cache
    save_data_to_cache(df, cache_path)

    return df

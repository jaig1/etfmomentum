"""ETF universe loader - reads ETF lists from external CSV files."""

import csv
import requests
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

TOPT_HOLDER_ENDPOINT = "https://financialmodelingprep.com/api/v3/etf-holder/TOPT"


def fetch_topt_holdings(api_key: str, top_n: int = 20) -> Dict[str, str]:
    """
    Fetch live top-N stock holdings from the TOPT ETF via FMP API.

    Deduplicates share-class variants (e.g. GOOGL / GOOG) by CUSIP issuer
    prefix (first 6 chars), keeping the higher-weight class.

    Args:
        api_key: FMP API key
        top_n:   Maximum number of stocks to return (default 20)

    Returns:
        Dict mapping ticker → company name, ordered by weight descending

    Raises:
        RuntimeError: On any API or data error — no fallback
    """
    try:
        response = requests.get(
            TOPT_HOLDER_ENDPOINT,
            params={"apikey": api_key},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch TOPT holdings from FMP API: {e}")

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError(
            "TOPT holdings API returned empty or unexpected response — cannot proceed"
        )

    # Filter out cash/collateral rows (asset field is empty)
    stocks = [row for row in data if row.get("asset", "").strip()]

    if not stocks:
        raise RuntimeError("TOPT holdings API returned no stock entries after filtering cash rows")

    # Sort by weight descending (API usually returns sorted, but enforce it)
    stocks.sort(key=lambda r: r.get("weightPercentage", 0), reverse=True)

    # Deduplicate by CUSIP issuer prefix (first 6 chars) — keeps highest-weight share class
    seen_cusip_prefixes: set = set()
    deduplicated = []
    for row in stocks:
        cusip = row.get("cusip", "").strip()
        prefix = cusip[:6] if len(cusip) >= 6 else None

        if prefix and prefix in seen_cusip_prefixes:
            logger.info(
                f"Skipping {row['asset']} (CUSIP prefix {prefix} already seen — "
                f"share-class duplicate of a higher-weight holding)"
            )
            continue

        if prefix:
            seen_cusip_prefixes.add(prefix)

        deduplicated.append(row)

    top_holdings = deduplicated[:top_n]

    result = {row["asset"]: row["name"].title() for row in top_holdings}
    logger.info(f"Fetched {len(result)} live holdings from TOPT ETF (top_n={top_n})")
    return result


def load_etf_universe(csv_file_path: Path) -> Dict[str, str]:
    """
    Load ETF universe from CSV file.

    Expected CSV format:
        Ticker,ETF_Name,Issuer
        "EWY","South Korea","iShares (BlackRock)"

    Args:
        csv_file_path: Path to CSV file containing ETF list

    Returns:
        Dictionary mapping ticker to ETF name/description

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not csv_file_path.exists():
        raise FileNotFoundError(f"ETF list file not found: {csv_file_path}")

    etf_universe = {}

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            if 'Ticker' not in reader.fieldnames or 'ETF_Name' not in reader.fieldnames:
                raise ValueError(
                    f"Invalid CSV format. Expected columns: Ticker, ETF_Name. "
                    f"Found: {reader.fieldnames}"
                )

            # Read ETFs
            for row in reader:
                ticker = row['Ticker'].strip().strip('"')
                etf_name = row['ETF_Name'].strip().strip('"')

                if ticker and etf_name:
                    etf_universe[ticker] = etf_name

        if not etf_universe:
            raise ValueError(f"No ETFs found in {csv_file_path}")

        logger.info(f"Loaded {len(etf_universe)} ETFs from {csv_file_path.name}")

        return etf_universe

    except csv.Error as e:
        raise ValueError(f"Error parsing CSV file {csv_file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading ETF universe from {csv_file_path}: {e}")


def get_available_universes(etflist_dir: Path) -> Dict[str, str]:
    """
    Get list of available ETF universes.

    Args:
        etflist_dir: Directory containing ETF list CSV files

    Returns:
        Dictionary mapping universe name to file path
    """
    universes = {}

    # Map universe names to expected filenames
    universe_files = {
        'emerging': 'emerging_market_etfs.csv',
        'developed': 'developed_market_etfs.csv',
        'sp500': 'sp500_sector_etfs.csv',
        'commodity': 'commodity_etfs.csv',
        'multi_asset': 'multi_asset_etfs.csv',
        'factor': 'factor_etfs.csv',
        'bond': 'bond_etfs.csv',
        'top20': 'top20_stock.csv',
    }

    for universe_name, filename in universe_files.items():
        file_path = etflist_dir / filename
        if file_path.exists():
            universes[universe_name] = str(file_path)

    return universes


def load_universe_by_name(universe_name: str, etflist_dir: Path, api_key: str = None) -> Dict[str, str]:
    """
    Load ETF universe by name.

    For the 'top20' universe, holdings are fetched live from the TOPT ETF via
    FMP API on every call (always current; raises RuntimeError on failure).
    All other universes are loaded from their static CSV files (backtest-safe).

    Args:
        universe_name: Name of universe (sp500, emerging, developed, commodity,
                       multi_asset, factor, bond, top20)
        etflist_dir:   Directory containing ETF list CSV files
        api_key:       FMP API key — required for top20, ignored for all others

    Returns:
        Dictionary mapping ticker to ETF name

    Raises:
        ValueError:   If universe name is invalid or CSV file not found
        RuntimeError: If top20 live API fetch fails
    """
    universe_files = {
        'emerging': 'emerging_market_etfs.csv',
        'developed': 'developed_market_etfs.csv',
        'sp500': 'sp500_sector_etfs.csv',
        'commodity': 'commodity_etfs.csv',
        'multi_asset': 'multi_asset_etfs.csv',
        'factor': 'factor_etfs.csv',
        'bond': 'bond_etfs.csv',
        'top20': 'top20_stock.csv',
    }

    if universe_name not in universe_files:
        available = ', '.join(universe_files.keys())
        raise ValueError(
            f"Invalid universe '{universe_name}'. "
            f"Available universes: {available}"
        )

    # top20 always uses live TOPT holdings — no CSV fallback
    if universe_name == 'top20':
        if not api_key:
            from . import config
            api_key = config.FMP_API_KEY
        return fetch_topt_holdings(api_key)

    filename = universe_files[universe_name]
    file_path = etflist_dir / filename

    logger.info(f"Loading '{universe_name}' universe from {filename}")

    return load_etf_universe(file_path)

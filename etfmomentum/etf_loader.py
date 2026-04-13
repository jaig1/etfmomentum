"""ETF universe loader - reads ETF lists from external CSV files."""

import csv
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


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
    }

    for universe_name, filename in universe_files.items():
        file_path = etflist_dir / filename
        if file_path.exists():
            universes[universe_name] = str(file_path)

    return universes


def load_universe_by_name(universe_name: str, etflist_dir: Path) -> Dict[str, str]:
    """
    Load ETF universe by name.

    Args:
        universe_name: Name of universe (emerging, developed, sp500, commodity, multi_asset)
        etflist_dir: Directory containing ETF list CSV files

    Returns:
        Dictionary mapping ticker to ETF name

    Raises:
        ValueError: If universe name is invalid or file not found
    """
    # Map universe names to filenames
    universe_files = {
        'emerging': 'emerging_market_etfs.csv',
        'developed': 'developed_market_etfs.csv',
        'sp500': 'sp500_sector_etfs.csv',
        'commodity': 'commodity_etfs.csv',
        'multi_asset': 'multi_asset_etfs.csv',
        'factor': 'factor_etfs.csv',
    }

    if universe_name not in universe_files:
        available = ', '.join(universe_files.keys())
        raise ValueError(
            f"Invalid universe '{universe_name}'. "
            f"Available universes: {available}"
        )

    filename = universe_files[universe_name]
    file_path = etflist_dir / filename

    logger.info(f"Loading '{universe_name}' universe from {filename}")

    return load_etf_universe(file_path)

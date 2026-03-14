"""Configuration file for ETF Relative Strength Backtest."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    raise ValueError("FMP_API_KEY not found in .env file. Please set it up.")

# FMP API Endpoints (using stable endpoints)
FMP_HISTORICAL_PRICE_ENDPOINT = "https://financialmodelingprep.com/stable/historical-price-eod/full"

# Benchmark
BENCHMARK_TICKER = "SPY"

# ETF Universe - Loaded dynamically from external CSV files
# Files location: PROJECT_ROOT/etflist/
# Available universes: emerging, developed, sp500

# Backtest Parameters
BACKTEST_START_DATE = "2016-01-01"
BACKTEST_END_DATE = "2026-03-01"
DATA_START_DATE = "2015-01-01"  # Need historical data for SMA calculation
INITIAL_CAPITAL = 100000.0

# Strategy Parameters
TOP_N_HOLDINGS = 3  # Optimized: 3 holdings outperform 5 (was 5)
REBALANCE_FREQUENCY = "monthly"  # First trading day of each month
SMA_LOOKBACK_DAYS = 210  # 10 months (optimized: was 200)
RS_ROC_LOOKBACK_DAYS = 63  # 3 months (optimized: was 21 for 1 month)
RISK_FREE_RATE = 0.045  # 4.5% annual risk-free rate for Sharpe calculation

# API Settings
FMP_API_DELAY = 0  # No delay needed (3000 calls/min plan)

# Signal Mode Settings
SIGNAL_DATA_LOOKBACK_DAYS = 400  # Days to fetch for signal generation (ensures 200-day SMA)

# Directory Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
ETFLIST_DIR = PROJECT_ROOT / "etflist"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Data Cache File
PRICE_DATA_CACHE = DATA_DIR / "price_data.csv"

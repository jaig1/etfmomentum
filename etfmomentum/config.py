"""Configuration file for ETF Relative Strength Backtest."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    raise ValueError(
        "\n" + "="*70 + "\n"
        "❌ PREREQUISITE ERROR: FMP_API_KEY not found\n"
        "="*70 + "\n"
        "This package requires a Financial Modeling Prep API key.\n\n"
        "To fix this, create a .env file in your project directory:\n\n"
        "  1. Create .env file:\n"
        "     echo 'FMP_API_KEY=your_key_here' > .env\n\n"
        "  2. OR export environment variable:\n"
        "     export FMP_API_KEY='your_key_here'\n\n"
        "Get a free API key at: https://financialmodelingprep.com/developer/docs/\n"
        "="*70
    )

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
REBALANCE_FREQUENCY = "weekly"  # Options: "weekly" (best: 378% return, 0.700 Sharpe) or "monthly" (340% return, 0.649 Sharpe)
SMA_LOOKBACK_DAYS = 210  # 10 months (optimized: was 200)
RS_ROC_LOOKBACK_DAYS = 63  # 3 months (optimized: was 21 for 1 month)
RISK_FREE_RATE = 0.045  # 4.5% annual risk-free rate for Sharpe calculation

# Volatility Regime Switching
ENABLE_VOLATILITY_REGIME_SWITCHING = True  # Toggle feature on/off
USE_VIX_FOR_REGIME = False  # Use VIX ticker (True) or calculate from SPY (False)
VIX_TICKER = "^VIX"  # VIX ticker symbol

# VIX-Based Thresholds (when USE_VIX_FOR_REGIME = True)
VIX_SMOOTHING_DAYS = 5  # Days to average VIX (reduces noise)
VIX_CURRENT_WEIGHT = 0.3  # Weight for current VIX (0.7 for average, 0.3 for current)
VIX_LOW_THRESHOLD = 14  # Below this = LOW regime
VIX_HIGH_ENTER_THRESHOLD = 26  # Above this = enter HIGH regime
VIX_HIGH_EXIT_THRESHOLD = 20  # Below this = exit HIGH regime (hysteresis)
VIX_LOW_EXIT_THRESHOLD = 16  # Above this = exit LOW regime (hysteresis)

# SPY-Based Thresholds (when USE_VIX_FOR_REGIME = False)
VOLATILITY_LOOKBACK_DAYS = 30  # Window for calculating SPY volatility
LOW_VOL_THRESHOLD = 0.10  # Annualized volatility threshold (10%)
HIGH_VOL_THRESHOLD = 0.25  # Annualized volatility threshold (25%)

# Regime-Specific Parameters
LOW_VOL_TOP_N = 3  # Holdings in low volatility regime (aggressive)
MEDIUM_VOL_TOP_N = 3  # Holdings in medium volatility regime (normal)
HIGH_VOL_TOP_N = 5  # Holdings in high volatility regime (defensive)
HIGH_VOL_SPY_MIN_ALLOCATION = 0.20  # Minimum SPY allocation in high vol (20%)

# Defensive Strategy Parameters (for high volatility testing)
HIGH_VOL_DEFENSIVE_SECTORS = ['XLP', 'XLU', 'XLV']  # Staples, Utilities, Healthcare
HIGH_VOL_TBILL_ETF = 'BIL'  # Short-term Treasury ETF (SGOV also works)
HIGH_VOL_TBILL_ALLOCATION = 0.50  # 50% allocation in hybrid mode
EXTREME_VOL_THRESHOLD = 0.35  # 35% annualized volatility for extreme regime

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

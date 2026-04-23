"""Configuration file for ETF Relative Strength Backtest."""

import importlib.resources
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

# Cash equivalent ETF (short-term treasuries)
CASH_TICKER = "SGOV"

# ETF Universe - Loaded dynamically from external CSV files
# Files location: PROJECT_ROOT/etflist/
# Available universes: emerging, developed, sp500

# Per-universe optimised parameters (walk-forward consensus).
# These are the only values third-party callers should rely on — just pass
# the universe name; the package resolves the right parameters automatically.
UNIVERSE_PARAMS = {
    "sp500": {
        "sma_lookback_days": 210,   # 10 months — in-sample optimised
        "roc_lookback_days": 63,    # 3 months  — in-sample optimised
        "top_n": 3,
    },
    "emerging": {
        "sma_lookback_days": 252,   # 12 months — walk-forward consensus (5/6 windows)
        "roc_lookback_days": 21,    # 1 month   — walk-forward consensus
        "top_n": 3,
    },
    "developed": {
        "sma_lookback_days": 168,   # 8 months  — walk-forward consensus (6/6 windows)
        "roc_lookback_days": 21,    # 1 month   — walk-forward consensus
        "top_n": 3,
    },
    "commodity": {
        "sma_lookback_days": 126,   # 6 months  — walk-forward consensus (6/6 windows)
        "roc_lookback_days": 126,   # 6 months  — walk-forward consensus (6/6 windows); ROC=1mo overfits in-sample
        "top_n": 3,                 # in-sample optimal; correlation filter makes TopN>3 redundant in this universe
    },
    "multi_asset": {
        "sma_lookback_days": 126,   # 6 months  — walk-forward consensus (6/6 windows)
        "roc_lookback_days": 63,    # 3 months  — walk-forward consensus (4/6 windows)
        "top_n": 5,                 # walk-forward consensus (4/6 windows); wider TopN suits 12-ETF cross-asset universe
    },
    "factor": {
        "sma_lookback_days": 210,   # 10 months — walk-forward consensus (W5+W6 agree; mode across 6 windows)
        "roc_lookback_days": 21,    # 1 month   — walk-forward consensus (5/6 windows)
        "top_n": 3,                 # walk-forward consensus (4/6 windows)
    },
    "bond": {
        "sma_lookback_days": 126,   # 6 months  — walk-forward consensus (6/6 windows; extremely stable)
        "roc_lookback_days": 63,    # 3 months  — walk-forward consensus (6/6 windows; extremely stable)
        "top_n": 10,                # walk-forward consensus (W4-W6); bonds benefit from diversification not concentration
    },
    "top20": {
        "sma_lookback_days": 126,   # 6 months  — walk-forward consensus (5/6 windows)
        "roc_lookback_days": 126,   # 6 months  — walk-forward consensus (5/6 windows)
        "top_n": 5,                 # walk-forward consensus (4/6 windows)
    },
}

# Backtest Parameters
BACKTEST_START_DATE = "2016-01-01"
BACKTEST_END_DATE = "2026-03-01"
DATA_START_DATE = "2006-01-01"  # Need historical data for SMA calculation (2006 for 19-year backtest)
INITIAL_CAPITAL = 100000.0

# Strategy Parameters
TOP_N_HOLDINGS = 3  # Optimized: 3 holdings outperform 5 (was 5)
REBALANCE_FREQUENCY = "weekly"  # Options: "weekly" (best: 378% return, 0.700 Sharpe) or "monthly" (340% return, 0.649 Sharpe)
SMA_LOOKBACK_DAYS = 210  # 10 months (optimized: was 200)
RS_ROC_LOOKBACK_DAYS = 63  # 3 months (optimized: was 21 for 1 month)
RISK_FREE_RATE = 0.045  # 4.5% annual risk-free rate for Sharpe calculation
STOP_LOSS_THRESHOLD = 0.95  # Stop order at 95% of entry price (5% stop loss)

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

# Short Selling (Hedge Sleeve)
# Always-on short book: bottom N ETFs from the universe that fail both filters.
# Adds 25% gross short on top of 100% long (125% gross total).
# Closes automatically when the breadth filter triggers.
ENABLE_SHORT_SELLING = True           # Master kill switch for short selling across all universes
SHORT_ENABLED_UNIVERSES = ['emerging', 'commodity', 'sp500']  # Universes with short selling active; add more as validated

# Per-universe short parameters — optimized independently per universe via short_optimizer.py.
# Only universes listed in SHORT_ENABLED_UNIVERSES are active; entries here are ignored otherwise.
# emerging params: validated via 72-combo grid search, 10yr + 19yr backtest (April 2026).
SHORT_UNIVERSE_PARAMS = {
    'emerging': {
        'top_n':         3,                       # Bottom 3 ETFs shorted equally (11% each at 33% allocation)
        'allocation':    0.33,                    # 33% gross short notional on top of 100% long (133% gross)
        'stop_loss':     1.03,                    # Cover if price rises 3% above entry
        'qualification': 'momentum_quality_only', # Bottom N by momentum quality; no filter gate required
    },
    'commodity': {
        'top_n':         2,                       # Bottom 2 ETFs shorted equally (16.5% each at 33% allocation)
        'allocation':    0.33,                    # 33% gross short notional on top of 100% long (133% gross)
        'stop_loss':     1.03,                    # Cover if price rises 3% above entry
        'qualification': 'both_filters',          # Must fail both RS and absolute trend filters (stricter gate)
    },
    'sp500': {
        'top_n':         1,                       # Single worst sector (cleaner signal in 12-ETF universe)
        'allocation':    0.33,                    # 33% gross short notional on top of 100% long (133% gross)
        'stop_loss':     1.03,                    # Cover if price rises 3% above entry
        'qualification': 'both_filters',          # both_filters == momentum_quality_only (tied); stricter gate chosen
    },
}

# Correlation Filter (Anti-Overlap)
# Prevents selecting highly correlated ETFs (e.g. SMH + XLK) in the same portfolio.
# Greedy selection: take top-ranked, skip any candidate with rolling correlation
# above threshold vs any already-selected holding.
ENABLE_CORRELATION_FILTER = True
CORRELATION_FILTER_THRESHOLD = 0.85  # Skip candidate if corr > this with any selected ETF
CORRELATION_LOOKBACK_DAYS = 60       # Rolling window for daily return correlation

# Breadth Filter (Master Switch)
# Uses % of sector ETFs above their SMA as a leading defensive indicator.
# When breadth is low (broad participation collapsing), reduce concentration.
ENABLE_BREADTH_FILTER = True
BREADTH_FILTER_THRESHOLD = 0.40   # < 40% of sector ETFs above SMA = low breadth
BREADTH_TOP_N_OVERRIDE = 1        # Reduce to 1 holding when breadth is low
BREADTH_CASH_ALLOCATION = 0.5     # Cash (SGOV) allocation when breadth triggers: 0.0=none, 0.5=50%, 1.0=100%

# API Settings
FMP_API_DELAY = 0  # No delay needed (3000 calls/min plan)

# Signal Mode Settings
SIGNAL_DATA_LOOKBACK_DAYS = 400  # Days to fetch for signal generation (ensures 200-day SMA)

# Directory Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
# Use importlib.resources so etflist/ works both from source and when installed
ETFLIST_DIR = Path(importlib.resources.files("etfmomentum").joinpath("etflist"))

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Data Cache File
PRICE_DATA_CACHE = DATA_DIR / "price_data.csv"

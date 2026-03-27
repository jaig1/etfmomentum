"""ETF Momentum package.

A comprehensive ETF Relative Strength Momentum Rotation Strategy framework
with backtesting and live signal generation capabilities.

Usage:
    # As a library
    from etfmomentum import RSEngine, Backtester, generate_current_signals

    # As a CLI
    $ etfmomentum signal --universe sp500 --detailed
    $ etfmomentum backtest --universe sp500 --refresh
"""

__version__ = "0.1.0"

# Core engine imports
from .rs_engine import generate_signals
from .backtest import run_backtest, get_rebalance_dates
from .signal_generator import generate_current_signals, select_current_portfolio, run_signals
from .etf_loader import load_universe_by_name as _load_universe_by_name
from .data_fetcher import get_price_data
from .report import (
    calculate_metrics,
    generate_performance_summary,
    print_performance_summary,
)
from .volatility_regime import VolatilityRegime, create_regime_detector

# Config
from . import config


# Convenience wrapper for load_universe_by_name
def load_universe_by_name(universe_name: str, etflist_dir=None):
    """
    Load ETF universe by name.

    Args:
        universe_name: Name of universe ('sp500', 'emerging', 'developed')
        etflist_dir: Optional path to etflist directory (defaults to package etflist/)

    Returns:
        Dict mapping ticker to name
    """
    if etflist_dir is None:
        etflist_dir = config.ETFLIST_DIR
    return _load_universe_by_name(universe_name, etflist_dir)

__all__ = [
    # Version
    "__version__",

    # Core functions
    "generate_signals",
    "run_backtest",
    "generate_current_signals",
    "select_current_portfolio",
    "run_signals",
    "get_rebalance_dates",

    # Data loading
    "load_universe_by_name",
    "get_price_data",

    # Reporting
    "calculate_metrics",
    "generate_performance_summary",
    "print_performance_summary",

    # Volatility regime
    "VolatilityRegime",
    "create_regime_detector",

    # Config module
    "config",
]

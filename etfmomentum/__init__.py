"""ETF Momentum - Relative Strength Signal Generator.

Generates momentum-based ETF rotation signals across three universes
(sp500, developed, emerging) using relative strength vs SPY, dual SMA
filters, and SGOV cash protection.

Usage:
    from etfmomentum import run_signals

    etfs = run_signals('sp500')      # e.g. ['XLK', 'XLF', 'XLC']
    etfs = run_signals('emerging')   # e.g. ['ARGT', 'INDA', 'SGOV']
    etfs = run_signals('developed')  # e.g. ['EWJ', 'EWG', 'EWU']

Requires:
    FMP_API_KEY environment variable (Financial Modeling Prep)

CLI:
    etfmomentum signal --universe sp500
    etfmomentum backtest --universe sp500
"""

__version__ = "0.2.0"

from .signal_generator import run_signals

__all__ = [
    "__version__",
    "run_signals",
]

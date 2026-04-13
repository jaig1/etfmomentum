"""ETF Momentum - Relative Strength Signal Generator.

Generates momentum-based ETF rotation signals across seven universes
(sp500, developed, emerging, commodity, multi_asset, factor, bond) using
relative strength vs SPY, dual SMA filters, and SGOV cash protection.

Usage:
    from etfmomentum import run_signals, run_short_signals

    # Long signals — tickers to buy
    etfs = run_signals('sp500')        # e.g. ['XLK', 'XLF', 'XLC']
    etfs = run_signals('emerging')     # e.g. ['ARGT', 'INDA', 'SGOV']

    # Short signals — tickers to sell short (empty for non-enabled universes)
    shorts = run_short_signals('emerging')  # e.g. ['KWEB', 'MCHI', 'FXI']
    shorts = run_short_signals('sp500')     # []  (not yet enabled)

Requires:
    FMP_API_KEY environment variable (Financial Modeling Prep)

CLI:
    etfmomentum signal --universe sp500
    etfmomentum signal --universe emerging
    etfmomentum backtest --universe emerging
    etfmomentum short-optimize --universe emerging
"""

__version__ = "0.10.0"

from .signal_generator import run_signals, run_short_signals

__all__ = [
    "__version__",
    "run_signals",
    "run_short_signals",
]

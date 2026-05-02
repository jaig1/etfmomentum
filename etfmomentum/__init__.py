"""ETF Momentum - Relative Strength Signal Generator.

Generates momentum-based ETF rotation signals across eight universes
(sp500, developed, emerging, commodity, multi_asset, factor, bond, top20) using
relative strength vs SPY, dual SMA filters, and SGOV cash protection.

Usage:
    from etfmomentum import run_signals, run_short_signals

    # Long signals — tickers to buy
    etfs = run_signals('sp500')                          # uses FMP_API_KEY env var
    etfs = run_signals('emerging', api_key='your_key')  # or pass key explicitly

    # Short signals — tickers to sell short (empty for non-enabled universes)
    shorts = run_short_signals('emerging')               # e.g. ['KWEB', 'MCHI', 'FXI']
    shorts = run_short_signals('sp500')                  # e.g. ['XLE']

Requires:
    FMP_API_KEY environment variable (Financial Modeling Prep)

CLI:
    etfmomentum signal --universe sp500
    etfmomentum signal --universe emerging
    etfmomentum backtest --universe emerging
    etfmomentum short-optimize --universe emerging
"""

__version__ = "0.19.0"

from .signal_generator import run_signals, run_short_signals

__all__ = [
    "__version__",
    "run_signals",
    "run_short_signals",
]

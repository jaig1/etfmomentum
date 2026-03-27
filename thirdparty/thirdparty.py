"""
Third-party usage example for the etfmomentum package.

Simulates an external developer who has installed etfmomentum from Git
and uses its public API to generate signals for all three ETF universes.
"""

from etfmomentum import run_signals

UNIVERSES = ["sp500", "developed", "emerging"]

for universe in UNIVERSES:
    etfs = run_signals(universe)
    print(f"{universe.upper()}: {etfs}")

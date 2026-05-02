# Using ETF Momentum as a Library

The package exposes two public functions: `run_signals()` and `run_short_signals()`.

---

## Installation

Install a specific release from Git (recommended for reproducibility):

```bash
pip install git+https://github.com/jaig1/etfmomentum.git@v0.19.0
```

Or always latest:

```bash
pip install git+https://github.com/jaig1/etfmomentum.git
```

Verify the installed version:

```python
import etfmomentum
print(etfmomentum.__version__)  # e.g. '0.19.0'
```

---

## API Key

The package requires a [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/) API key.

**Option 1 — Pass at call time (preferred for security):**

```python
etfs = run_signals('sp500', api_key='your_key_here')
```

**Option 2 — Environment variable / `.env` file:**

```bash
echo 'FMP_API_KEY=your_key_here' > .env
```

```python
from etfmomentum import run_signals
etfs = run_signals('sp500')  # reads FMP_API_KEY from environment
```

The key is resolved lazily — importing the package succeeds without it. `ValueError` is raised only when a call is made without a key available.

---

## `run_signals()`

Returns the list of ETF tickers to **hold long** for the current week.

### Signature

```python
run_signals(
    universe: str,
    date: pd.Timestamp | None = None,
    top_n: int | None = None,
    api_key: str | None = None,
) -> list[str]
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `universe` | `str` | required | Universe name — see table below |
| `date` | `pd.Timestamp` | `None` | Signal date (None = latest trading day) |
| `top_n` | `int` | `None` | Holdings to select (None = strategy default per universe) |
| `api_key` | `str` | `None` | FMP API key; falls back to `FMP_API_KEY` env var |

**Returns:** List of ticker strings. Positions underperforming SGOV are replaced with `'SGOV'` (cash). When the breadth filter triggers, returns `['SGOV', top_1_ticker]`.

### Examples

```python
from etfmomentum import run_signals

# Basic — reads FMP_API_KEY from environment
etfs = run_signals('sp500')        # e.g. ['XLK', 'XLF', 'XLC']
etfs = run_signals('emerging')     # e.g. ['ARGT', 'INDA', 'EWZ']
etfs = run_signals('commodity')    # e.g. ['GLD', 'SLV', 'PPLT']

# Pass API key explicitly (preferred for security)
etfs = run_signals('sp500', api_key='your_key_here')

# Historical signal for a specific date
import pandas as pd
etfs = run_signals('sp500', date=pd.Timestamp('2025-01-15'))

# Override number of holdings
etfs = run_signals('sp500', top_n=5)
```

---

## `run_short_signals()`

Returns the list of ETF tickers to **sell short** for the current week.

Returns `[]` for universes where short selling is not enabled, when the master kill switch is off, or when the breadth filter is triggered.

### Signature

```python
run_short_signals(
    universe: str,
    api_key: str | None = None,
) -> list[str]
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `universe` | `str` | required | Universe name |
| `api_key` | `str` | `None` | FMP API key; falls back to `FMP_API_KEY` env var |

**Returns:** List of ticker strings to short, or `[]`.

### Examples

```python
from etfmomentum import run_signals, run_short_signals

# Long and short signals are mutually exclusive — no overlap guaranteed
longs  = run_signals('emerging')        # e.g. ['ARGT', 'INDA', 'EWZ']
shorts = run_short_signals('emerging')  # e.g. ['KWEB', 'MCHI', 'FXI']

longs  = run_signals('sp500')           # e.g. ['XLK', 'XLF', 'XLC']
shorts = run_short_signals('sp500')     # e.g. ['XLU']  (top_n=1 for sp500)

# Non-enabled universes always return []
run_short_signals('bond')        # []
run_short_signals('multi_asset') # []
```

### Short-Enabled Universes and Position Sizing

| Universe | Enabled | top_n | Allocation | Stop |
|---|---|---|---|---|
| `emerging` | Yes | 3 | 33% gross | 3% |
| `commodity` | Yes | 2 | 33% gross | 3% |
| `sp500` | Yes | 1 | 33% gross | 3% |
| `developed` | Yes | 1 | 33% gross | 3% |
| `multi_asset` | No | — | — | — |
| `factor` | No | — | — | — |
| `bond` | No | — | — | — |
| `top20` | No | — | — | — |

Position sizing per universe: **long 100% + short 33% = 133% gross, 67% net long.**

The bot is responsible for position sizing, order execution, and stop-loss tracking. Stop = cover if price rises N% above entry (tracked daily, not just on rebalance day).

---

## Weekly Rebalance Pattern

```python
from etfmomentum import run_signals, run_short_signals

universe = 'emerging'

new_longs  = run_signals(universe)
new_shorts = run_short_signals(universe)

# Long side
# - Sell positions no longer in new_longs
# - Buy new positions not currently held
# - Intra-week: sell if price < entry * 0.95

# Short side
# - Cover shorts no longer in new_shorts (rotation exit)
# - If new_shorts == [] and had open shorts → cover all (breadth filter / no candidates)
# - Open new shorts not currently held
# - Intra-week (daily): cover if price > entry * 1.03
```

---

## ETF Universes

| Universe | ETF Count | Description | Default top_n |
|---|---|---|---|
| `sp500` | 12 | 11 SPDR sector ETFs + SMH | 3 |
| `emerging` | 28 | Country/regional emerging market ETFs | 3 |
| `developed` | 26 | iShares country ETFs | 3 |
| `commodity` | 10 | Commodity ETFs (oil, gold, gas, agriculture, metals) | 3 |
| `multi_asset` | 12 | Cross-asset ETFs (equities, bonds, commodities, real estate) | 5 |
| `factor` | 12 | Factor ETFs (value, growth, quality, momentum, size, low-vol) | 3 |
| `bond` | 12 | Bond duration/credit ETFs | 10 |
| `top20` | 20 | Live TOPT ETF holdings via FMP API (mega-cap stocks) | 5 |

**Benchmark:** SPY (all universes)
**Cash equivalent:** SGOV (iShares 0-3 Month Treasury Bond ETF)

---

## Signal Logic

Each call to `run_signals()` internally:

1. Fetches recent price data from FMP (no caching)
2. Checks sector breadth — if < 40% of ETFs above their SMA, reduces to 1 holding + 50% SGOV
3. Calculates relative strength (RS ratio) of each ETF vs SPY
4. Applies dual momentum filters: RS ratio > its SMA AND ETF price > its SMA
5. Ranks qualifying ETFs by **Momentum Quality** (RS ROC ÷ StdDev — smooth trends beat one-day gaps)
6. Applies correlation filter — skips candidates with > 0.85 rolling correlation to already-selected holdings
7. Fills remaining slots with SPY if fewer than top_n qualify
8. Replaces any holding with 3-month ROC below SGOV's with `'SGOV'`

SMA window and ROC lookback are universe-specific (see `UNIVERSE_PARAMS` in `config.py`).

---

## Validated Performance (production config, April 2026)

| Universe | Period | Sharpe | Ann Return | MaxDD |
|---|---|---|---|---|
| Emerging + Short | 10yr | **2.765** | 56.80% | -9.10% |
| Commodity + Short | 10yr | **2.252** | 60.57% | -10.56% |
| SP500 + Short | 10yr | **1.661** | 29.33% | -8.09% |
| Developed + Short | 10yr | **1.439** | 22.57% | -8.47% |
| SP500 long-only | 10yr | 1.266 | 23.51% | -11.83% |
| Top20 | 16 months* | **3.394** | 125.43% | -8.92% |

*Top20: bias-free track from TOPT ETF inception (Oct 2024 – Mar 2026); not comparable to 10yr figures.

SPY benchmark over the same 10yr period: ~236% total return, ~12.5% annualized.

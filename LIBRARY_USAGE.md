# Using ETF Momentum as a Library

The package exposes a single public function: `run_signals()`.

---

## Installation

Install directly from Git:

```bash
pip install git+https://github.com/jaig1/etfmomentum.git
```

Or with uv:

```bash
uv pip install git+https://github.com/jaig1/etfmomentum.git
```

### API Key

The package requires a Financial Modeling Prep API key. Set it before use:

```bash
# Option 1: .env file in your project directory
echo 'FMP_API_KEY=your_key_here' > .env

# Option 2: Environment variable
export FMP_API_KEY='your_key_here'
```

Get a free key at: https://financialmodelingprep.com/developer/docs/

---

## Usage

```python
from etfmomentum import run_signals
```

### Signature

```python
run_signals(
    universe: str,
    date: pd.Timestamp | None = None,
    top_n: int | None = None,
) -> list[str]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `universe` | `str` | required | `'sp500'`, `'developed'`, or `'emerging'` |
| `date` | `pd.Timestamp` | `None` | Signal date (None = today) |
| `top_n` | `int` | `None` | Holdings to select (None = strategy default of 3) |

**Returns:** List of ETF ticker strings. Any position underperforming SGOV (short-term treasuries) is replaced with `'SGOV'` as a cash equivalent.

---

### Examples

**Get current signals for all universes:**

```python
from etfmomentum import run_signals

for universe in ['sp500', 'developed', 'emerging']:
    etfs = run_signals(universe)
    print(f"{universe.upper()}: {etfs}")

# Example output:
# SP500: ['XLK', 'XLF', 'XLC']
# DEVELOPED: ['EWJ', 'EWG', 'SGOV']
# EMERGING: ['ARGT', 'INDA', 'EWZ']
```

**Get signals for a specific historical date:**

```python
import pandas as pd
from etfmomentum import run_signals

etfs = run_signals('sp500', date=pd.Timestamp('2025-01-15'))
print(etfs)
```

**Override number of holdings:**

```python
from etfmomentum import run_signals

etfs = run_signals('sp500', top_n=5)
print(etfs)  # Up to 5 tickers
```

---

## Signal Logic

Each call to `run_signals()` internally:

1. Fetches recent price data from FMP (no caching)
2. Calculates relative strength (RS ratio) of each ETF vs SPY
3. Applies dual momentum filters:
   - RS ratio must be above its 10-month SMA (relative trend)
   - ETF price must be above its 10-month SMA (absolute trend)
4. Ranks qualifying ETFs by 3-month RS momentum
5. Selects top N — fills remaining slots with SPY if fewer than N qualify
6. Replaces any holding with a 3-month ROC below SGOV's with `'SGOV'`

---

## ETF Universes

| Universe | Count | Description |
|----------|-------|-------------|
| `sp500` | 11 | S&P 500 SPDR sector ETFs (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC) |
| `developed` | 26 | Developed-market country ETFs (Japan, Germany, UK, Australia, Canada, France, Switzerland, and more) |
| `emerging` | 28 | Emerging-market country ETFs (China, India, Taiwan, Brazil, Argentina, Saudi Arabia, and more) |

**Benchmark:** SPY (all universes)
**Cash equivalent:** SGOV (iShares 0-3 Month Treasury Bond ETF)

---

## Backtest Performance (reference)

The following results used the same signal logic as `run_signals()` with weekly rebalancing and 5% stop-loss orders.

**S&P 500 Sectors (Jan 2016 – Mar 2026, 10 years):**
- Total Return: **610.93%** vs SPY 218.04%
- Annualized: **21.18%** vs 12.00%
- Max Drawdown: **-27.63%** vs -34.10%
- Sharpe Ratio: **1.016** vs 0.471

**Emerging Markets (Aug 2020 – Mar 2026, ~6 years):**
- Total Return: **687.61%** vs SPY 94.28%
- Annualized: **44.23%** vs 12.51%
- Max Drawdown: **-19.12%** vs -25.36%
- Sharpe Ratio: **1.741** vs 0.514

**Developed Markets (Aug 2020 – Mar 2026, ~6 years):**
- Total Return: **140.73%** vs SPY 94.28%
- Annualized: **16.87%** vs 12.51%
- Max Drawdown: **-17.47%** vs -25.36%
- Sharpe Ratio: **0.842** vs 0.514

---

## Verifying Installation

```python
import etfmomentum

print(etfmomentum.__version__)   # 0.1.0

from etfmomentum import run_signals
etfs = run_signals('sp500')
print(etfs)                       # e.g. ['XLK', 'XLF', 'XLC']
```

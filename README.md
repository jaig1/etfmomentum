# ETF Momentum - Relative Strength Framework

A Python package for **generating momentum-based ETF rotation signals** and **backtesting** across three ETF universes (S&P 500 sectors, developed markets, emerging markets).

## Overview

Implements a quantitative momentum strategy:
- Ranks ETFs by relative strength vs SPY
- Applies dual momentum filters (relative + absolute trend vs 10-month SMA)
- Selects top 3 performers, equal-weighted
- Replaces underperformers with SGOV (short-term treasuries) as cash protection
- 5% stop-loss orders between rebalances

**Backtest Performance (weekly rebalancing, 5% stop-loss):**

| Universe | Period | Total Return | vs SPY | Max Drawdown | Sharpe |
|----------|--------|-------------|--------|-------------|--------|
| S&P 500 Sectors | 2016–2026 (10yr) | **610.93%** | +392% | -27.63% | 1.016 |
| Emerging Markets | 2020–2026 (6yr) | **687.61%** | +593% | -19.12% | 1.741 |
| Developed Markets | 2020–2026 (6yr) | **140.73%** | +46% | -17.47% | 0.842 |
| SPY Benchmark | 2016–2026 | 218.04% | — | -34.10% | 0.471 |

---

## Quick Start (Library)

Install from Git:

```bash
pip install git+https://github.com/jaig1/etfmomentum.git
```

Set your FMP API key:

```bash
echo 'FMP_API_KEY=your_key_here' > .env
```

Generate signals:

```python
from etfmomentum import run_signals

etfs = run_signals('sp500')      # e.g. ['XLK', 'XLF', 'XLC']
etfs = run_signals('emerging')   # e.g. ['ARGT', 'INDA', 'EWZ']
etfs = run_signals('developed')  # e.g. ['EWJ', 'EWG', 'SGOV']
```

`run_signals()` is the only public interface. It fetches fresh data from FMP on every call, runs the full signal logic, and returns a list of tickers to hold. See [LIBRARY_USAGE.md](LIBRARY_USAGE.md) for full documentation.

---

## API Key

This package requires a [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/) API key.

```bash
# .env file (recommended)
FMP_API_KEY=your_key_here

# Or environment variable
export FMP_API_KEY='your_key_here'
```

---

## ETF Universes

### S&P 500 Sector ETFs (`sp500`)
11 SPDR sector ETFs: XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC

### Developed Market ETFs (`developed`)
26 iShares country ETFs covering Japan, Germany, UK, Australia, Canada, France, Switzerland, Spain, Italy, Netherlands, Sweden, Belgium, Singapore, Hong Kong, Norway, Denmark, Finland, Ireland, Israel — including small-cap and currency-hedged variants.

### Emerging Market ETFs (`emerging`)
28 country/regional ETFs across Asia (China, India, Taiwan, South Korea, Malaysia, Indonesia, Thailand, Philippines, Vietnam), Latin America (Brazil, Mexico, Chile, Peru, Argentina, Colombia), and EMEA (Turkey, Poland, Saudi Arabia, UAE, Qatar, South Africa, Egypt, Nigeria, Greece).

**Benchmark for all universes:** SPY
**Cash equivalent:** SGOV (iShares 0-3 Month Treasury Bond ETF)

---

## Strategy Logic

1. **RS Ratio**: ETF price ÷ SPY price
2. **Relative filter**: RS ratio > its 10-month SMA
3. **Absolute filter**: ETF price > its 10-month SMA
4. **Momentum ranking**: 3-month RS Rate of Change (ROC)
5. **Selection**: Top 3 qualifying ETFs, equal-weighted (33% each)
6. **SPY fallback**: If fewer than 3 qualify, fill remaining slots with SPY
7. **SGOV protection**: Replace any holding whose 3-month ROC < SGOV's 3-month ROC
8. **Stop-loss**: 5% stop orders set at each rebalance, triggered positions moved to SGOV

---

## CLI Interface

The package also ships a CLI for backtesting and signal generation:

```bash
# Signal generation
etfmomentum signal --universe sp500
etfmomentum signal --universe emerging --detailed

# Backtesting
etfmomentum backtest --universe sp500 --start-date 2016-01-01 --end-date 2026-03-27
etfmomentum backtest --universe emerging --start-date 2020-08-01 --end-date 2026-03-27

# Options
etfmomentum backtest --universe sp500 --top-n 5 --initial-capital 50000
etfmomentum --help
```

### Web UI

```bash
./start_api.sh   # FastAPI backend at http://localhost:8000
./start_ui.sh    # React UI at http://localhost:3000
```

---

## Project Structure

```
etfmomentum/
├── etfmomentum/          # Core package (run_signals is the public API)
├── api/                  # FastAPI backend
├── ui/                   # React Web UI
├── etflist/              # ETF universe CSV definitions
├── output/               # Backtest results (gitignored)
├── data/                 # Price data cache (gitignored)
├── thirdparty/           # Third-party usage example
└── pyproject.toml
```

---

## Requirements

- Python 3.11+
- Financial Modeling Prep API key
- Dependencies: pandas, numpy, requests, python-dotenv, tabulate

---

## License

MIT

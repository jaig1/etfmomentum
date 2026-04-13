# ETF Momentum — Release Notes

---

## v0.10.0 — Short Hedge Sleeve (April 2026)

### Overview

v0.10.0 introduces an always-on short selling hedge for the **emerging market universe**. A new public function `run_short_signals()` is added alongside the existing `run_signals()`, giving trading bots a symmetric interface for both long and short signals.

---

### New Public API

#### `run_short_signals(universe: str) -> List[str]`

Returns tickers to **sell short** for the given universe.

```python
from etfmomentum import run_signals, run_short_signals

# Long signals — tickers to buy
longs  = run_signals('emerging')        # e.g. ['EPOL', 'ILF', 'EWT']

# Short signals — tickers to sell short
shorts = run_short_signals('emerging')  # e.g. ['KWEB', 'MCHI', 'FXI']

# Non-enabled universes always return empty list
shorts = run_short_signals('sp500')     # []
shorts = run_short_signals('commodity') # []
shorts = run_short_signals('developed') # []
shorts = run_short_signals('bond')      # []
shorts = run_short_signals('factor')    # []
shorts = run_short_signals('multi_asset') # []
```

**Behaviour:**
- Returns `[]` for any universe not in `SHORT_ENABLED_UNIVERSES` (currently only `'emerging'`)
- Returns `[]` when the master kill switch `ENABLE_SHORT_SELLING = False`
- Returns `[]` when the breadth filter is triggered (< 40% of sectors above SMA) — defensive mode
- Automatically excludes tickers already selected by `run_signals()` — no long/short conflicts
- All parameters resolved internally from `SHORT_UNIVERSE_PARAMS` — bot passes universe name only

---

### Trading Bot Integration

#### Weekly Rebalance Flow

```python
from etfmomentum import run_signals, run_short_signals

universe = 'emerging'

longs  = run_signals(universe)       # tickers to hold long
shorts = run_short_signals(universe) # tickers to sell short

# longs and shorts are mutually exclusive — no overlap guaranteed
```

#### Position Sizing

| Sleeve | Allocation | Per position |
|--------|-----------|--------------|
| Long   | 100%      | 33.3% (top 3) |
| Short  | 33%       | 11% each (3 positions) |
| Gross exposure | 133% | |
| Net long exposure | 67% | |

The bot is responsible for all position sizing, order execution, and stop tracking.

#### Short Stop-Loss (bot responsibility)

The signal functions return tickers only — stop management is the bot's responsibility:

```python
# On opening a new short position:
entry_price  = get_current_price(ticker)
cover_stop   = entry_price * 1.03   # cover if price rises 3% above entry

# Check daily (not just on rebalance day):
if current_price > cover_stop:
    cover_short(ticker)             # buy-to-cover
    # do not re-enter until next weekly rebalance signal
```

#### Breadth Filter — Short Book Closure

When `run_short_signals()` returns `[]` after previously returning tickers, the breadth filter has triggered. The bot should cover all open short positions:

```python
new_shorts = run_short_signals(universe)

if not new_shorts and existing_short_positions:
    cover_all_shorts()   # breadth filter — go fully defensive
```

#### Weekly Rebalance Checklist

```
1. Call run_signals(universe)        → new long targets
2. Call run_short_signals(universe)  → new short targets

3. Long side:
   - Sell longs no longer in new_longs list
   - Buy new longs not in current positions

4. Short side:
   - Cover shorts no longer in new_shorts list (rotation exit)
   - If new_shorts is [] and had open shorts → cover all (breadth triggered)
   - Open new shorts not in current short positions

5. Intra-week (daily):
   - Check each short: if price > entry * 1.03 → cover immediately
   - Check each long : if price < entry * 0.95 → sell immediately
```

---

### Validated Performance — Emerging Universe (Rank 1 Config)

| Period | Sharpe | Ann Return | Max Drawdown | vs Baseline |
|--------|--------|-----------|--------------|-------------|
| 10yr (2016–2026) | **2.514** | 46.74% | -7.68% | +0.652 Sharpe |
| 19yr (2007–2026) | **2.436** | 44.17% | -8.35% | +0.720 Sharpe |

**Baseline (long-only, no shorts):**

| Period | Sharpe | Ann Return | Max Drawdown |
|--------|--------|-----------|--------------|
| 10yr | 1.862 | 36.04% | -9.09% |
| 19yr | 1.716 | 34.20% | -11.35% |

Optimization: 72-combo grid search over `top_n × allocation × stop_loss × qualification`.
Validated on both 10yr and 19yr periods before locking parameters.

---

### Short Parameters — Emerging Universe

Parameters are stored in `SHORT_UNIVERSE_PARAMS['emerging']` in `config.py`.
These are **not intended to be overridden by the trading bot** — they are strategy parameters validated through the optimization process.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `top_n` | 3 | Bottom 3 ETFs by momentum quality score |
| `allocation` | 0.33 | 33% gross short notional |
| `stop_loss` | 1.03 | Cover if price rises 3% above entry |
| `qualification` | `momentum_quality_only` | No filter gate; pure signal ranking |

---

### New CLI Command

```bash
# Grid search optimizer for short sleeve parameters
uv run python -m etfmomentum short-optimize --universe emerging

# Backtest with short hedge active
uv run python -m etfmomentum backtest --universe emerging --start-date 2016-01-01 --end-date 2026-04-08
```

---

### Universes Enabled for Short Selling

| Universe | Short Enabled | Notes |
|----------|--------------|-------|
| emerging | Yes | Optimized and validated v0.10.0 |
| sp500 | No | Pending optimization |
| developed | No | Pending optimization |
| commodity | No | Pending optimization |
| multi_asset | No | Pending optimization |
| factor | No | Pending optimization |
| bond | No | Not suitable (long-only complement universe) |

To enable shorts for a new universe: add optimized params to `SHORT_UNIVERSE_PARAMS` and add the universe name to `SHORT_ENABLED_UNIVERSES` in `config.py`.

---

### Installation

```bash
pip install git+https://github.com/jaig1/etfmomentum.git@v0.10.0
```

---

## v0.9.0 — Bond ETF Universe (April 2026)

Added 12-ETF bond universe. 10yr Sharpe 0.477. Complement universe for capital preservation in equity bear years (2018, 2020, 2022). Walk-forward decay 0.58.

## v0.8.0 — Factor ETF Universe (April 2026)

Added 12-ETF factor universe. 10yr Sharpe 0.716. Walk-forward decay 0.87 (robust).

## v0.7.0 — Multi-Asset ETF Universe (April 2026)

Added 12-ETF cross-asset universe. 10yr Sharpe 1.147. SPY circularity note: value is drawdown protection, not equity alpha.

## v0.6.0 — Commodity ETF Universe (April 2026)

Added 10-ETF commodity universe. 10yr Sharpe 1.861. Regime-dependent: outperforms in inflation/commodity bull cycles.

## v0.5.0 — Unified Signal Pipeline (April 2026)

Backtest, CLI, and `run_signals()` all share `_compute_tickers()`. Baseline locked: 10yr Sharpe 1.266 (SP500), 1.862 (emerging).

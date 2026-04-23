# ETF Momentum — Release Notes

---

## v0.14.0 — Top 20 Stock Universe (April 23, 2026)

### Overview

v0.14.0 adds a new **Top 20 mega-cap stock universe** — the first individual-stock universe in the framework. All existing ETF universes and short sleeves are unchanged.

### New Universe: `top20`

20 of the largest US stocks by market cap, covering technology, consumer, financials, healthcare, and energy:

```
NVDA, AAPL, GOOGL, MSFT, AMZN, BRK-B, TSLA, AVGO, META,
JPM, LLY, XOM, JNJ, WMT, V, COST, MA, NFLX, ABBV, MU
```

> **Note:** `BRK-B` uses hyphen format (not `BRK.B`) — required by the FMP API.

### Optimized Parameters

Parameters determined via 48-combination grid search, validated with 6-window walk-forward (decay ratio 0.99):

| Parameter | Value | Source |
|---|---|---|
| `sma_lookback_days` | 126 (6 months) | Walk-forward consensus (5/6 windows) |
| `roc_lookback_days` | 126 (6 months) | Walk-forward consensus (5/6 windows) |
| `top_n` | 5 | Walk-forward consensus (4/6 windows) |

### Validated Performance

**10-Year Backtest (2016–2026, WF consensus params):**

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | 93,412% | 241% |
| Annualized Return | 96.45% | 12.88% |
| Sharpe Ratio | 2.849 | 0.514 |
| Max Drawdown | -16.10% | -34.10% |
| Win Rate (years) | 10/10 | — |

**Walk-Forward OOS (6 windows):**

| Metric | Value |
|---|---|
| Combined OOS Return | 24,470% |
| Avg OOS Sharpe | 2.320 |
| OOS/IS Decay Ratio | **0.99** (near-zero degradation) |
| Windows beating SPY | 6/6 |

**Year-wise Max Drawdown — Strategy consistently protects capital:**

| Year | Strategy | SPY |
|---|---|---|
| 2018 | -2.0% | -14.0% |
| 2020 | -3.9% | -19.9% |
| 2022 | -3.7% | -20.9% |

### Turnover Characteristics

- **Rebalance frequency:** Weekly
- **Average holding period:** ~5 weeks per position
- **Annual turnover:** ~1,000% (approx. 0.5 positions rotated per week)
- **Tax note:** Almost all gains are short-term. Best suited for tax-advantaged accounts (IRA/401k).

### How to Use

```bash
# Run current signals
uv run python -m etfmomentum signal --universe top20 --detailed

# Run 10-year backtest
uv run python -m etfmomentum backtest --universe top20 --start-date 2016-01-01

# Run walk-forward validation
uv run python -m etfmomentum walk-forward --universe top20

# Re-run grid search optimization
uv run python -c "from etfmomentum.optimizer import optimize_parameters; optimize_parameters(universe='top20', output_subdir='top20')"
```

### Installation

```bash
pip install git+https://github.com/jaig1/etfmomentum.git@v0.14.0
```

### Files Changed

| File | Change |
|---|---|
| `etfmomentum/etflist/top20_stock.csv` | New — 20 mega-cap stock universe |
| `etfmomentum/etf_loader.py` | Registered `top20` in universe map |
| `etfmomentum/config.py` | Added `top20` to `UNIVERSE_PARAMS` |
| `etfmomentum/main.py` | Added `top20` to CLI universe choices |

---

## v0.13.0 — Short Hedge Sleeve: SP500 Universe + Short Pipeline Hardening (April 17, 2026)

### Overview

v0.13.0 delivers two changes:

1. **SP500 short sleeve** — the short hedge sleeve is now enabled for the `sp500` universe after a 72-combo grid search. The sector universe (12 ETFs) rewards a concentrated single-position short against the weakest sector, adding +0.36 Sharpe and tightening MaxDD from -11.83% to -8.09%.

2. **Short pipeline hardening** — two new filters are applied to all short candidate selection across every enabled universe (`rs_engine.py`, `signal_generator.py`):
   - **Directional gate:** candidates must be in confirmed absolute downtrend (`price < SMA` AND `rs_roc < 0`) before being eligible to short
   - **Correlation filter:** the same 0.85-threshold greedy correlation filter already used on the long side is now applied to short candidate pools — prevents doubling up on two highly-correlated laggards

These pipeline changes are shared across emerging and commodity universes as well. Existing validated params for those universes remain unchanged.

---

### What Changed

| File | Change |
|---|---|
| `config.py` | `sp500` added to `SHORT_ENABLED_UNIVERSES`; `SHORT_UNIVERSE_PARAMS['sp500']` added |
| `rs_engine.py` | `get_short_candidates()` gains optional `pool_size` param — allows callers to request a larger pool for downstream filtering |
| `signal_generator.py` | Directional gate + correlation filter applied in `_run_short_signals_with_data()` and `run_short_signals()` |

No changes to `run_signals()` or `run_short_signals()` function signatures — fully backward compatible.

---

### Short Parameters — SP500 Universe

| Parameter | Value | Notes |
|---|---|---|
| `top_n` | 1 | Single weakest sector (concentrated — 33% per position) |
| `allocation` | 0.33 | 33% gross short on top of 100% long (133% gross) |
| `stop_loss` | 1.03 | Cover if price rises 3% above entry |
| `qualification` | `both_filters` | Must fail RS filter AND absolute trend filter |

**Why `top_n=1`:** The SP500 sector universe (12 ETFs) is more correlated than emerging or commodity — adding a second short typically introduces a correlated position rather than independent alpha. Grid search avg Sharpe: 1.377 (top_n=1) vs 1.342 (top_n=2) vs 1.350 (top_n=3).

**Why `both_filters`:** Tied exactly with `momentum_quality_only` in the grid search. With the new directional gate applied universally in the pipeline, the two qualification modes converge — `both_filters` chosen as the stricter / more defensible gate.

**Why 3% stop:** Decisive sensitivity finding consistent across all three universes. Avg Sharpe 1.488 at 3% vs 1.267 at 10%. Tight stop preserves gains on short positions that reverse quickly.

---

### Short Pipeline Hardening — All Universes

#### Directional Gate

Before a short candidate is selected, it must satisfy:

```python
price < SMA      # abs_filter == False  (absolute downtrend)
rs_roc < 0       # RS ratio is declining vs SPY
```

This prevents shorting ETFs that are merely relative underperformers in a broadly rising market — they must be in a confirmed absolute downtrend with deteriorating RS momentum.

#### Correlation Filter on Short Pool

The greedy correlation filter (same as long side, 60-day rolling, 0.85 threshold) is applied to the short candidate pool before final selection. If two laggard candidates have >0.85 rolling correlation, only the weaker one is selected.

**Example:** During an energy/materials downturn, XLE and XLB may both qualify as shorts. The correlation filter prevents holding both, keeping the short book diversified.

---

### Optimization Summary — SP500 (72-combo grid search, 10yr)

| Parameter | Sensitivity Finding |
|---|---|
| `top_n` | **1 dominates** — avg Sharpe 1.377 vs 1.342 (2) vs 1.350 (3) |
| `stop_loss` | **3% is decisive** — avg Sharpe 1.488 (3%) vs 1.375 (5%) vs 1.267 (10%) |
| `allocation` | Marginally insensitive; 33% best, 25% close |
| `qualification` | Exactly tied; `both_filters` chosen as stricter gate |

---

### Validated Performance — SP500 Universe

| Period | Metric | Long-Only | With Short | Delta |
|---|---|---|---|---|
| 10yr (2016–2026) | Sharpe | 1.266 | **1.626** | +0.360 |
| 10yr | Ann Return | 23.51% | **28.70%** | +5.19pp |
| 10yr | Max Drawdown | -11.83% | **-8.09%** | +3.74pp tighter |
| 10yr | Total Return | 769% | **1,224%** | — |
| 10yr | Activation rate | — | **82%** | — |
| 10yr | Stop triggers | — | **62** (~6.2/yr) | — |
| 19yr (2007–2026) | Sharpe | ~0.991 | **1.397** | — |
| 19yr | Ann Return | ~18.5% | **25.06%** | — |
| 19yr | Max Drawdown | -13.03% | **-8.52%** | — |
| 19yr | Total Return | 2,531% | **7,272%** | — |
| 19yr | Win rate (years) | — | **14/19** | — |

Standout years for the short sleeve:

| Year | Strategy | SPY | Delta |
|---|---|---|---|
| 2008 | +21.1% | -38.3% | **+59.4pp** |
| 2022 | +39.9% | -19.5% | **+59.4pp** |
| 2020 | +66.4% | +16.2% | +50.2pp |

---

### Trading Bot Integration — SP500

```python
from etfmomentum import run_signals, run_short_signals

longs  = run_signals('sp500')        # e.g. ['SMH', 'XLF', 'XLC']
shorts = run_short_signals('sp500')  # e.g. ['XLU']  — single position
```

#### Position Sizing — SP500

| Sleeve | Allocation | Per position |
|---|---|---|
| Long | 100% | 33.3% (top 3) |
| Short | 33% | 33% (1 position) |
| Gross exposure | 133% | |
| Net long exposure | 67% | |

#### Stop-Loss (bot responsibility)

```python
# On opening a new short position:
entry_price = get_current_price(ticker)
cover_stop  = entry_price * 1.03   # cover if price rises 3% above entry

# Check daily:
if current_price > cover_stop:
    cover_short(ticker)
    # do not re-enter until next weekly rebalance signal
```

#### SP500 Weekly Rebalance Checklist

```
1. Call run_signals('sp500')        → new long targets (top 3 sectors)
2. Call run_short_signals('sp500')  → new short target (0 or 1 ticker)

3. Long side (unchanged from prior versions):
   - Sell longs no longer in new_longs
   - Buy new longs not in current positions
   - Intra-week: cover if price < entry * 0.95

4. Short side:
   - Cover if ticker no longer in new_shorts (rotation exit)
   - If new_shorts is [] and had open short → cover (breadth or no candidates)
   - Open new short if not already held
   - Intra-week (daily): cover if price > entry * 1.03
```

---

### Universe Enablement Status (v0.13.0)

| Universe | Short Enabled | Notes |
|---|---|---|
| `emerging` | **Yes** | Optimized v0.10.0; breadth-filter reversal v0.11.0; Sharpe 2.778 (19yr) |
| `commodity` | **Yes** | Optimized v0.12.0; top_n=2; Sharpe 2.194 (10yr) |
| `sp500` | **Yes** | Optimized v0.13.0; top_n=1; Sharpe 1.626 (10yr) |
| `developed` | No | Pending |
| `multi_asset` | No | Pending |
| `factor` | No | Candidate — slow factor rotations may reward shorting |
| `bond` | No | Not suitable — long-only complement universe |

---

### Installation

```bash
pip install git+https://github.com/jaig1/etfmomentum.git@v0.13.0
```

---

## v0.12.0 — Short Hedge Sleeve: Commodity Universe (April 15, 2026)

### Overview

v0.12.0 extends the short hedge sleeve to the **commodity universe** after a 72-combo grid search. Commodity ETFs (oil, natural gas, gold, agriculture, metals, copper) are driven by completely independent supply/demand factors — the highest natural dispersion of any universe tested. Laggards such as UNG, BNO, and CORN exhibit persistent downtrends uncorrelated with long winners like GLD, SLV, and PPLT.

---

### What Changed

- `SHORT_ENABLED_UNIVERSES` expanded from `['emerging']` to `['emerging', 'commodity']`
- `SHORT_UNIVERSE_PARAMS['commodity']` added to `config.py` with validated parameters

No API changes — `run_signals()` and `run_short_signals()` signatures are unchanged.

---

### Short Parameters — Commodity Universe

| Parameter | Value | Notes |
|---|---|---|
| `top_n` | 2 | Bottom 2 ETFs by momentum quality (16.5% each at 33% allocation) |
| `allocation` | 0.33 | 33% gross short on top of 100% long (133% gross) |
| `stop_loss` | 1.03 | Cover if price rises 3% above entry |
| `qualification` | `both_filters` | Must fail RS filter AND absolute trend filter |

**Why `both_filters` for commodity (vs `momentum_quality_only` for emerging):** With only 10 ETFs in the universe (vs 28 for emerging), requiring both filters fail ensures only ETFs in confirmed absolute downtrend are shorted — avoiding the risk of shorting an ETF that is merely a relative underperformer in a broadly rising commodity market.

**Why `top_n=2` (vs 3 for emerging):** Grid search sensitivity showed top_n=2 dominates (avg Sharpe 2.000 vs 1.957 for top_n=3). The smaller universe and correlation structure naturally favours 2 concentrated shorts.

---

### Optimization Summary (72-combo grid search, 10yr)

| Parameter | Sensitivity Finding |
|---|---|
| `top_n` | **2 dominates** — avg Sharpe 2.000 vs 1.957 (3) vs 1.860 (1) |
| `stop_loss` | **3% is critical** — avg Sharpe 2.061 (3%) vs 1.850 (10%); tightest stop best |
| `allocation` | Insensitive across 15/25/33%; 33% chosen for consistency |
| `qualification` | Exactly tied; `both_filters` chosen as stricter / more defensive gate |

---

### Validated Performance — Commodity Universe

| Period | Metric | Long-Only | With Short | Delta |
|---|---|---|---|---|
| 10yr (2016–2026) | Sharpe | 1.861 | **2.194** | +0.333 |
| 10yr | Ann Return | 47.38% | **59.21%** | +11.83pp |
| 10yr | Max Drawdown | -10.67% | **-10.56%** | flat |
| 10yr | Activation rate | — | **95%** | — |
| 19yr (2007–2026) | Sharpe | — | **2.034** | — |
| 19yr | Ann Return | — | **48.67%** | — |
| 19yr | Max Drawdown | — | **-10.56%** | — |
| 19yr | Activation rate | — | **92%** | — |

All 6 backtest runs (3× 10yr, 3× 19yr) deterministic.

---

### Trading Bot Integration — Commodity

```python
from etfmomentum import run_signals, run_short_signals

longs  = run_signals('commodity')        # e.g. ['GLD', 'SLV', 'PPLT']
shorts = run_short_signals('commodity')  # e.g. ['UNG', 'BNO']
```

#### Position Sizing — Commodity

| Sleeve | Allocation | Per position |
|---|---|---|
| Long | 100% | 33.3% (top 3) |
| Short | 33% | 16.5% each (2 positions) |
| Gross exposure | 133% | |
| Net long exposure | 67% | |

Stop-loss logic is identical to emerging: cover if price rises 3% above entry, checked daily.

---

### Universe Enablement Status (v0.12.0)

| Universe | Short Enabled | Notes |
|---|---|---|
| `emerging` | **Yes** | Optimized v0.10.0; breadth-filter reversal v0.11.0 |
| `commodity` | **Yes** | Optimized + validated v0.12.0 |
| `sp500` | No | Not recommended — high intra-sector correlation limits dispersion |
| `developed` | No | Pending |
| `multi_asset` | No | Pending |
| `factor` | No | Candidate — slow factor rotations may reward shorting |
| `bond` | No | Not suitable — long-only complement universe |

---

### Installation

```bash
pip install git+https://github.com/jaig1/etfmomentum.git@v0.12.0
```

---

## v0.11.0 — Short Book Kept Open During Breadth Filter (April 15, 2026)

### Overview

v0.11.0 reverses the breadth filter interaction with the short book for the emerging universe. Previously, when breadth < 40% (defensive mode), the short book was closed entirely. The new behaviour **keeps shorts open** during low-breadth regimes.

---

### Rationale

Low-breadth environments mean the broad market is in systemic weakness — most ETFs are already below their SMA. This is precisely when laggard ETFs fall hardest. Closing shorts during defensive periods was leaving the most significant short alpha unrealised. The 67% → 100% activation rate improvement confirms shorts are valid and profitable during these periods.

The long side behaviour is unchanged: breadth filter still triggers 50% SGOV + 50% top-1 holding.

---

### Impact — Emerging Universe 19-Year Backtest

| Metric | v0.10.0 | v0.11.0 | Delta |
|---|---|---|---|
| Sharpe | 2.436 | **2.778** | +0.342 |
| Ann Return | 44.17% | **53.75%** | +9.58pp |
| Max Drawdown | -8.35% | **-8.12%** | improved |
| Short activation | 67% | **100%** | +33pp |

All 3 runs deterministic.

---

### What Changed

Single logic change in `backtest.py`: the `if not breadth_triggered` gate on short candidate selection was removed. The short book is now populated unconditionally on every rebalance, regardless of breadth state.

No API or config changes. Behaviour change is internal to the backtest and live signal engine.

---

### Installation

```bash
pip install git+https://github.com/jaig1/etfmomentum.git@v0.11.0
```

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
# Note: sp500 and commodity are now enabled as of v0.13.0 and v0.12.0
shorts = run_short_signals('sp500')       # e.g. ['XLU']  (enabled v0.13.0)
shorts = run_short_signals('commodity')   # e.g. ['UNG', 'BNO']  (enabled v0.12.0)
shorts = run_short_signals('developed')   # []
shorts = run_short_signals('bond')        # []
shorts = run_short_signals('factor')      # []
shorts = run_short_signals('multi_asset') # []
```

**Behaviour:**
- Returns `[]` for any universe not in `SHORT_ENABLED_UNIVERSES` (currently only `'emerging'`)
- Returns `[]` when the master kill switch `ENABLE_SHORT_SELLING = False`
- Returns `[]` when the breadth filter is triggered (< 40% of sectors above SMA) — defensive mode *(changed in v0.11.0: backtest engine keeps shorts open; live API still returns `[]` when breadth triggers for safety)*
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

### Validated Performance — Emerging Universe (Rank 1 Config, v0.10.0 baseline)

*Note: 19yr numbers superseded by v0.11.0 (Sharpe 2.778, Ann 53.75%).*

| Period | Sharpe | Ann Return | Max Drawdown | vs Baseline |
|--------|--------|-----------|--------------|-------------|
| 10yr (2016–2026) | **2.514** | 46.74% | -7.68% | +0.652 Sharpe |
| 19yr (2007–2026) | 2.436 | 44.17% | -8.35% | +0.720 Sharpe |

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

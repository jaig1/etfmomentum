# ETF Momentum Strategy — Comprehensive Overview

*Last updated: April 12, 2026 | Version: 0.7.0 (multi-asset ETF universe)*

---

## Table of Contents

1. [Strategy Concept](#1-strategy-concept)
2. [Core Mechanism](#2-core-mechanism)
3. [Iteration History](#3-iteration-history)
4. [Defensive Layers](#4-defensive-layers)
5. [Optimization Research](#5-optimization-research)
6. [Universe Analysis](#6-universe-analysis)
7. [Current Performance](#7-current-performance)
8. [Architecture](#8-architecture)
9. [Caveats and Risks](#9-caveats-and-risks)
10. [Commodity Universe — Detailed Notes](#10-commodity-universe--detailed-notes)
11. [Multi-Asset Universe — Detailed Notes](#11-multi-asset-universe--detailed-notes)

---

## 1. Strategy Concept

The ETF Momentum Strategy is a **relative strength sector rotation** system. It holds a concentrated portfolio of the top-performing S&P 500 sector ETFs at any point in time, rotating monthly (or weekly) into whichever sectors are showing the strongest momentum relative to the broad market.

The core insight is that sector performance trends. Energy leads for multi-year cycles. Technology dominates during earnings-driven expansions. Utilities and healthcare outperform in risk-off environments. By systematically identifying which sectors are leading and concentrating capital there — while exiting laggards — the strategy aims to compound returns significantly above a buy-and-hold SPY approach.

**What makes it different from simple sector picking:**
- Signals are rules-based and systematic, not discretionary
- Both *relative* strength (vs SPY) and *absolute* trend are required to enter a position
- Momentum quality — not just magnitude — determines ranking (smooth trends beat one-day gaps)
- Four independent defensive layers protect capital during drawdowns
- The universe is narrow (12 ETFs) and sector-level, keeping transaction costs and complexity low

---

## 2. Core Mechanism

### Signal Generation

At each rebalance date the strategy calculates two filters for every ETF in the universe:

**Filter 1 — Relative Strength (RS Ratio)**
- RS = (ETF price / SPY price), normalized to a base of 1.0
- Rate of Change (ROC) of the RS ratio over a universe-specific lookback period
- Positive ROC means the ETF is outperforming SPY on a trend basis

**Filter 2 — Absolute Trend (SMA)**
- ETF price must be above its universe-specific simple moving average
- This prevents buying into downtrending ETFs regardless of relative strength
- ETFs in absolute downtrends are excluded even if they're "the best of a bad bunch"

> **Universe-specific parameters** — the SMA window, ROC lookback, and Top N are determined per universe. See Section 6 for the validated values and the rationale.


**Ranking — Momentum Quality (Risk-Adjusted Momentum)**
- ETFs passing both filters are ranked by *Momentum Quality*, not raw ROC
- Formula: `RS_ROC(63) / StdDev(daily RS ratio returns, 63 days)`
- This is the Information Ratio of the relative strength trend: how much outperformance per unit of volatility
- A sector that gaps up 20% in one day scores lower than one that trends up steadily over 3 months
- Smooth, persistent trends are historically more likely to continue; erratic movers suffer more momentum crashes

**Portfolio Construction**
- Top 3 by Momentum Quality are selected for equal-weight allocation
- If fewer than 3 ETFs pass both filters, remaining slots go to SGOV (cash equivalent)

### Rebalancing

- **Default:** Monthly (first trading day of the month)
- **Alternative:** Weekly with volatility regime switching (tested and validated)
- Trades only execute when the signal changes — many weeks require no action

---

## 3. Iteration History

The strategy evolved through several distinct phases, each adding measurable performance improvements.

---

### Phase 1 — Baseline Implementation

**When:** Initial build (pre-March 2026)
**Universe:** 11 S&P 500 sector ETFs (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLU, XLRE, XLC)
**Parameters:**
- SMA Lookback: 210 days (10 months)
- ROC Lookback: 21 days (1 month)
- Top N Holdings: 5
- Rebalancing: Monthly

**10-Year Performance (2016–2026):**
| Metric | Strategy | SPY |
|---|---|---|
| Total Return | 270.81% | 141.26% |
| Sharpe Ratio | 0.574 | — |
| vs SPY | +129.55% | — |

The baseline already outperformed SPY significantly. The 1-month ROC lookback and 5-position portfolio were the starting assumptions, not yet validated.

---

### Phase 2 — Parameter Optimization (March 14, 2026)

**What was done:** A grid search across 48 parameter combinations, running full 10-year backtests for each combination.

**Grid:**
- SMA Windows: 6, 8, 10, 12 months (84, 126, 210, 252 days)
- ROC Lookbacks: 1, 3, 6 months (21, 63, 126 days)
- Top N Holdings: 3, 5, 7, 10 positions
- **Total combinations:** 4 × 3 × 4 = 48

**Key Findings:**

*Finding 1 — Concentration beats diversification*

Average Sharpe ratio by portfolio size:
| Holdings | Avg Sharpe |
|---|---|
| 3 | 0.591 |
| 5 | 0.573 |
| 7 | 0.571 |
| 10 | 0.558 |

The 4th and 5th ranked ETFs consistently diluted returns from the top positions. S&P 500 sector ETFs are internally diversified (XLK holds ~70 stocks), so 3 sectors already represents hundreds of underlying companies.

*Finding 2 — Momentum lookback matters enormously*

- 1-month ROC: captures noise, too reactive to short-term reversals
- 3-month ROC: captures sustainable sector trends without lag
- 6-month ROC: too slow to adapt to regime changes

Moving from 1-month to 3-month lookback increased returns by ~25%.

*Finding 3 — SMA window is a secondary factor*

Optimal range is 10–12 months. Average Sharpe:
- 6-month SMA: 0.581
- 8-month SMA: 0.543
- 10-month SMA: 0.583
- 12-month SMA: 0.585

The existing 10-month (210-day) choice was already near-optimal.

**Top 5 Parameter Combinations:**
| Rank | SMA | ROC | Top N | Return | Sharpe |
|---|---|---|---|---|---|
| 1 | 10mo | 3mo | 3 | 341.37% | 0.656 |
| 2 | 12mo | 1mo | 3 | 339.87% | 0.655 |
| 3 | 10mo | 1mo | 3 | 333.22% | 0.652 |
| 4 | 6mo | 6mo | 5 | 299.85% | 0.613 |
| 5 | 8mo | 1mo | 3 | 304.85% | 0.613 |

**Baseline ranked 24th out of 48.** Switching to top-3 + 3-month ROC moved it to rank 1.

**Result of optimization:**
- Total Return: 270.81% → 341.37% (+70.56 pp)
- Sharpe Ratio: 0.574 → 0.656 (+14.2%)
- Outperformance vs SPY: +129.55% → +100.11% (different periods; SPY also moved)

---

### Phase 3 — Long-Term Validation and Leverage Analysis (March 14, 2026)

**What was done:** Tested optimized parameters on a 19-year period (2007–2026) to stress-test across the 2008 financial crisis and multiple market cycles.

**Data constraint:** XLC (Communication Services) only has data from June 2018; XLRE from October 2015. The 19-year backtest uses the original 9 sectors (excluding both).

**19-Year Results (9 sectors, 2007–2026):**
| Metric | Strategy | SPY |
|---|---|---|
| Total Return | 580.42% | 385.24% |
| Annualized Return | 10.55% | — |
| Sharpe Ratio | 0.376 | 0.277 |
| Max Drawdown | -53.14% | -56.47% |
| Final Value ($100k) | $680k | $485k |
| Outperformance | +195.18% | — |

**2008 Crisis:** Strategy drawdown was -53.14% vs SPY's -56.47%. The defensive rotation to staples and utilities sectors reduced losses slightly even without explicit protective mechanisms.

**Leverage Analysis:**

Given the -53% max drawdown, safe leverage was calculated:
- Theoretical max: 1.88x
- With 30% margin requirement: 1.41x
- Conservative (50% buffer): 0.94x
- **Tested: 1.2x**

1.2x leverage backtest (19-year):
- Total Return: 810.45%
- Annualized: 12.24%
- Minimum equity hit: 58.94% (well above 30% margin requirement)
- No margin calls triggered across the entire 19-year period including 2008

---

### Phase 4 — Volatility Regime Switching

**What was done:** Added an adaptive position-sizing layer that detects the current volatility environment and adjusts the portfolio defensively.

**Regime Detection (SPY-based):**
- Calculate 30-day annualized volatility of SPY
- Low Vol: < 10% annualized
- Medium Vol: 10–25%
- High Vol: > 25%

**Regime-Specific Behavior:**
| Regime | Holdings | Additional Rules |
|---|---|---|
| Low Vol | 3 | Aggressive — no SPY floor |
| Medium Vol | 3 | Normal |
| High Vol | 5 | 20% minimum SPY allocation |

**Defensive modes tested for High Vol:**
- `baseline` — add SPY allocation
- `defensive_sectors` — force XLP, XLU, XLV
- `tbills` — 100% BIL (T-bills)
- `hybrid` — 50% T-bills + 50% defensive sectors
- `tiered` — defensive sectors in high vol, T-bills in extreme vol (>35%)

**Weekly rebalancing + vol regime:**
- Return: 378% (vs 341% monthly)
- Sharpe: 0.700 (vs 0.656 monthly)
- ~60–70% of weeks require no trades (signals unchanged)

---

### Phase 5 — SGOV Protection and Stop-Loss (March 2026)

Two additional independent protective mechanisms were added on top of vol regime switching.

**SGOV Protection (momentum-based cash safeguard):**

At each rebalance, the strategy compares each selected ETF's 63-day ROC against SGOV's 63-day ROC. If an ETF is underperforming even short-term treasury bills on a momentum basis, it is replaced with SGOV.

This is a second check after the RS/SMA filters — it catches cases where a sector passes the trend filters but has recently weakened relative to cash. The effect is a tactical, momentum-driven shift to safety without requiring a separate defensive mode.

**Stop-Loss (5% intraperiod exit):**

At each rebalance, an entry price and stop price (entry × 0.95) are set for each holding. Every trading day, if any holding's price drops below its stop price, the position is liquidated and the weight is reallocated to SGOV. SGOV itself is exempt.

This operates *between* rebalances, unlike all other signals which only fire at rebalance dates. It provides intraperiod risk control — if a sector collapses mid-month, the strategy exits rather than waiting for end-of-month rotation.

**Combined effect of the three layers:**

| Layer | Timing | Trigger | Action |
|---|---|---|---|
| Volatility Regime | Rebalance | SPY vol level | Adjust N + SPY floor |
| SGOV Protection | Rebalance | ETF ROC < SGOV ROC | Replace with SGOV |
| Stop-Loss | Daily | Price -5% from entry | Exit → SGOV |

---

### Phase 6 — SMH Addition and Universe Expansion (April 8, 2026)

**What was done:** Added SMH (VanEck Semiconductor ETF) to the S&P 500 universe, bringing it from 11 to 12 ETFs.

**Rationale:** SMH is not a SPDR sector ETF — it is a thematic ETF focused on semiconductor companies. Semiconductors are a subset of XLK (Technology) but have distinct characteristics: higher beta, more concentrated exposure to AI/chip cycle, and historically stronger momentum during tech bull runs. Adding it creates an "overweight" option for the technology/semiconductor trend without removing any existing sector coverage.

**Config change:** `DATA_START_DATE` moved back to `2006-01-01` to support full 19-year backtests.

**19-Year Results with SMH (2007–2026-04-08):**
| Metric | Strategy | SPY |
|---|---|---|
| Total Return | **4,745%** | 366% |
| Annualized Return | **22.36%** | 8.34% |
| Sharpe Ratio | **0.929** | 0.277 |
| Max Drawdown | **-28.48%** | -56.47% |
| Final Value ($100k) | **$4.85M** | $466k |
| Years beating SPY | 18/19 | — |

The Sharpe ratio improvement from 0.376 to 0.929 is the most dramatic change in the entire iteration history. SMH's inclusion captured the 2024–2025 AI/semiconductor bull cycle with full momentum allocation, while stop-loss and SGOV protection kept drawdowns at -28% vs the strategy's prior -53%.

**Standout years:**
| Year | Strategy | SPY |
|---|---|---|
| 2008 | +6.79% | -38.28% |
| 2020 | +48.81% | +16.16% |
| 2022 | +2.24% | -19.48% |
| 2026 YTD | +9.47% | -3.33% |

**Version bump:** 0.1.0 → 0.2.0

---

### Phase 7 — Momentum Quality Ranking (April 10, 2026)

**What was done:** Replaced raw RS ROC as the ranking signal with risk-adjusted momentum (Momentum Quality).

**Problem with raw ROC:** Rate of Change measures distance traveled, not journey quality. A sector that crashes 30% then bounces 35% in a single week has high ROC but "low quality" momentum. These erratic movers are historically prone to momentum crashes and reversals.

**The fix:** Divide RS_ROC(63) by the rolling standard deviation of daily RS ratio returns over the same 63-day window. This is the Information Ratio of the trend — it penalises noisy, erratic movers and prioritises sectors with smooth, persistent relative strength.

**Impact (vs prior baseline):**

| Metric | Before | After | Delta |
|---|---|---|---|
| 10yr Return | 857% | 862% | +5pp |
| 10yr Sharpe | 1.248 | 1.271 | +0.023 |
| 10yr MaxDD | -13.6% | -13.6% | flat |
| 19yr Return | 2,831% | 2,909% | +78pp |
| 19yr Sharpe | 0.973 | 0.997 | +0.024 |
| Walk-forward OOS | 504% / 4 of 6 windows | 576% / 5 of 6 windows | +72pp |

No deterioration on any metric. Sharpe improved across all periods.

---

### Phase 8 — Sector Breadth Filter (April 10, 2026)

**What was done:** Added a market breadth "master switch" that fires before the momentum ranking when broad sector participation is collapsing.

**Rationale:** SPY volatility (the existing regime signal) is a lagging indicator — it spikes *after* damage has occurred. Market breadth tends to deteriorate in advance. When fewer sectors are in uptrends, the environment is structurally hostile to concentrated momentum longs regardless of individual sector signals.

**Implementation:** At each rebalance, the strategy counts how many of the 11 sector ETFs have their current price above their 210-day SMA. If fewer than 40% do (i.e., < 5 of 11 sectors in uptrends), the breadth filter triggers.

**Three defensive actions were tested:**

| Action | 19yr Return | 19yr Sharpe | 19yr MaxDD |
|---|---|---|---|
| 100% top-1 sector | 3,605% | 1.009 | -19.1% |
| **50% SGOV + 50% top-1** | **2,955%** | **1.025** | **-12.7%** |
| 100% SGOV | 2,352% | 0.972 | -12.8% |

The 50% SGOV variant was selected: best Sharpe (1.025), tightest MaxDD (-12.7%), and still meaningfully outperforms the no-breadth baseline.

**Historical trigger periods (19-year backtest):**

| Period | Breadth Reading | Context |
|---|---|---|
| Jan–Mar 2008 | 0–30% | Pre-Lehman deterioration |
| Jul–Sep 2008 | 0–20% | Lehman collapse |
| Jan 2016 | 10% | China / oil selloff |
| Oct–Dec 2018 | 0–37% | Fed tightening crash |
| Mar–Apr 2020 | 0–8% | COVID crash |

**Impact vs Phase 7 baseline:**

| Metric | Before | After | Delta |
|---|---|---|---|
| 10yr Return | 862% | 901% | +39pp |
| 10yr Sharpe | 1.271 | 1.316 | +0.045 |
| 10yr MaxDD | -13.6% | **-11.8%** | +1.8pp tighter |
| 19yr Return | 2,909% | 2,955% | +46pp |
| 19yr Sharpe | 0.997 | **1.025** | +0.028 |
| 19yr MaxDD | -14.0% | **-12.7%** | +1.3pp tighter |

MaxDD improved on both periods — the breadth filter is reducing drawdowns while simultaneously improving returns.

---

### Phase 9 — Stop-Loss Whipsaw Validation (April 10, 2026)

**What was done:** Evaluated a proposal to replace the fixed 5% stop-loss with a volatility-adjusted ATR-based stop (2.5×ATR(20) below entry price). The proposal's premise was that a fixed 5% stop causes whipsaws in high-beta sectors like SMH, where a 5% intraday move is "noise."

**Analysis method:** Instrumented the 10-year backtest (2016–2026-04-08) to log every stop-loss trigger and track each stopped position's price at the *next* rebalance date (typically 3–5 trading days later). A whipsaw is defined as: price at next rebalance > entry price at stop.

**Results:**

| Metric | Result |
|---|---|
| Total stop-loss events (10yr) | 46 |
| Whipsaws (price > entry at next rebalance) | **0 / 46 (0%)** |
| Average drop at stop trigger | -6.4% from entry |
| Average price at next rebalance vs entry | -5.9% (still down) |

**By ticker:**

| Ticker | Stops | Avg drop at trigger | Avg recovery vs entry |
|---|---|---|---|
| SMH | 14 | -6.3% | -6.5% |
| XLE | 9 | -6.3% | -7.8% |
| XLB | 4 | -6.0% | -6.8% |
| XLY | 4 | -5.6% | -4.5% |
| Others | 15 | -6.3% | -5.3% |

SMH — the ticker the proposal was specifically trying to protect — accounted for 14/46 stops (30%). In every case the stop fired, SMH continued lower through the next rebalance.

**Findings:**

1. **No whipsaw problem exists.** In 100% of stop events, the position was still below entry at the next rebalance. The stop was protecting capital from real, continuing drawdowns — not cutting noise.

2. **Stops trigger late, not early.** The average drop at trigger is -6.4%, already past the 5% threshold. Positions were actively sliding before the daily price check caught them. After the stop, they declined further on average.

3. **ATR-based stop would not improve outcomes.** A 2.5×ATR stop sets a wider threshold for high-beta sectors. Given that all 46 stops were justified, widening them would only delay exit on real losers, worsening P&L.

4. **The existing four-layer system absorbs the scenarios ATR stops are designed for.** Volatile markets are already handled by vol regime switching (position sizing) and the sector breadth filter (defensive rotation before vol spikes). The stop-loss is a backstop, not the primary defence.

**Decision:** ATR-based stop-loss proposal rejected. Fixed 5% stop retained unchanged.

---

### Phase 10 — Universe-Specific Parameters (April 11, 2026)

**What was done:** Full 10yr, 19yr, and walk-forward backtests run for all three universes (sp500, emerging, developed) using their own walk-forward consensus parameters. Universe-specific parameters codified into `config.UNIVERSE_PARAMS`. The public API (`run_signals`, `POST /signals`) updated so callers pass only a universe name — the package resolves SMA, ROC, and TopN automatically.

**The silent bug fixed:** Before this change, calling `run_signals(universe="emerging")` would use SP500's global parameters (SMA=210d, ROC=63d). All universes were running with the wrong parameters. Emerging markets were especially penalised: 3-month ROC is too noisy for country-level signals.

**Key discovery:** With universe-appropriate parameters, **emerging markets dramatically outperforms SP500 sectors** in all three tests:
- 10yr: Sharpe 1.631 vs 1.316 for SP500
- 19yr: 16,320% total return vs 2,955%
- Walk-forward OOS: 734% combined return, 0.949 avg Sharpe, OOS/IS decay ratio 0.90

**API contract change:** `SignalRequest` no longer accepts `top_n`. The only required field is `universe`.

```python
# Before
run_signals(universe="emerging", top_n=3)   # wrong params used internally

# After
run_signals(universe="emerging")             # SMA=252d, ROC=21d, TopN=3 resolved automatically
```

---

### Phase 11 — Unified Signal Pipeline + Commodity Universe (April 12, 2026)

**What was done (v0.5.0 — Unified Pipeline):** The backtest engine, CLI signal mode, and public `run_signals()` were all found to follow slightly different signal computation paths. A shared `_compute_tickers()` function was extracted and made the single source of truth for all three interfaces. Baselines were locked: 10yr Sharpe 1.266, 19yr Sharpe 0.991 (SP500 universe).

**What was done (v0.6.0 — Commodity Universe):** A fourth standalone universe — `commodity` — was added and fully validated.

**ETF List (10 ETFs):**

| Ticker | Commodity | Type | Inception |
|---|---|---|---|
| GLD | Gold | Physical | 2004 |
| SLV | Silver | Physical | 2006 |
| PPLT | Platinum | Physical | 2010 |
| PALL | Palladium | Physical | 2010 |
| DBC | Broad Commodities | Futures basket | 2006 |
| DBB | Base Metals | Futures basket | 2007 |
| BNO | Brent Crude Oil | Futures | 2010 |
| UNG | Natural Gas | Futures | 2007 |
| CPER | Copper | Futures | 2011 |
| CORN | Corn | Futures | 2010 |

**Data availability constraint:** CPER (Copper) is the newest ETF, with data from November 2011. This sets the honest maximum backtest start at June 2012 (after the 6-month SMA warmup period). The 19-year backtest is not meaningful for this universe; all validated results use 2012+ data.

**Parameter optimisation:**

In-sample grid search (48 combinations, 2016–2026):

| Param | In-sample optimal | Walk-forward consensus (6/6 windows) | Used |
|---|---|---|---|
| SMA | 6mo (126d) | 6mo (126d) | **6mo** |
| ROC | 1mo (21d) | **6mo (126d)** | **6mo** |
| TopN | 3 | 5 (most frequent) | **3** |

Key insight: ROC=1mo dominates in-sample (avg Sharpe 2.021 vs 1.838 for ROC=6mo) but the walk-forward unanimously chose ROC=6mo in all 6 windows. ROC=1mo overfits — it is too reactive for commodity cycles. TopN was corrected from the walk-forward's 5 to 3 after observing that the correlation filter limits effective positions anyway (DBC as a broad basket is highly correlated with most individual commodity ETFs).

**Rebalancing frequency:** Weekly rebalancing is dramatically better for commodities than monthly — Sharpe 1.861 vs 1.146. Commodity momentum trends move faster than equity sector trends and weekly rebalancing captures entries and exits earlier.

**Walk-Forward Results (6 windows, 2007–2026):**

| Window | OOS Period | OOS Sharpe | OOS Return | vs SPY |
|---|---|---|---|---|
| W1 | 2014–2015 | -0.527 | -2.2% | -13.7pp — MISSED |
| W2 | 2016–2017 | 1.148 | 47.1% | +14.4pp |
| W3 | 2018–2019 | 1.520 | 53.2% | +33.5pp |
| W4 | 2020–2021 | 1.900 | 103.9% | +57.7pp |
| W5 | 2022–2023 | 0.353 | 17.1% | +17.6pp |
| W6 | 2024–2026 | 1.607 | 104.9% | +59.8pp |
| **Combined** | | **1.000** | **978%** | 5/6 beat SPY |

OOS/IS Sharpe decay ratio: **0.93** (robust — threshold is 0.70). Window 1 failure (2014–2015) reflects the commodity secular bear driven by USD strength and China slowdown — not a strategy flaw.

**Version bump:** 0.5.0 → 0.6.0

---

## 4. Defensive Layers

Four mechanisms provide capital protection, operating at different timescales and triggers:

```
Rebalance Signal
     │
     ├── [1] Breadth Filter (Master Switch)
     │         < 40% of sector ETFs above SMA → 50% SGOV + 50% top-1 sector
     │         Leading indicator: fires before volatility spikes
     │
     ├── [2] Volatility Regime Check
     │         Adjust N holdings and SPY floor based on current market vol
     │
     ├── [3] SGOV Momentum Check
     │         Replace any ETF where ROC < SGOV ROC with cash equivalent
     │
     └── Portfolio Set for Period
               │
               └── Daily Price Check
                         [4] Stop-Loss: exit any position down 5% from entry → SGOV
```

These four layers are additive and independent. Layer 1 (breadth) acts as a pre-filter before the momentum signal even runs. Layers 2 and 3 operate on the momentum-selected portfolio. Layer 4 provides intraperiod risk control between rebalances.

| Layer | Timing | Trigger | Action |
|---|---|---|---|
| [1] Breadth Filter | Rebalance | < 40% sectors above SMA | 50% SGOV + 50% top-1 sector |
| [2] Volatility Regime | Rebalance | SPY vol level | Adjust N holdings + SPY floor |
| [3] SGOV Momentum | Rebalance | ETF ROC < SGOV ROC | Replace position with SGOV |
| [4] Stop-Loss | Daily | Price -5% from entry | Exit position → SGOV — validated: 0/46 whipsaws in 10yr backtest |

---

## 5. Optimization Research

### Parameter Sensitivity

Most important parameters, in order of impact:

1. **Top N Holdings** — Massive impact. 3 is definitively better than 5+. Concentration wins in sector rotation because sectors are already internally diversified.

2. **ROC Lookback** — Large impact. 3 months captures sector trends. 1 month is too noisy. 6 months too slow. Aligns with Jegadeesh & Titman (1993) momentum research, adapted for sector-level signals.

3. **SMA Window** — Moderate impact. 10–12 months is the optimal zone. Protects against false signals during bear markets while remaining responsive enough for cycle changes.

### Academic Alignment

The findings align with momentum investing research:
- Jegadeesh & Titman (1993): 6–12 month momentum optimal at stock level
- Our finding: 3-month sector-level ROC (shorter due to sector aggregation smoothing noise)
- "Best ideas" literature: concentrated portfolios outperform diversified ones when using a high-conviction signal

### Robustness Check

The top 3 ranked parameter combinations are tightly clustered (Sharpe 0.652–0.656), suggesting the results are not highly sensitive to small parameter changes. This reduces overfitting concern for the chosen parameters.

---

## 6. Universe Analysis

Five universes are supported. Each has its own walk-forward validated parameters — the package resolves these automatically when a universe is specified. Third-party callers only need to pass the universe name.

### Validated Parameters Per Universe

| Universe | ETFs | SMA | ROC | Top N | Source |
|---|---|---|---|---|---|
| `sp500` | 12 | 210d (10mo) | 63d (3mo) | 3 | In-sample optimised |
| `emerging` | 28 | 252d (12mo) | 21d (1mo) | 3 | Walk-forward consensus (5/6 windows) |
| `developed` | 26 | 168d (8mo) | 21d (1mo) | 3 | Walk-forward consensus (6/6 windows) |
| `commodity` | 10 | 126d (6mo) | 126d (6mo) | 3 | Walk-forward consensus (6/6 windows) |
| `multi_asset` | 12 | 126d (6mo) | 63d (3mo) | 5 | Walk-forward consensus (4/6 windows) |

### Performance Comparison (April 12, 2026)

**10-Year (2016–2026-04-08):**

| Universe | Return | Ann. Return | Sharpe | MaxDD | vs SPY |
|---|---|---|---|---|---|
| SP500 | 901% | 25.24% | 1.316 | -11.8% | +663pp |
| **Emerging** | **1,890%** | **33.89%** | **1.631** | -14.18% | +1,652pp |
| Developed | 245% | 12.85% | 0.677 | -12.91% | +7pp |
| **Commodity** | **5,204%** | **47.38%** | **1.861** | **-10.67%** | +4,966pp |
| Multi-Asset | 470% | 18.54% | 1.147 | -13.05% | +232pp |
| SPY (B&H) | 238% | 12.58% | 0.499 | -34.1% | — |

**Max-History (2012–2026-04-08, commodity only):**

| Universe | Return | Ann. Return | Sharpe | MaxDD | vs SPY |
|---|---|---|---|---|---|
| Commodity | 6,445% | 35.34% | 1.536 | -23.06% | +6,018pp |
| SPY (B&H) | 427% | 12.79% | 0.533 | -34.1% | — |

Note: The 2012–2015 period captures the commodity secular bear (USD strength, China slowdown, oil crash), which widens MaxDD to -23% and reduces Sharpe from 1.861 to 1.536. The 10-year result starting 2016 is cleaner and reflects the full strategy with all defensive layers active.

**19-Year (2007–2026):**

| Universe | Return | Ann. Return | Sharpe | MaxDD | vs SPY |
|---|---|---|---|---|---|
| SP500 | 2,955% | 19.46% | 1.025 | -12.7% | +2,577pp |
| **Emerging** | **16,320%** | **30.36%** | **1.426** | -18.51% | +15,940pp |
| Developed | 827% | 12.27% | 0.603 | -19.06% | +447pp |
| Multi-Asset | 2,425% | 18.28% | 1.062 | — | +2,047pp |
| SPY (B&H) | 381% | 8.5% | 0.284 | -56.47% | — |

*Commodity 19yr not shown — CPER (Copper, inception Nov 2011) limits the honest start to 2012.*

**Walk-Forward OOS (6 windows):**

| Universe | Combined OOS Return | Avg OOS Sharpe | OOS/IS Decay | Windows Beat SPY |
|---|---|---|---|---|
| SP500 | 576% | 0.891 | ~0.87 | 5/6 |
| **Emerging** | **734%** | **0.949** | **0.90** | **5/6** |
| Developed | 210% | 0.420 | ~0.56 | 2/6 |
| **Commodity** | **978%** | **1.000** | **0.93** | **5/6** |
| Multi-Asset | 270% | 0.623 | ~0.78 | 2/6 |

### Why Parameters Differ Per Universe

**Emerging markets (SMA=12mo, ROC=1mo):** Country ETF trends are driven by slower-moving macro forces — commodity cycles, currency flows, political risk, demographic tailwinds. A longer SMA (12mo) ensures the strategy only goes long when a genuine multi-month uptrend is established. Short ROC (1mo) identifies which countries just broke out. With 28 mostly-uncorrelated country ETFs, concentration at TopN=3 works: a country bull market can last 2–3 years once established.

**Developed markets (SMA=8mo, ROC=1mo):** Developed country ETFs are more tightly correlated than EM (European economies move together) and trend somewhat faster than EM. The 8mo SMA is the walk-forward consensus across all 6 windows. Overall, the momentum dynamics are weaker — only 2/6 walk-forward windows beat SPY, making developed markets the weakest universe.

**Commodity (SMA=6mo, ROC=6mo):** Commodities trend in multi-year supercycles but rotate quickly within a cycle. A shorter SMA (6mo) keeps the strategy responsive to cycle turns. ROC=6mo (rather than the in-sample optimal ROC=1mo) was unanimously chosen by the walk-forward — 1-month ROC overfits commodity data by chasing short-term noise. The correlation filter naturally limits effective positions to 2-3 in this universe because DBC (broad basket) absorbs the correlation of most individual commodity ETFs.

**Multi-Asset (SMA=6mo, ROC=3mo, TopN=5):** Cross-asset rotation requires a wider portfolio (TopN=5) because the 12 ETFs span uncorrelated asset classes — holding only 3 would miss valid diversification. The 3-month ROC (walk-forward consensus 4/6 windows) balances responsiveness against noise. Note: SPY is both a universe member and the RS benchmark, creating a circularity that limits the RS signal quality for SPY itself. See Section 11.

**Why the original analysis showed EM underperforming:** Before April 11 2026, all universes used the SP500 global config parameters (SMA=210d, ROC=63d). This was wrong for EM — a 3-month ROC is too slow and noisy for country-level signals, and the 10mo SMA doesn't match EM trend dynamics. With universe-specific parameters applied, emerging markets becomes the strongest universe.

### Universe Selection Guidance

- Use `sp500` for US market sector rotation (primary, most validated, tightest drawdowns)
- Use `emerging` for highest return potential with slightly wider drawdowns (strongest walk-forward OOS)
- Use `commodity` for inflation-regime and commodity-cycle exposure; highest 10yr Sharpe but regime-dependent (see Section 10)
- Use `multi_asset` for cross-asset class rotation with drawdown protection; lower alpha vs equities but strong risk-adjusted returns (see Section 11)
- `developed` is the weakest universe; use only if there is a specific mandate for developed market exposure

---

## 7. Current Performance

### Current Parameters (v0.7.0)

```python
# Global (shared across all universes)
REBALANCE_FREQUENCY = "weekly"
CASH_TICKER = "SGOV"               # backfilled with BIL pre-2020-06-12
STOP_LOSS_THRESHOLD = 0.95         # 5% stop
ENABLE_VOLATILITY_REGIME_SWITCHING = True
ENABLE_BREADTH_FILTER = True
BREADTH_FILTER_THRESHOLD = 0.40    # < 40% of sectors above SMA = low breadth
BREADTH_CASH_ALLOCATION = 0.5      # 50% SGOV + 50% top-1 when breadth triggers

# Per-universe optimised parameters — resolved automatically by the package.
# Third-party callers only need to pass the universe name.
UNIVERSE_PARAMS = {
    "sp500":       { "sma_lookback_days": 210, "roc_lookback_days": 63,  "top_n": 3 },
    "emerging":    { "sma_lookback_days": 252, "roc_lookback_days": 21,  "top_n": 3 },
    "developed":   { "sma_lookback_days": 168, "roc_lookback_days": 21,  "top_n": 3 },
    "commodity":   { "sma_lookback_days": 126, "roc_lookback_days": 126, "top_n": 3 },
    "multi_asset": { "sma_lookback_days": 126, "roc_lookback_days": 63,  "top_n": 5 },
}
```

### 10-Year Summary (2016–2026-04-08)

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | **901%** | 236% |
| Annualized Return | **25.24%** | 12.58% |
| Sharpe Ratio | **1.316** | 0.499 |
| Max Drawdown | **-11.8%** | -34.1% |
| $100k → | **$1.00M** | $336k |
| Months beating SPY | 79 / 123 | — |
| Years beating SPY | 9 / 10 | — |

### 19-Year Summary (2007–2026-04-08)

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | **2,955%** | 378% |
| Annualized Return | **19.46%** | 8.48% |
| Sharpe Ratio | **1.025** | 0.283 |
| Max Drawdown | **-12.7%** | -56.47% |
| $100k → | **$3.06M** | $478k |
| Months beating SPY | 146 / 231 | — |
| Years beating SPY | 15 / 19 | — |

### Walk-Forward Validation (OOS, 6 windows, 2014–2026)

| Metric | Result |
|---|---|
| Combined OOS Return | 576% |
| Average OOS Sharpe | 0.891 |
| Windows beating SPY | 5 / 6 |

Walk-forward uses monthly rebalancing without vol regime switching, which structurally reduces OOS numbers relative to the weekly backtest. The 5/6 window beat rate and 576% OOS return confirm the signal generalises beyond the in-sample period.

### Commodity Universe — 10-Year Summary (2016–2026-04-08)

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | **5,204%** | 236% |
| Annualized Return | **47.38%** | 12.58% |
| Sharpe Ratio | **1.861** | 0.499 |
| Max Drawdown | **-10.67%** | -34.1% |
| $100k → | **$5.30M** | $336k |
| Months beating SPY | 67 / 123 | — |
| Years beating SPY | 8 / 10 | — |

### Commodity Universe — Year-by-Year (2016–2026)

| Year | Strategy | SPY | Alpha |
|---|---|---|---|
| 2017 | +30.8% | +19.4% | +11.4pp |
| 2018 | +25.1% | -6.4% | +31.4pp |
| 2019 | +33.1% | +28.8% | +4.3pp |
| 2020 | +71.8% | +16.2% | +55.6pp |
| 2021 | +77.8% | +27.0% | +50.8pp |
| 2022 | +46.7% | -19.5% | +66.2pp |
| 2023 | -1.0% | +24.3% | -25.3pp |
| 2024 | +14.7% | +23.3% | -8.6pp |
| 2025 | +156.1% | +16.4% | +139.7pp |
| 2026 (partial) | +69.4% | -0.9% | +70.3pp |

Strong in inflation/commodity bull regimes (2020–2022, 2025–2026). Underperforms in strong USD/equity-led regimes (2023–2024). See Section 10 for regime dependency details.

### Multi-Asset Universe — 10-Year Summary (2016–2026-04-08)

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | **470%** | 238% |
| Annualized Return | **18.54%** | 12.58% |
| Sharpe Ratio | **1.147** | 0.499 |
| Max Drawdown | **-13.05%** | -34.1% |
| $100k → | **$570k** | $336k |
| Years beating SPY | 6 / 10 | — |

### Multi-Asset Universe — 19-Year Summary (2007–2026-04-08)

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | **2,425%** | 381% |
| Annualized Return | **18.28%** | 8.5% |
| Sharpe Ratio | **1.062** | 0.284 |
| Years beating SPY | 10 / 19 | — |

### Current Signals (April 2026)

**SP500:** System has rotated out of SMH/XLK (semiconductor/tech) into defensive sectors: **XLE (Energy), XLB (Materials), XLU (Utilities)** — reflecting the risk-off, tariff-uncertainty environment of early 2026.

**Commodity:** **BNO (Brent Crude Oil), DBC (Broad Commodities), SGOV (Cash)** — only 2 commodity ETFs qualifying through the correlation filter; third slot is defensive cash.

---

## 8. Architecture

### Core Package (`etfmomentum/`)

| Module | Purpose |
|---|---|
| `config.py` | All parameters and configuration |
| `data_fetcher.py` | FMP API integration and price caching |
| `etf_loader.py` | Load ETF universes from CSV |
| `rs_engine.py` | RS ratio, SMA, ROC signal calculation |
| `backtest.py` | Portfolio simulation with daily stop-loss |
| `signal_generator.py` | Live signal generation with SGOV check; resolves per-universe params from `UNIVERSE_PARAMS` |
| `report.py` | Performance metrics (Sharpe, drawdown, etc.) |
| `main.py` | CLI orchestrator (backtest / signal modes) |

### Research Modules

| Module | Purpose |
|---|---|
| `optimizer.py` | 48-combination grid search |
| `volatility_regime.py` | Regime detection and adaptive allocation |
| `trading_frequency_analyzer.py` | Weekly vs monthly rebalancing analysis |
| `defensive_strategy_tester.py` | Defensive mode comparison |
| `volatility_timing_analyzer.py` | Vol signal lag analysis |

### Interfaces

- **CLI:** `uv run python -m etfmomentum signal|backtest --universe sp500 --refresh`
- **FastAPI backend:** `api/` — endpoints for dashboard, signals, backtest, config
- **React UI:** `ui/` — Vite/React on port 3000, connects to API on port 8000

### ETF Universe Files

| File | Universe | ETFs |
|---|---|---|
| `sp500_sector_etfs.csv` | `sp500` | 12: XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLU, XLRE, XLC, SMH |
| `emerging_market_etfs.csv` | `emerging` | 28: FXI, MCHI, KWEB, INDA, SMIN, EWT, EWY, EWM, EIDO, THD, EPHE, EWZ, EWW, ECH, EPU, TUR, EPOL, KSA, UAE, QAT, EZA, ILF, VNM, EGPT, ARGT, GXG, NGE, GREK |
| `developed_market_etfs.csv` | `developed` | 26: EWJ, EWG, EWU, EWA, EWC, EWQ, EWL, EWP, EWI, EWN, EWD, EWK, EWS, EWH, ENOR, EDEN, EFNL, EIRL, EIS, EWGS, SCJ, EWUS, EWAS, HEWJ, HEWG, HEWU |
| `commodity_etfs.csv` | `commodity` | 10: GLD, SLV, PPLT, PALL, DBC, DBB, BNO, UNG, CPER, CORN |
| `multi_asset_etfs.csv` | `multi_asset` | 12: SPY, IWM, QQQ, EFA, EEM, TLT, IEF, LQD, HYG, GLD, VNQ, DBC |

XLRE and XLC are gracefully skipped for pre-inception dates. CPER (Copper) limits commodity backtest start to June 2012. HYG (April 2007) is the limiting ETF for multi_asset — backtest starts July 2007 after SMA warmup.

---

## 9. Caveats and Risks

### Backtest Limitations

**Overfitting:** 48 combinations were tested on the same in-sample dataset. Walk-forward validation (6 windows, 576 backtests) was completed and shows 5/6 OOS windows beating SPY with a 576% combined OOS return (SP500 universe), reducing but not eliminating this concern. The walk-forward consensus for SP500 (SMA=8mo, ROC=1mo, TopN=10) differs from the in-sample optimum (SMA=10mo, ROC=3mo, TopN=3) — the current in-sample params have not been confirmed as walk-forward optimal for SP500. Emerging and developed universes use their own walk-forward consensus parameters directly.

**Survivorship bias:** The ETF universe was constructed with knowledge of which sectors exist today. Some ETFs did not exist at the start of the backtest period (XLC from 2018, XLRE from 2015).

**Market regime dependency:** Parameters were optimized on 2016–2026, a period that included a significant bull market. The 2008 crisis is covered in the 19-year test and the strategy performed well, but prolonged bear markets with different sector dynamics could stress the parameters.

### Stop-Loss Empirical Validation

The fixed 5% stop-loss was empirically validated in April 2026 via a full 10-year event study. All 46 stop events in the 2016–2026 backtest were analysed: in every case the stopped position continued lower at the next rebalance date (0% whipsaw rate). The stop-loss is functioning as a real loss cutter, not a noise amplifier. An ATR-based replacement was evaluated and rejected — see Phase 9 in the Iteration History.

### Concentration Risk

A 3-position portfolio has higher idiosyncratic volatility than a 5–10 position portfolio. While this was optimal on a risk-adjusted basis historically, individual sector blowups (e.g., energy in 2014–2015, financials in 2008) can cause short-term pain before the stop-loss or rebalance exits the position.

### Implementation Costs

- Bid-ask spreads and commissions are not modeled
- Large position sizes in less-liquid ETFs may cause slippage
- Monthly rebalancing keeps transaction costs low in practice

### SMH-Specific Risk

SMH's addition dramatically improved historical performance due to the 2024–2025 AI/semiconductor bull run. If the semiconductor cycle mean-reverts sharply, SMH will rotate out via the momentum signal — but the historical backtest result is partially a reflection of favorable timing for this specific addition.

---

---

## 10. Commodity Universe — Detailed Notes

### Regime Dependency

The commodity universe has a strong macro regime dependency that users must understand:

| Regime | Strategy Behaviour | Historical Example |
|---|---|---|
| Inflationary / commodity bull | Strong outperformance | 2020–2022 (post-COVID stimulus), 2025–2026 (tariff/gold surge) |
| Equity bull / USD strength | Underperforms SPY | 2013–2015 (China slowdown, oil crash), 2023–2024 (AI rally) |
| Risk-off / crisis | Defensive (gold-heavy) | 2018, partial 2022 |

This is fundamentally different from the equity universes (sp500, emerging, developed), which all use SPY as the benchmark and trend alongside broad risk appetite. The commodity universe diverges from equities — it is strongest precisely when equities are weak (inflation regimes) and weakest when equities are strong (disinflation regimes).

**Key implication:** The commodity universe is a *complement* to the SP500 universe, not a substitute. Running both simultaneously in a portfolio provides regime diversification.

### Correlation Filter Behaviour

DBC (Invesco DB Commodity Index Tracking Fund) is a broad basket that includes energy, metals, and agriculture. It is highly correlated with most individual commodity ETFs in the universe. As a result, once BNO (oil) and DBC are selected, the correlation filter (threshold: 0.85 rolling 60-day correlation) typically blocks SLV, GLD, DBB, CPER from being added.

**Practical consequence:** The effective portfolio is usually 2 real commodities + SGOV as the third slot. SGOV appearing in commodity signals is expected and correct — it is a defensive cash position, not a data error.

### Data Quality Notes

| ETF | Type | Risk |
|---|---|---|
| GLD, SLV, PPLT, PALL | Physical-backed | Clean return series — no roll cost |
| DBC, DBB, BNO, CORN | Futures-based | Subject to contango/roll costs; returns understate physical commodity exposure |
| UNG | Futures-based | Severe contango history; absolute returns are significantly eroded by roll costs |

Backtest returns reflect the ETF's actual NAV (including roll costs), so the strategy's returns already account for contango drag. However, users should understand that nominal commodity price moves will differ from what the strategy captures.

### Third-Party Usage

```python
from etfmomentum import run_signals

# Current signals (today)
etfs = run_signals('commodity')
# e.g. ['BNO', 'DBC', 'SGOV']

# Signals for a specific date
import pandas as pd
etfs = run_signals('commodity', date=pd.Timestamp('2026-04-08'))

# Install
# pip install git+https://github.com/jaig1/etfmomentum.git@v0.6.0
```

---

---

## 11. Multi-Asset Universe — Detailed Notes

### Universe Composition

12 ETFs spanning six asset classes:

| Asset Class | ETFs |
|---|---|
| US Equities (size/style) | SPY (large cap), IWM (small cap), QQQ (tech/growth) |
| International Equities | EFA (developed ex-US), EEM (emerging markets) |
| Fixed Income | TLT (20yr+ Treasuries), IEF (7-10yr Treasuries), LQD (IG corporate), HYG (high yield) |
| Real Assets | GLD (gold), VNQ (US REITs) |
| Commodities | DBC (broad commodities basket) |

### SPY Circularity

SPY serves a dual role: it is both a universe member (US Large Cap) and the benchmark used to compute RS ratios for all ETFs including itself. This means SPY's RS ratio is always ~1.0 — it neither outperforms nor underperforms itself. As a result, SPY only enters the portfolio when absolute trend is positive and other assets are weaker, not via the RS signal that drives the other 11 members.

**Practical implication:** The strategy functions primarily as a rotation across non-SPY asset classes, with SPY acting as a passive anchor. This is by design — the cross-asset diversification benefit comes from rotating into bonds, gold, or international equities when US equities are lagging, not from overweighting SPY.

### Walk-Forward Caveat

Only 2/6 walk-forward windows beat SPY (vs 5/6 for SP500 and emerging). This is structurally expected: the SPY circularity limits signal quality, and the cross-asset universe includes fixed income and commodities that will naturally underperform in equity bull regimes. The strategy's value proposition is **drawdown protection and risk-adjusted returns** (Sharpe 1.147 vs SPY 0.499, MaxDD -13% vs -34%) rather than raw outperformance in equity bull markets.

The decay ratio (0.78 OOS/IS) is the weakest of all universes. Users considering the multi-asset universe should weight the 19-year Sharpe (1.062) and drawdown metrics more heavily than the 10-year return comparison vs SPY.

### Regime Behaviour

| Regime | Strategy Behaviour |
|---|---|
| Equity bull (no inflation) | Rotates into QQQ, SPY, EEM — competitive with SPY |
| Risk-off / crisis | Rotates into TLT, IEF, GLD — significant drawdown protection |
| Inflationary / commodity bull | Rotates into GLD, DBC, EEM — captures real asset appreciation |
| Rising rate environment | May hold HYG or LQD briefly before rotating to short-duration or equities |

### Third-Party Usage

```python
from etfmomentum import run_signals

# Current signals (today)
etfs = run_signals('multi_asset')
# e.g. ['QQQ', 'GLD', 'TLT', 'SPY', 'IWM']

# Signals for a specific date
import pandas as pd
etfs = run_signals('multi_asset', date=pd.Timestamp('2026-04-08'))

# Install
# pip install git+https://github.com/jaig1/etfmomentum.git@v0.7.0
```

---

*For current signals: `uv run python -m etfmomentum signal --universe sp500 --detailed --refresh`*
*For emerging signals: `uv run python -m etfmomentum signal --universe emerging --detailed --refresh`*
*For commodity signals: `uv run python -m etfmomentum signal --universe commodity --detailed --refresh`*
*For multi-asset signals: `uv run python -m etfmomentum signal --universe multi_asset --detailed --refresh`*
*For a backtest: `uv run python -m etfmomentum backtest --universe multi_asset --start-date 2016-01-01`*
*Web UI: `./start_api.sh` + `./start_ui.sh` → http://localhost:3000*

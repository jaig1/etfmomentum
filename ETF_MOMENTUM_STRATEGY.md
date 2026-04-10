# ETF Momentum Strategy — Comprehensive Overview

*Last updated: April 10, 2026 | Version: 0.2.0*

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

---

## 1. Strategy Concept

The ETF Momentum Strategy is a **relative strength sector rotation** system. It holds a concentrated portfolio of the top-performing S&P 500 sector ETFs at any point in time, rotating monthly (or weekly) into whichever sectors are showing the strongest momentum relative to the broad market.

The core insight is that sector performance trends. Energy leads for multi-year cycles. Technology dominates during earnings-driven expansions. Utilities and healthcare outperform in risk-off environments. By systematically identifying which sectors are leading and concentrating capital there — while exiting laggards — the strategy aims to compound returns significantly above a buy-and-hold SPY approach.

**What makes it different from simple sector picking:**
- Signals are rules-based and systematic, not discretionary
- Both *relative* strength (vs SPY) and *absolute* trend are required to enter a position
- Three independent defensive layers protect capital during drawdowns
- The universe is narrow (12 ETFs) and sector-level, keeping transaction costs and complexity low

---

## 2. Core Mechanism

### Signal Generation

At each rebalance date the strategy calculates two filters for every ETF in the universe:

**Filter 1 — Relative Strength (RS Ratio)**
- RS = (ETF price / SPY price), normalized to a base of 1.0
- Rate of Change (ROC) of the RS ratio over 63 days (3 months)
- Positive ROC means the ETF is outperforming SPY on a trend basis

**Filter 2 — Absolute Trend (SMA)**
- ETF price must be above its 210-day (10-month) simple moving average
- This prevents buying into downtrending sectors regardless of relative strength
- Sectors in absolute downtrends are excluded even if they're "the best of a bad bunch"

**Portfolio Construction**
- ETFs that pass both filters are ranked by their RS ROC (descending)
- Top 3 are selected for equal-weight allocation
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

## 4. Defensive Layers

Three mechanisms provide capital protection, operating at different timescales and triggers:

```
Rebalance Signal
     │
     ├── [1] Volatility Regime Check
     │         Adjust N holdings and SPY floor based on current market vol
     │
     ├── [2] SGOV Momentum Check
     │         Replace any ETF where ROC < SGOV ROC with cash equivalent
     │
     └── Portfolio Set for Month
               │
               └── Daily Price Check
                         [3] Stop-Loss: exit any position down 5% from entry → SGOV
```

These three layers are additive and independent. The portfolio can simultaneously be in "high vol mode" (from layer 1), have one position replaced by SGOV (layer 2), and trigger an intraday stop-loss on another position (layer 3).

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

Three universes were tested with the optimized parameters:

| Universe | ETFs | Return vs SPY | Notes |
|---|---|---|---|
| S&P 500 Sectors | 12 | +100% (10yr) | Best performer |
| Developed Markets | Various | -134% | Underperforms |
| Emerging Markets | Various | -85% | Underperforms |

**Why S&P 500 sectors dominate:**
- Lower correlation between sector ETFs than country ETFs
- Sector performance is more differentiated and trend-following
- Internally diversified (each sector ETF = dozens of stocks)
- Deep liquidity and long data history

**Conclusion:** Focus exclusively on S&P 500 sector rotation. The developed and emerging market universes do not benefit from the same momentum dynamics.

---

## 7. Current Performance

### Optimized Parameters (v0.2.0)

```python
TOP_N_HOLDINGS = 3
SMA_LOOKBACK_DAYS = 210       # 10 months
RS_ROC_LOOKBACK_DAYS = 63     # 3 months
REBALANCE_FREQUENCY = "monthly"
CASH_TICKER = "SGOV"
STOP_LOSS_THRESHOLD = 0.95    # 5% stop
ENABLE_VOLATILITY_REGIME_SWITCHING = True  # (optional, used with weekly)
```

### 10-Year Summary (2016–2026, 11 sectors)

| | Baseline | Optimized | Improvement |
|---|---|---|---|
| Return | 270.81% | 341.37% | +70.56 pp |
| Sharpe | 0.574 | 0.656 | +14.2% |
| Final Value | $374k | $441k | +$66k |
| Rank (of 48) | 24 | 1 | — |

### 19-Year Summary (2007–2026, 12 sectors incl. SMH)

| Metric | Strategy | SPY |
|---|---|---|
| Total Return | 4,745% | 366% |
| Annualized | 22.36% | 8.34% |
| Sharpe | 0.929 | 0.277 |
| Max Drawdown | -28.48% | -56.47% |
| $100k → | $4.85M | $466k |

### Current Signal (April 2026)

System has rotated out of SMH/XLK (semiconductor/tech) into defensive sectors: **XLE (Energy), XLB (Materials), XLU (Utilities)** — reflecting the risk-off, tariff-uncertainty environment of early 2026.

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
| `signal_generator.py` | Live signal generation with SGOV check |
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

### ETF Universe (sp500_sector_etfs.csv)

12 ETFs: XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLU, XLRE, XLC, **SMH**

XLRE and XLC are gracefully skipped for pre-inception dates with warnings only.

---

## 9. Caveats and Risks

### Backtest Limitations

**Overfitting:** 48 combinations were tested on the same dataset. Walk-forward validation and out-of-sample testing have not been completed. The tight clustering of top results reduces (but does not eliminate) this concern.

**Survivorship bias:** The ETF universe was constructed with knowledge of which sectors exist today. Some ETFs did not exist at the start of the backtest period (XLC from 2018, XLRE from 2015).

**Market regime dependency:** Parameters were optimized on 2016–2026, a period that included a significant bull market. The 2008 crisis is covered in the 19-year test and the strategy performed well, but prolonged bear markets with different sector dynamics could stress the parameters.

### Concentration Risk

A 3-position portfolio has higher idiosyncratic volatility than a 5–10 position portfolio. While this was optimal on a risk-adjusted basis historically, individual sector blowups (e.g., energy in 2014–2015, financials in 2008) can cause short-term pain before the stop-loss or rebalance exits the position.

### Implementation Costs

- Bid-ask spreads and commissions are not modeled
- Large position sizes in less-liquid ETFs may cause slippage
- Monthly rebalancing keeps transaction costs low in practice

### SMH-Specific Risk

SMH's addition dramatically improved historical performance due to the 2024–2025 AI/semiconductor bull run. If the semiconductor cycle mean-reverts sharply, SMH will rotate out via the momentum signal — but the historical backtest result is partially a reflection of favorable timing for this specific addition.

---

*For current signals: `uv run python -m etfmomentum signal --universe sp500 --detailed --refresh`*
*For a backtest: `uv run python -m etfmomentum backtest --universe sp500 --start-date 2007-01-01`*
*Web UI: `./start_api.sh` + `./start_ui.sh` → http://localhost:3000*

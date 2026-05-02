# Architecture Decision Records

Settled design decisions for the etfmomentum package. Each entry records what was tried, the data behind the decision, and what it would take to re-open the question. **Do not re-open a decision without first reading its entry and meeting the re-open threshold.**

---

## ADR-001 — Fixed 5% Stop-Loss (not ATR-based)

**Status:** Accepted
**Decided:** April 10, 2026

### Decision
Use a fixed 5% stop-loss (`STOP_LOSS_THRESHOLD = 0.95`) rather than a volatility-adjusted ATR-based stop.

### What was tried
ATR-based stop (2.5×ATR(20) below entry) was proposed on the grounds that a fixed 5% stop on high-beta sectors like SMH constitutes "noise" and causes whipsaws.

A 10yr backtest (2016–2026) was run with custom instrumentation tracking every stop event and checking price recovery at the next rebalance.

| Metric | Result |
|---|---|
| Total stop events | 46 |
| Whipsaws (price > entry at next rebalance) | **0 / 46 (0%)** |
| Avg drop at stop trigger | -6.4% from entry |
| Avg price at next rebalance vs entry | -5.9% (still down) |

SMH specifically accounted for 14/46 stops. All 14 recovered further downward (avg -6.5% vs entry at next rebalance).

### Why rejected
There is no whipsaw problem to solve. Every stop that fired was a genuine loss cutter. ATR-based stops would:
- Add a new overfitting surface (ATR multiplier)
- Widen stops on high-beta sectors in exactly the crashes where protection matters most
- Add complexity to an already multi-layered defensive system

### Re-open threshold
Re-run whipsaw analysis on current data. If whipsaw rate rises above ~10% (5+ whipsaws per 50 stops), the case for a wider stop deserves review. Do not re-open based on intuition alone.

---

## ADR-002 — Keep Short Book Open During Breadth Filter

**Status:** Accepted
**Decided:** April 15, 2026 (v0.11.0, reversal of original v0.10.0 behaviour)

### Decision
The short book stays open unconditionally during low-breadth (defensive) periods. The breadth filter only affects the long side.

### What was tried
v0.10.0 closed all short positions when the breadth filter triggered (< 40% of sectors above SMA). Rationale: defensive mode = reduce all exposure.

v0.11.0 reversed this. Results on emerging 19yr backtest:

| Metric | v0.10.0 (closes shorts) | v0.11.0 (keeps shorts) |
|---|---|---|
| Sharpe | 2.436 | **2.778** |
| Ann Return | 44.17% | **53.75%** |
| Max Drawdown | -8.35% | -8.12% |
| Short activation | 67% | **100%** |

### Why
Low-breadth regimes mean broad systemic weakness — most ETFs are already below their SMA. This is precisely when laggard ETFs fall hardest. Closing shorts during defensive periods was leaving the most significant short alpha unrealised.

### Re-open threshold
Only if a future period shows that keeping shorts open during a breadth-triggered period caused a large loss (short squeeze during a panic-driven reversal). Review the activation data first.

---

## ADR-003 — Breadth Filter: SP500 Only, Not Cross-Universe

**Status:** Accepted
**Decided:** April 2026 (v0.16.0–v0.18.0, per-universe flag added)

### Decision
The breadth filter is enabled only for the `sp500` universe. All other universes (`emerging`, `developed`, `commodity`) have `enable_breadth_filter: False` in `UNIVERSE_PARAMS`.

### Rationale
The SP500 breadth signal uses the same 12 ETFs being traded — it is a direct health check of the portfolio universe itself. For other universes, the signal is calculated from those same 12 sector ETFs (not from the traded ETFs), making it an indirect proxy that adds friction without the same informational edge.

More specifically, universes with high-activation short books (95–100%) already hedge what the breadth filter was delivering. Disabling the filter for those universes improved or matched Sharpe in all cases:

| Universe | With Filter | Without | Delta |
|---|---|---|---|
| Emerging (10yr Sharpe) | 2.514 | **2.765** | +0.251 |
| Commodity (10yr Sharpe) | 2.194 | **2.252** | +0.058 |
| Developed (10yr Sharpe) | 1.440 | 1.439 | flat |

### Re-open threshold
If a new universe is added and its short activation falls below ~50%, the breadth filter should be evaluated for that universe before defaulting it to off.

---

## ADR-004 — SP500 Uses In-Sample Parameters (Not Walk-Forward Consensus)

**Status:** Accepted (known risk)
**Decided:** April 10, 2026

### Decision
SP500 production config uses in-sample optimised parameters (SMA=10mo, ROC=3mo, TopN=3) rather than the walk-forward consensus (SMA=8mo, ROC=1mo, TopN=10).

### Walk-Forward Results (SP500, 6 windows)

| Window | Test Period | WF Best Params | OOS Sharpe | vs SPY |
|---|---|---|---|---|
| 1 | 2014–2015 | SMA=6mo, ROC=3mo, N=7 | 0.065 | -1.7pp |
| 2 | 2016–2017 | SMA=6mo, ROC=3mo, N=7 | 0.863 | -6.2pp |
| 3 | 2018–2019 | SMA=8mo, ROC=1mo, N=10 | 0.996 | +8.0pp |
| 4 | 2020–2021 | SMA=8mo, ROC=1mo, N=10 | 1.735 | +21.2pp |
| 5 | 2022–2023 | SMA=8mo, ROC=1mo, N=10 | 0.263 | +15.2pp |
| 6 | 2024–2026 | SMA=12mo, ROC=3mo, N=3 | 1.575 | +34.4pp |

WF consensus: SMA=8mo, ROC=1mo, TopN=10. The in-sample params (SMA=10mo, ROC=3mo, TopN=3) were not selected in any window.

### Why in-sample params are kept
1. The WF consensus TopN=10 contradicts the clear in-sample finding that concentration (TopN=3) outperforms diversification. TopN=10 for 11-sector universe is essentially equal-weight — degrades to an index strategy.
2. OOS/IS decay ratio of 1.46 is inflated (OOS periods happened to be more favorable than IS training periods which include 2008). Don't over-read the WF consensus.
3. The 10yr in-sample baseline (Sharpe 1.266) is validated and production-locked. Switching to WF params has not been tested.

### Known risk
If market regime shifts to favour broader diversification, in-sample params may underperform WF consensus. The walk-forward evidence suggests ROC=1mo may generalise better than ROC=3mo across regimes.

### Re-open threshold
If SP500 universe underperforms SPY for 2+ consecutive walk-forward windows, re-run optimizer and compare in-sample vs WF consensus on new data before changing.

---

## ADR-005 — Weekly Rebalancing Over Monthly

**Status:** Accepted
**Decided:** Early 2026

### Decision
`REBALANCE_FREQUENCY = "weekly"`. Monthly rebalancing was also tested.

### Data
| Frequency | Return | Sharpe | Notes |
|---|---|---|---|
| Weekly | Higher | Higher | Especially dramatic for commodity universe |
| Monthly | Lower | Lower | First trading day of month |

Weekly rebalancing captures faster momentum rotations and responds to stop-loss exits more quickly. The benefit is most pronounced in commodity (high turnover by nature) and emerging (sharp country-level moves).

### Re-open threshold
If transaction costs become a concern (real-money implementation with large AUM), monthly rebalancing should be re-evaluated with explicit cost modelling. At small AUM, weekly dominates.

---

## ADR-006 — Momentum Quality over Raw ROC for Ranking

**Status:** Accepted
**Decided:** April 2026 (v0.3.0)

### Decision
ETFs are ranked by **Momentum Quality** (`RS_ROC / StdDev(RS ratio returns, 63d)`) rather than raw RS ROC.

### What was tried
Original ranking: raw 3-month RS ROC. Replacement: information ratio of the RS trend (how much outperformance per unit of RS volatility).

### Why
A sector that gaps up 20% in one day scores lower than one that trends up steadily over 3 months. Smooth, persistent trends are historically more likely to continue; erratic movers suffer more momentum crashes. The change improved Sharpe and tightened MaxDD across all universes tested.

### Re-open threshold
Do not change without a full 10yr + 19yr comparison showing the raw ROC alternative beats momentum quality on both Sharpe and MaxDD.

---

## ADR-007 — SGOV Cash Equivalent with BIL Proxy Pre-Inception

**Status:** Accepted
**Decided:** April 10, 2026

### Decision
`CASH_TICKER = "SGOV"`. Pre-2020-06-12 (SGOV inception), automatically backfilled with BIL (iShares 1-3 Month Treasury, launched Jan 2007) inside `data_fetcher.fetch_all_data()`. Callers are unaware.

### Why this matters
Without the proxy, SGOV had NaN prices for the entire 2007–2020 period. When stop-loss or SGOV protection triggered pre-2020, portfolio calculations were silently corrupted. The fix halved the reported MaxDD for 19yr backtests (from -28% to -14%) and increased Sharpe (from 0.930 to 0.973) by providing valid cash return data.

### Re-open threshold
Do not change to a different cash proxy without verifying inception date coverage from 2007. If SGOV itself is replaced, the proxy logic in `data_fetcher.py` must be updated.

---

## ADR-008 — Top20 Universe: Live TOPT API (Not Static CSV)

**Status:** Accepted
**Decided:** April 26, 2026 (v0.19.0)

### Decision
Top20 holdings are fetched live from `FMP /api/v3/etf-holder/TOPT` on every signal and backtest call. The static `etflist/top20_stock.csv` was removed.

### Why
Any static holdings snapshot for a mega-cap universe introduces look-ahead bias: the snapshot captures holdings as of today, not as of each historical backtest date. Backtests from 2016 using today's TOPT constituents (which themselves reflect 10 years of survivorship and index evolution) are invalid.

The prior published numbers (10yr Sharpe 2.849, Ann 96.45%) were generated this way and are **permanently superseded**. Only the bias-free 16-month track (Oct 2024–Mar 2026, Sharpe 3.394) is valid.

### Constraints
- Backtest clamped to TOPT inception 2024-10-24 — earlier dates raise a warning and are refused.
- Raises `RuntimeError` on API failure — no silent fallback to stale data.

### Re-open threshold
Only if FMP discontinues the TOPT ETF holder endpoint. In that case, a time-series of historical holdings would be needed before backtesting can be re-enabled for earlier periods.

---

## ADR-009 — Short Sleeve: 3% Stop-Loss Across All Universes

**Status:** Accepted
**Decided:** April 2026 (v0.10.0–v0.15.0)

### Decision
All short positions use `stop_loss = 1.03` (cover if price rises 3% above entry). This was independently confirmed decisive across emerging, commodity, SP500, and developed.

### Sensitivity data (72-combo grid, 10yr)

| Universe | Avg Sharpe @ 3% | Avg Sharpe @ 5% | Avg Sharpe @ 10% |
|---|---|---|---|
| SP500 | 1.488 | 1.375 | 1.267 |
| Commodity | 2.061 | ~1.900 | 1.850 |
| Developed | 1.296 | 1.153 | — |

Across all universes: tight stop (3%) is best. Short positions that reverse quickly (short squeezes, news) need to be exited fast. Loose stops let small reversals become large losses.

### Re-open threshold
If a universe with fundamentally different volatility characteristics (e.g. very low-vol bond shorts) is added, re-run the sensitivity analysis for that universe specifically.

---

## ADR-010 — FastAPI Route Does Not Call `run_signals()`

**Status:** Accepted (known technical debt)
**Decided:** Architecture predates unified pipeline (pre-v0.5.0)

### Decision
`api/routes/signals.py` reimplements signal selection directly using internal modules rather than calling `run_signals()`. It does not apply: breadth filter, SGOV protection, momentum quality ranking, or short signals.

### Why not fixed
The route was built before the `_compute_tickers()` unified pipeline existed (v0.5.0). Routing through `run_signals()` would change the behaviour visible in the React UI and requires deliberate testing and decision.

### Re-open threshold
This is the right thing to fix eventually — the UI should reflect the live strategy. When addressing it, replace the route's internal reimplementation with a call to `run_signals()` and `run_short_signals()`, update `SignalResponse` to include short signals, and test the UI end-to-end. Confirm with the user before starting.

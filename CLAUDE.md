# CLAUDE.md — ETF Momentum Strategy

Instructions for AI assistants working on this codebase. **Read this before making any changes.**

---

## Project Identity

- **Package:** `etfmomentum` — systematic ETF relative-strength rotation strategy
- **Version:** v0.19.0 (current as of April 26, 2026)
- **Status:** Production-ready. Remote fully synced (main + tags v0.5.0–v0.19.0 pushed).
- **Install (external users):** `pip install git+https://github.com/jaig1/etfmomentum.git@v0.19.0`

---

## Tech Stack

| Layer | Tool |
|---|---|
| Runtime | Python 3.11+ |
| Package manager | `uv` (all commands use `uv run`) |
| Build backend | `hatchling` (pyproject.toml) |
| Data source | Financial Modeling Prep (FMP) API — key in `.env` as `FMP_API_KEY` |
| CLI | `python -m etfmomentum` or `etfmomentum` after install |
| API backend | FastAPI (`api/`) |
| UI | React (`ui/`) |

**Run anything with `uv run`, not `python` directly.**

---

## Architecture & Module Map

```
etfmomentum/
├── etfmomentum/          # Core package
│   ├── config.py         # All parameters: UNIVERSE_PARAMS, SHORT_UNIVERSE_PARAMS, global flags
│   ├── data_fetcher.py   # FMP API + BIL proxy backfill for SGOV pre-inception
│   ├── rs_engine.py      # RS ratio, SMA, ROC, momentum quality, breadth filter, short candidates
│   ├── backtest.py       # Portfolio simulation: stop-loss + short sleeve execution
│   ├── signal_generator.py  # run_signals() and run_short_signals() — the public API; _compute_tickers() unified pipeline
│   ├── optimizer.py      # 48-combo long-side grid search
│   ├── short_optimizer.py   # 72-combo short sleeve grid search
│   ├── walk_forward.py   # Walk-forward validation (6 windows)
│   ├── volatility_regime.py # Regime detection and adaptive allocation
│   ├── etf_loader.py     # load_universe_by_name() — routes to FMP API for top20 or CSV for others
│   └── main.py           # CLI entry point
├── api/                  # FastAPI backend
├── ui/                   # React frontend
├── etfmomentum/etflist/  # ETF universe CSV definitions (bundled in package via importlib.resources)
├── data/                 # Price data cache (gitignored)
├── output/               # Backtest results (gitignored)
├── thirdparty/           # Third-party integration example
├── pyproject.toml        # Build config (hatchling); version must be updated on each release
└── ETF_MOMENTUM_STRATEGY.md  # Full strategy doc (source of truth for strategy logic)
```

---

## Public API

The **only** stable public interface is:

```python
from etfmomentum import run_signals, run_short_signals

# Long signals — list of tickers to hold
tickers = run_signals('sp500')      # e.g. ['XLK', 'XLF', 'XLC']
tickers = run_signals('emerging')   # e.g. ['ARGT', 'INDA', 'SGOV']

# Short signals — list of tickers to short (empty list for non-enabled universes)
shorts = run_short_signals('emerging')  # e.g. ['KWEB', 'MCHI', 'FXI']
```

Both functions fetch fresh FMP data on every call and run the full signal pipeline. No other functions in `signal_generator.py` or elsewhere are part of the public API — do not expose or document internal helpers to external callers.

---

## Common Commands

```bash
# Signal generation (current week)
uv run python -m etfmomentum signal --universe emerging --detailed --refresh
uv run python -m etfmomentum signal --universe sp500

# Backtesting
uv run python -m etfmomentum backtest --universe emerging --start-date 2016-01-01
uv run python -m etfmomentum backtest --universe sp500 --start-date 2007-01-01  # 19yr

# Optimization
uv run python -m etfmomentum short-optimize --universe emerging

# Walk-forward validation
uv run python -m etfmomentum walk-forward --universe sp500

# Start API + UI
./start_api.sh   # FastAPI at http://localhost:8000
./start_ui.sh    # React at http://localhost:3000
```

---

## MANDATORY: Change Protocol

**Any change to signal logic, ranking, defensive layers, or UNIVERSE_PARAMS must follow this protocol. No exceptions.**

1. **Discuss first** — explain the change, files touched, and any architectural concerns before writing code.
2. **Feature branch** — implement on `feature/<name>`; `main` stays clean as the rollback.
3. **Run all three tests:** 10yr backtest, 19yr backtest, walk-forward validation.
4. **Compare against locked baselines** (see section below).
5. **Regression thresholds** — flag (do not auto-merge) if any of:
   - Annualized return drops > 1pp
   - Sharpe drops > 0.05
   - MaxDD worsens > 2pp (flag for user decision — not auto-fail)
6. **Decision:** if pass → merge + delete branch. If fail → `git checkout main && git branch -D feature/x`.

Walk-forward is **required**, not optional.

---

## Validated Baselines (Locked — April 25, 2026)

These numbers are the reference for regression testing. Do not treat them as aspirational — they are the production floor.

| Universe | Period | Return | Ann | Sharpe | MaxDD |
|---|---|---|---|---|---|
| SP500 long-only | 10yr (2016–) | 769% | 23.51% | 1.266 | -11.83% |
| SP500 long-only | 19yr (2007–) | 2,531% | 18.53% | 0.991 | -13.03% |
| SP500 + Short (v0.13.0) | 10yr | 1,254% | 29.33% | **1.661** | -8.09% |
| SP500 + Short (v0.13.0) | 19yr | 7,501% | 25.42% | **1.415** | -8.52% |
| Commodity long-only | 10yr | 5,204% | 47.38% | 1.861 | -10.67% |
| Commodity + Short (v0.17.0) | 10yr | 12,023% | 60.57% | **2.252** | -10.56% |
| Commodity + Short (v0.17.0) | 19yr | 242,096% | 50.30% | **2.076** | -10.56% |
| Emerging + Short (v0.18.0) | 10yr | 9,427% | 56.80% | **2.765** | -9.10% |
| Emerging + Short (v0.18.0) | 19yr | 428,974% | 54.87% | **2.587** | -10.02% |
| Developed + Short (v0.16.0) | 10yr | 686% | 22.57% | **1.439** | -8.47% |
| Developed + Short (v0.16.0) | 19yr | 8,796% | 26.45% | **1.517** | -13.31% |
| Top20 (v0.19.0) | 16mo (Oct 2024–Mar 2026) | 195.59% | 125.43% | **3.394** | -8.92% |
| Multi-Asset | 10yr | 470% | 18.54% | 1.147 | -13.05% |
| Factor | 10yr | 258% | 13.27% | 0.716 | -20.37% |
| Bond | 10yr | 127.5% | 8.36% | 0.477 | -18.61% |

**Top20 note:** Prior 10yr/19yr numbers (Sharpe 2.849 / 2.821) used static holdings — look-ahead biased, **permanently superseded**. Only the 16-month bias-free track is valid.

---

## Strategy Parameters

All parameters live in `etfmomentum/config.py`. Do not hardcode values in other modules — always read from config.

### Global Parameters
```python
REBALANCE_FREQUENCY = "weekly"
CASH_TICKER = "SGOV"           # backfilled with BIL pre-2020-06-12
STOP_LOSS_THRESHOLD = 0.95     # 5% stop
ENABLE_BREADTH_FILTER = True
BREADTH_FILTER_THRESHOLD = 0.40
BREADTH_CASH_ALLOCATION = 0.5
ENABLE_SHORT_SELLING = True
SHORT_ENABLED_UNIVERSES = ['emerging', 'commodity', 'sp500', 'developed']
```

### UNIVERSE_PARAMS (per-universe SMA / ROC / TopN)
```python
# sp500:       SMA=210d(10mo), ROC=63d(3mo),  TopN=3, breadth_filter=True (default)
# emerging:    SMA=252d(12mo), ROC=21d(1mo),  TopN=3, breadth_filter=False
# developed:   SMA=168d(8mo),  ROC=21d(1mo),  TopN=3, breadth_filter=False
# commodity:   SMA=126d(6mo),  ROC=126d(6mo), TopN=3, breadth_filter=False
# multi_asset: SMA=126d(6mo),  ROC=63d(3mo),  TopN=5
# factor:      SMA=210d(10mo), ROC=21d(1mo),  TopN=3
# bond:        SMA=126d(6mo),  ROC=63d(3mo),  TopN=10
# top20:       SMA=126d(6mo),  ROC=126d(6mo), TopN=5
```

### SHORT_UNIVERSE_PARAMS
```python
# emerging:  top_n=3, allocation=0.33, stop_loss=1.03, qualification=momentum_quality_only
# commodity: top_n=2, allocation=0.33, stop_loss=1.03, qualification=both_filters
# sp500:     top_n=1, allocation=0.33, stop_loss=1.03, qualification=both_filters
# developed: top_n=1, allocation=0.33, stop_loss=1.03, qualification=both_filters
```

**SP500 in-sample params (SMA=10mo, ROC=3mo) differ from walk-forward consensus (SMA=8mo, ROC=1mo, TopN=10). In-sample params are in production — do not change without protocol.**

---

## Key Research Findings (Do Not Revisit Without Strong Reason)

These questions are settled. Don't re-open them without a specific hypothesis.

1. **Momentum quality beats raw ROC** — risk-adjusted momentum (ROC/StdDev) rewards smooth trends.
2. **Breadth filter is a leading indicator** — fires before vol spikes; tightens MaxDD while improving returns. Applies to sp500 only (see #14).
3. **Concentration beats diversification** — TopN=3 outperforms TopN=5+ for most universes.
4. **ROC lookback is universe-specific** — SP500: 3mo; emerging/developed: 1mo; commodity: 6mo.
5. **Weekly rebalancing beats monthly** — especially dramatic for commodities.
6. **Stop-loss whipsaw non-issue** — 0/46 whipsaws in 10yr backtest; fixed 5% stop working correctly.
7. **Short sleeve adds alpha on both sides** — persistent laggards in emerging (100% activation) and commodity (95%).
8. **Keep shorts open during breadth filter** — low-breadth regimes are best time to hold shorts; closing leaves alpha unrealised.
9. **Commodity short: top_n=2, not 3** — smaller universe (10 ETFs) with high DBC correlation; stop=3% is critical.
10. **SP500 short: top_n=1** — single worst sector cleaner than top 2-3 in 12-ETF universe.
11. **Developed short: top_n=1, 3% stop decisive** — 26 country ETFs highly correlated; WF decay 0.57 (weakest short sleeve).
12. **Breadth filter works for SP500 only** — commodity/emerging/developed: high-activation short book already hedges what breadth filter was delivering; per-universe `enable_breadth_filter` flag in UNIVERSE_PARAMS.
13. **Multi-asset SPY circularity** — SPY is both benchmark and universe member; value is drawdown protection, not equity alpha.
14. **Top20 look-ahead bias** — static holdings snapshots are inherently biased; only live TOPT API call at signal time is valid. Backtest clamped to TOPT inception 2024-10-24.

---

## Universe Coverage

| Universe | Description | ETF Count |
|---|---|---|
| sp500 | 11 SPDR sector ETFs + SMH | 12 |
| emerging | 28 country/regional emerging market ETFs | 28 |
| developed | 26 iShares country ETFs | 26 |
| commodity | 10 commodity ETFs | 10 |
| multi_asset | 12 cross-asset ETFs (equities, bonds, commodities, real estate) | 12 |
| factor | 12 factor ETFs (value, growth, quality, momentum, size, low-vol) | 12 |
| bond | 12 bond duration/credit ETFs | 12 |
| top20 | Live TOPT ETF holdings via FMP API (TOPT inception 2024-10-24) | 20 |

ETF universe definitions live in `etfmomentum/etflist/*.csv` — bundled in the package via `importlib.resources` so they work after `pip install`.

**Top20 exception:** holdings are fetched live from `FMP /api/v3/etf-holder/TOPT` on every call (no CSV). CUSIP issuer deduplication applied (GOOG dropped; GOOGL kept). Raises `RuntimeError` on API failure — no silent fallback.

---

## Defensive Layers (in priority order)

1. **Absolute trend filter** — ETF below SMA → excluded from selection
2. **SGOV cash protection** — any top-N holding with ROC < SGOV ROC → replaced with SGOV
3. **Breadth filter** — < 40% of SP500 sector ETFs above SMA → reduce to 1 holding + 50% SGOV
4. **Stop-loss** — 5% stop per position; triggered positions move to SGOV until next rebalance
5. **Short sleeve** — always-on short book of bottom-N ETFs; adds ≈ 33% gross short on top of 100% long

---

## Walk-Forward Validation Results

Walk-forward uses 6 expanding windows (anchor 2007-01-01, 2-year OOS periods). The **OOS/IS decay ratio** is the primary robustness indicator.

| Universe | Combined OOS Return | Avg OOS Sharpe | Decay Ratio | OOS windows beating benchmark |
|---|---|---|---|---|
| top20 | 24,470% | 2.320 | **0.99** | 6/6 |
| commodity | 978% | 1.000 | **0.93** | 5/6 |
| factor | 249% | 0.542 | **0.87** | 3/6 |
| sp500 | 576% | 0.891 | ~1.46* | 5/6 |
| multi_asset | 270% | 0.623 | 0.78 | 2/6 ⚠️ |
| bond | 169% | 0.330 | 0.58 | 0/6 ⚠️ (benchmark = AGG) |
| developed short | — | — | 0.57 | — ⚠️ |

*SP500 decay >1 because OOS periods (2014–2026) were more favorable than IS training periods (which include 2008). Do not over-read.

**Interpretation thresholds:**
- ≥ 0.85 = robust — parameters generalise well; high confidence
- 0.70–0.85 = moderate — usable but monitor; re-validate if regime shifts
- < 0.70 = weak — treat as complement/experimental, not standalone ⚠️

---

## Optimization Methodology

Follow this process exactly when adding a new universe or testing parameter changes.

### Long-side optimizer (48-combo grid)

```bash
uv run python -c "from etfmomentum.optimizer import optimize_parameters; optimize_parameters(universe='<name>', output_subdir='<name>')"
```

Grid searched: `sma_lookback_days × roc_lookback_days × top_n`
- SMA: [126, 168, 210, 252] days (6, 8, 10, 12 months)
- ROC: [21, 63, 126] days (1, 3, 6 months)
- TopN: [3, 5, 7, 10]  — 4×3×4 = 48 combinations

**What to look for:**
1. Top-3 combos clustered (Sharpe within 0.05 of each other) → robust; pick the middle
2. Top-3 combos spread > 0.1 Sharpe apart → sensitive; flag and discuss before locking
3. TopN sensitivity: if TopN=3 and TopN=10 tie, prefer 3 (concentration principle)
4. ROC sensitivity: if 1mo and 3mo tie, prefer the one that walk-forward confirms

### Walk-forward validation

```bash
uv run python -m etfmomentum walk-forward --universe <name>
```

Run after optimizer. Confirm:
- OOS/IS decay ratio ≥ 0.85 before calling parameters "production ready"
- WF consensus params (mode across 6 windows) match or align with IS optimal
- If IS optimal and WF consensus disagree significantly (especially on TopN), discuss with user before locking — see ADR-004 for the SP500 precedent

### Short sleeve optimizer (72-combo grid)

```bash
uv run python -m etfmomentum short-optimize --universe <name>
```

Grid: `top_n × allocation × stop_loss × qualification` — 3×3×4×2 = 72 combinations
- top_n: [1, 2, 3]
- allocation: [0.15, 0.25, 0.33]
- stop_loss: [1.03, 1.05, 1.07, 1.10]
- qualification: ['momentum_quality_only', 'both_filters']

Key sensitivities established across all universes (see ADR-009):
- 3% stop is decisive — do not change without explicit grid evidence
- top_n should be determined by universe size and correlation structure
- allocation is typically insensitive; 33% chosen for consistency

Always validate short sleeve on both 10yr and 19yr before merging.

---

## Open Methodology Issues

| Issue | Status | Impact |
|---|---|---|
| SGOV pre-inception proxy | ✅ Fixed — BIL backfill in `data_fetcher.py` | High |
| Look-ahead bias (same-day signal + execute) | Open | Moderate |
| Stop-loss gap handling | Open | Moderate |

---

## Files to Touch Per Operation

Use this as a checklist whenever you make a change. Missing any of these is the primary source of consistency failures.

### Public API signature change (`run_signals` / `run_short_signals`)
```
[ ] etfmomentum/signal_generator.py   — update function signature
[ ] etfmomentum/__init__.py           — update module docstring examples
[ ] LIBRARY_USAGE.md                  — update signature table + all code examples
[ ] thirdparty/thirdparty.py          — update usage example if relevant
[ ] CLAUDE.md (Public API section)    — update if semantics changed
```
Note: `api/routes/signals.py` does NOT call `run_signals()` — it reimplements signal logic directly (see "Known Technical Debt" section). Update it separately and intentionally, not as a side effect.

### Adding a new universe
```
[ ] etfmomentum/etflist/<universe>.csv  — new ETF list (or live API in etf_loader.py for dynamic holdings)
[ ] etfmomentum/etf_loader.py           — register in universe map
[ ] etfmomentum/config.py               — add to UNIVERSE_PARAMS with validated params
[ ] etfmomentum/main.py                 — add to CLI universe choices
[ ] api/models/schemas.py               — add to SignalRequest/BacktestRequest universe description
[ ] LIBRARY_USAGE.md                    — add to universe table
[ ] README.md                           — add to ETF Universes section
[ ] RELEASE_NOTES.md                    — new entry
[ ] ETF_MOMENTUM_STRATEGY.md            — add section + update UNIVERSE_PARAMS table
[ ] MEMORY.md + new memory file         — record validated parameters and performance
```
Always run: 48-combo optimizer → walk-forward → 10yr + 19yr backtest before merging.

### Enabling a short sleeve for a new universe
```
[ ] etfmomentum/config.py              — add to SHORT_ENABLED_UNIVERSES; add SHORT_UNIVERSE_PARAMS entry
[ ] RELEASE_NOTES.md                   — new entry with optimization summary + performance table
[ ] ETF_MOMENTUM_STRATEGY.md           — update short sleeve section + universe enablement table
[ ] MEMORY.md + new memory file        — record validated params and performance
```
Always run: 72-combo short_optimizer → 10yr + 19yr backtest. Consider whether to disable breadth filter (per-universe flag) — check the research finding in CLAUDE.md first.

### Changing UNIVERSE_PARAMS or SHORT_UNIVERSE_PARAMS
```
[ ] etfmomentum/config.py             — change the value
[ ] CLAUDE.md (Strategy Parameters)   — update the inline reference table
[ ] MEMORY.md                         — update validated baselines if numbers changed
[ ] RELEASE_NOTES.md                  — new entry
```
Requires full change protocol: feature branch + 10yr + 19yr + walk-forward.

### Release (version bump)
See the Release Checklist section below.

---

## Known Technical Debt

### `api/routes/signals.py` — bypasses the unified pipeline

The FastAPI `POST /signals` route **does not call `run_signals()`**. It reimplements signal selection directly using internal modules (`rs_engine.py`, `data_fetcher.py`). As a result it:
- Does not apply the breadth filter
- Does not apply SGOV cash protection
- Does not use momentum quality ranking (uses raw RS ROC instead)
- Does not support short signals

This is a known divergence, not an accident. The route was built before the unified `_compute_tickers()` pipeline existed. **Do not silently "fix" it** by routing through `run_signals()` — that is a behaviour change for the UI that requires intentional decision. If asked to align the FastAPI route with the strategy, confirm with the user first.

---

## Release Checklist (run every time a version is tagged)

Complete **all** steps before pushing the tag. No partial releases.

```
[ ] 1. pyproject.toml          — update `version = "X.Y.Z"`
[ ] 2. etfmomentum/__init__.py — update `__version__ = "X.Y.Z"`
[ ] 3. RELEASE_NOTES.md        — add entry at the TOP of the file (newest first)
                                  follow the existing format: Overview, What Changed,
                                  Validated Performance table, Files Changed, Installation snippet
[ ] 4. LIBRARY_USAGE.md          — update signature tables, universe table, performance table
[ ] 5. ETF_MOMENTUM_STRATEGY.md — update version line + any affected sections/tables
[ ] 6. Annotated git tag        — `git tag -a vX.Y.Z -m "...summary..."`
[ ] 7. Push tag                 — `git push origin vX.Y.Z`
[ ] 8. Update MEMORY.md         — reflect new version and any new performance numbers
[ ] 9. Update DECISIONS.md      — add a new ADR if this release reversed or extended a prior decision
```

**Version string must match in all four places:** `pyproject.toml`, `__init__.py`, the RELEASE_NOTES heading, and the git tag. A mismatch is a bug — `pip show etfmomentum` and `importlib.metadata.version('etfmomentum')` both read `pyproject.toml`.

---

## Key Documentation Files

| File | Audience | What to keep in sync |
|---|---|---|
| `CLAUDE.md` | Future Claude sessions | Rules, checklists, baselines, known debt, WF results, optimization methodology |
| `DECISIONS.md` | Future Claude sessions | Why each design decision was made; what was tried; re-open thresholds |
| `LIBRARY_USAGE.md` | External consumers / bots | Public API signatures, all 8 universes, performance table, rebalance pattern |
| `RELEASE_NOTES.md` | All users | Entry for every tagged version, newest first |
| `ETF_MOMENTUM_STRATEGY.md` | Strategy reference | Version line, UNIVERSE_PARAMS table, performance numbers, phase history |
| `README.md` | GitHub landing page | Universe list, install command, basic usage |

`LIBRARY_USAGE.md` is the primary reference for third-party integrators. It must match the actual `run_signals()` and `run_short_signals()` signatures exactly — stale signatures here are what generates external user feedback.

---

## Distribution & Versioning

- **Build:** `hatchling` via `pyproject.toml`. Update `version` in `pyproject.toml` **and** `__version__` in `etfmomentum/__init__.py` on every release.
- **Install (remote):** `pip install git+https://github.com/jaig1/etfmomentum.git@vX.Y.Z`
- **Install (local dev):** `pip install -e /Users/jaig/etfmomentum` or `uv pip install -e .`
- **Environment:** FMP_API_KEY required; set in `.env` or exported, **or** pass as `api_key=` to `run_signals()`/`run_short_signals()`. The key is resolved lazily — importing the package succeeds without it; the `ValueError` fires only at call time if neither the parameter nor the env var is set.
- **etflist/ packaging:** Universe CSVs are bundled using `importlib.resources` so they resolve correctly both from source and after `pip install`. Always use `ETFLIST_DIR = Path(importlib.resources.files("etfmomentum").joinpath("etflist"))` — never construct the path manually.
- **Tagging convention:** annotated tags (`git tag -a vX.Y.Z -m "..."`) pushed to origin.

---

## Known Bugs / Quirks

- **CLI top_n display for top20:** `main.py` defaults to global `TOP_N_HOLDINGS=3` and prints "Top N Holdings: 3" for top20. Actual backtest uses `UNIVERSE_PARAMS['top20']['top_n'] = 5` correctly. Use the programmatic API for correct top_n.
- **CLI top_n display for top20** is the only known display inconsistency remaining (see above).

---

## What NOT to Do

- Do not change `UNIVERSE_PARAMS` or `SHORT_UNIVERSE_PARAMS` values without the full change protocol.
- Do not add new universes to `SHORT_ENABLED_UNIVERSES` without a 72-combo grid search + 10yr/19yr validation.
- Do not re-use static holding snapshots for top20 backtests — always use the live TOPT API.
- Do not expose internal signal functions in `__all__` — only `run_signals` and `run_short_signals` are the public API.
- Do not use `python` directly — always use `uv run python -m etfmomentum` for consistency.
- Do not create new output files in `data/` or `output/` — these are gitignored scratch dirs.

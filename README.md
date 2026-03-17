# ETF Momentum - Relative Strength Framework

A Python-based system for **backtesting** and **generating live signals** using a Relative Strength (RS) momentum rotation strategy across multiple ETF universes.

## Overview

This framework implements a **quantitative momentum strategy** with advanced optimization and regime-switching capabilities:
- Ranks ETFs by relative strength vs SPY
- Applies dual momentum filters (relative + absolute trend)
- Selects top performers for portfolio construction
- **Parameter-optimized** through grid search (48 combinations tested)
- **Volatility regime switching** for adaptive allocation
- **Weekly rebalancing** with conditional trading
- Supports both historical backtesting and live signal generation
- Works with 3 different ETF universes (48 total ETFs)

**Optimized Strategy Performance (10-year backtest 2016-2026):**
- **S&P 500 Sectors (Optimized + Weekly):** +378% total return (+137% vs SPY), Sharpe 0.700
- **S&P 500 Sectors (Optimized Monthly):** +341% total return (+100% vs SPY), Sharpe 0.656
- **Baseline (Before Optimization):** +270% total return (+29% vs SPY), Sharpe 0.574
- SPY Benchmark: +241% total return, Sharpe 0.951

**YTD 2026 Performance (Jan 1 - Mar 16, 2026):**
- **S&P 500 Sectors:** +9.77% (+11.75% vs SPY), Sharpe 3.156, Max DD -4.87%
- **SPY Benchmark:** -1.98%, Sharpe -1.268
- **Current Holdings (as of Mar 16, 2026):**
  - SP500: XLE (Energy), XLU (Utilities), XLB (Materials) - 33% each

---

## Quick Start for Future Sessions

When starting a new session with Claude:

1. **Tell Claude**: "This is the ETF momentum project at `/Users/jaig/etfmomentum`. Read the README."
2. **Ask for what you need**:
   - "Run signals for S&P 500 sectors"
   - "Run backtest for emerging markets"
   - "Generate signals for all three universes"

Claude will read this file and understand the project structure and commands.

---

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Install dependencies
uv sync
```

### API Key Setup

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Add your Financial Modeling Prep API key:
```
FMP_API_KEY=your_api_key_here
```

Get your API key at: https://financialmodelingprep.com/developer/docs/

**Note**: This project uses FMP **stable** endpoints (not v3) and works with premium plans (3000 calls/min, 30 years of data).

---

## Usage

The framework provides both a **Web UI** and **CLI** interface for backtesting and signal generation.

### Web UI (Recommended)

The React-based web interface provides an intuitive way to interact with the strategy:

```bash
# Start API server (Terminal 1)
./start_api.sh

# Start React UI (Terminal 2)
./start_ui.sh
```

Access the application:
- **UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**Features:**
- **Dashboard**: View YTD performance, current holdings, portfolio metrics
- **Signals**: Generate buy/sell/hold recommendations with rebalancing actions
- **Backtest**: Run historical simulations with customizable date ranges

**API Endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Get configuration
curl http://localhost:8000/api/config

# Dashboard data
curl "http://localhost:8000/api/dashboard?universe=sp500"

# Test UI screens (requires Playwright)
cd ui && node test_ui_screens.js
```

---

### CLI Interface

#### Signal Generation (Most Common Use Case)

Generate current month portfolio recommendations:

```bash
# S&P 500 Sector ETFs (recommended - best performer)
uv run python -m etfmomentum signal --universe sp500 --refresh

# Developed Market ETFs
uv run python -m etfmomentum signal --universe developed --refresh

# Emerging Market ETFs
uv run python -m etfmomentum signal --universe emerging --refresh

# Add --detailed flag for comprehensive ETF status report
uv run python -m etfmomentum signal --universe sp500 --detailed --refresh
```

**Always use `--refresh`** when generating signals to fetch the latest data.

### Backtesting

Run historical performance simulation:

```bash
# 10-year backtest (2016-2026) for S&P 500 sectors
uv run python -m etfmomentum backtest --universe sp500

# Backtest other universes
uv run python -m etfmomentum backtest --universe developed
uv run python -m etfmomentum backtest --universe emerging

# Force refresh data from API
uv run python -m etfmomentum backtest --universe sp500 --refresh
```

### Command Options

**Common flags (both modes):**
- `--universe {sp500|developed|emerging}` - **Required**: Select ETF universe
- `--refresh` - Force fetch fresh data from FMP API (bypasses cache)

**Backtest-specific:**
- `--top-n N` - Number of ETFs to hold (default: 3, optimized)
- `--initial-capital AMOUNT` - Starting capital (default: 100000)

---

## ETF Universes

The framework supports three distinct ETF universes defined in CSV files under `etflist/`:

### 1. S&P 500 Sector ETFs (`sp500_sector_etfs.csv`)
**11 SPDR sector ETFs** - Best historical performance
- XLK (Technology), XLF (Financials), XLE (Energy)
- XLV (Health Care), XLY (Consumer Discretionary), XLP (Consumer Staples)
- XLI (Industrials), XLB (Materials), XLRE (Real Estate)
- XLU (Utilities), XLC (Communication Services)

### 2. Developed Market ETFs (`developed_market_etfs.csv`)
**26 iShares country ETFs** covering major developed economies
- Countries: Japan, Germany, UK, Australia, Canada, France, Switzerland, Spain, Italy, Netherlands, Sweden, Belgium, Singapore, Hong Kong, Norway, Denmark, Finland, Ireland, Israel
- Includes small-cap and currency-hedged variants

### 3. Emerging Market ETFs (`emerging_market_etfs.csv`)
**28 country/regional ETFs** across Asia, LatAm, and EMEA
- Asia: China, India, Taiwan, South Korea, Malaysia, Indonesia, Thailand, Philippines, Vietnam
- LatAm: Brazil, Mexico, Chile, Peru, Argentina, Colombia
- EMEA: Turkey, Poland, Saudi Arabia, UAE, Qatar, South Africa, Egypt, Nigeria, Greece

**Benchmark for all universes:** SPY (S&P 500)

---

## Strategy Logic

### Core Methodology (Optimized)

1. **Relative Strength (RS) Ratio**: ETF price / SPY price
2. **RS Filter**: RS ratio must be > its 10-month SMA (relative trend)
3. **Absolute Filter**: ETF price must be > its 10-month SMA (absolute trend)
4. **Momentum Ranking**: Calculate **3-month** RS Rate of Change (ROC) — optimized from 1-month
5. **Portfolio Selection**: Choose top **3 ETFs** by RS momentum — optimized from 5
6. **Equal Weighting**: 33% allocation to each selected ETF
7. **SPY Fallback**: If <3 ETFs qualify, allocate remainder to SPY
8. **Rebalancing**: **Weekly monitoring** with conditional trading (only trade when signals change)
9. **Volatility Regime Switching**: Adaptive position sizing based on market volatility (low/medium/high)

### Why This Works

- **Dual filters prevent false signals**: Both relative and absolute trends must align
- **RS vs SPY captures relative momentum**: Identifies outperformers vs market
- **3-month ROC reduces noise**: More stable than 1-month, captures sustainable trends
- **Top 3 concentration**: Holding only the strongest performers beats diversification (avg Sharpe 0.591 vs 0.573 for 5 holdings)
- **Weekly monitoring**: Better performance than monthly (378% vs 341%) with only ~60-70% weeks requiring trades
- **Volatility regime adaptation**: Adjusts holdings and SPY allocation based on market conditions

---

## Optimization & Research Findings

### Parameter Optimization Results

A comprehensive grid search tested **48 parameter combinations** across:
- SMA Windows: 6, 8, 10, 12 months
- ROC Lookbacks: 1, 3, 6 months
- Top N Holdings: 3, 5, 7, 10

**Key Findings:**

1. **Top 3 Holdings Beat More Diversification**
   - Average Sharpe: 3 holdings (0.591) vs 5 holdings (0.573) vs 10 holdings (0.558)
   - Top 5 ranked combinations ALL use 3 holdings
   - Holding 4th and 5th ranked ETFs dilutes alpha from top performers

2. **3-Month ROC Beats 1-Month**
   - 3-month lookback captures sustainable trends without noise
   - Changing from 1mo → 3mo increased returns by ~25%
   - 6-month lookback too slow to adapt to regime changes

3. **Weekly Rebalancing Outperforms Monthly**
   - Weekly monitoring with conditional trading: 378% return, 0.700 Sharpe
   - Monthly rebalancing: 341% return, 0.656 Sharpe
   - Only ~60-70% of weeks require actual trades (rest stay unchanged)

**Optimization Impact:**
- **Before:** 270% return, Sharpe 0.574, +29% vs SPY (Rank: 24/48)
- **After:** 341% return, Sharpe 0.656, +100% vs SPY (Rank: 1/48)
- **Improvement:** +70.56 percentage points, +14.2% Sharpe

See `output/sp500/optimization_results.csv` for full results.

### Volatility Regime Switching

The strategy adapts to market volatility conditions:

**SPY-Based Detection (default):**
- Low Vol (<10%): 3 holdings, aggressive (no SPY minimum)
- Medium Vol (10-25%): 3 holdings, normal allocation
- High Vol (>25%): 5 holdings, minimum 20% SPY allocation

**Alternative: VIX-Based Detection**
- Uses ^VIX ticker with smoothing and hysteresis
- Configurable thresholds for regime transitions

**Defensive Modes** (high volatility):
- `baseline`: Increase SPY allocation
- `defensive_sectors`: Force allocation to XLP, XLU, XLV
- `tbills`: 100% T-Bills (BIL)
- `hybrid`: 50% T-Bills + 50% defensive sectors
- `tiered`: Defensive sectors in high vol, T-Bills in extreme vol (>35%)

---

## Deployment Status

**✅ Production Ready** - The project workspace has been cleaned and validated for deployment:

- ✅ All test scripts and debug files removed (51 files cleaned)
- ✅ CLI functionality verified and working
- ✅ API endpoints tested and operational
- ✅ React UI validated across all pages
- ✅ No broken dependencies or imports
- ✅ Comprehensive test report available: `POST_CLEANUP_TEST_REPORT.md`

**Ready for**: Google Cloud Run deployment, Docker containerization, or local production use.

**Cleanup Utility**: Use `cleanup_workspace.py` to safely remove test files in future sessions (includes backup and restore features).

---

## Output Files

Results are saved in universe-specific directories:

```
output/
├── sp500/
│   ├── backtest_results.csv          # Equity curve data
│   ├── performance_summary.csv       # Key metrics vs SPY
│   ├── yearly_summary.csv            # Year-by-year performance
│   ├── monthly_holdings.csv          # Holdings each month
│   ├── current_signals.csv           # Latest month portfolio (signal mode)
│   └── all_etf_status.csv           # Complete ETF status (signal mode)
├── developed/
│   └── (same structure)
└── emerging/
    └── (same structure)
```

### Report Contents

**Backtest Reports:**
- `performance_summary.csv`: Total return, annualized return, Sharpe ratio, max drawdown, vs SPY
- `yearly_summary.csv`: Year-by-year returns for portfolio and SPY
- `monthly_holdings.csv`: Portfolio composition at each rebalance
- `backtest_results.csv`: Daily portfolio values and returns

**Signal Reports:**
- `current_signals.csv`: Top 5 recommended ETFs for current month
- `all_etf_status.csv`: Complete status of all ETFs (prices, SMAs, filters, rankings)

---

## Configuration

Edit `etfmomentum/config.py` to adjust:

```python
# Backtest period (10 years)
BACKTEST_START_DATE = "2016-01-01"
BACKTEST_END_DATE = "2026-03-01"
DATA_START_DATE = "2015-01-01"  # Must be 10+ months before backtest start

# Optimized Strategy Parameters (from grid search)
SMA_LOOKBACK_DAYS = 210  # 10-month SMA (optimized)
RS_ROC_LOOKBACK_DAYS = 63  # 3-month momentum lookback (optimized from 21 days)
TOP_N_HOLDINGS = 3  # Number of ETFs to hold (optimized from 5)
REBALANCE_FREQUENCY = "weekly"  # "weekly" or "monthly" (weekly performs better)
INITIAL_CAPITAL = 100000  # Starting capital for backtest

# Volatility Regime Switching
ENABLE_VOLATILITY_REGIME_SWITCHING = True  # Toggle regime switching on/off
USE_VIX_FOR_REGIME = False  # Use VIX ticker (True) or calculate from SPY (False)
VOLATILITY_LOOKBACK_DAYS = 30  # Window for SPY volatility calculation
LOW_VOL_THRESHOLD = 0.10  # 10% annualized
HIGH_VOL_THRESHOLD = 0.25  # 25% annualized

# Regime-Specific Parameters
LOW_VOL_TOP_N = 3  # Holdings in low volatility (aggressive)
MEDIUM_VOL_TOP_N = 3  # Holdings in medium volatility (normal)
HIGH_VOL_TOP_N = 5  # Holdings in high volatility (defensive)
HIGH_VOL_SPY_MIN_ALLOCATION = 0.20  # Minimum 20% SPY in high vol

# API settings
FMP_API_DELAY = 0  # No delay needed with premium plan (3000 calls/min)

# Paths
ETFLIST_DIR = PROJECT_ROOT / "etflist"  # External ETF universe CSVs
DATA_DIR = PROJECT_ROOT / "data"  # Cached price data
OUTPUT_DIR = PROJECT_ROOT / "output"  # Results
```

### Updating for Future Backtests

To extend the backtest period, only update:
```python
BACKTEST_END_DATE = "2026-04-01"  # New end date
```

For signal generation, **no changes needed** - always uses latest data.

---

## Project Structure

```
etfmomentum/
├── etfmomentum/                      # Core Python package
│   ├── __init__.py
│   ├── __main__.py                  # CLI entry point
│   ├── main.py                      # CLI orchestrator (backtest/signal modes)
│   ├── config.py                    # Configuration and optimized parameters
│   ├── data_fetcher.py              # FMP API integration (stable endpoints)
│   ├── etf_loader.py                # Load ETF universes from CSV
│   ├── rs_engine.py                 # Signal generation (RS, SMA, filters, ROC)
│   ├── backtest.py                  # Portfolio simulation engine
│   ├── report.py                    # Performance metrics and reporting
│   ├── signal_generator.py          # Live signal generation
│   ├── signal_report.py             # Signal formatting and output
│   │
│   ├── optimizer.py                 # Grid search parameter optimization
│   ├── volatility_regime.py         # Volatility regime detection and switching
│   ├── trading_frequency_analyzer.py # Weekly vs monthly rebalancing analysis
│   ├── defensive_strategy_tester.py  # Defensive allocation testing
│   ├── timing_strategy_tester.py     # Market timing analysis
│   └── volatility_timing_analyzer.py # Volatility signal lag analysis
│
├── api/                             # FastAPI backend
│   ├── main.py                      # FastAPI application
│   ├── requirements.txt             # API dependencies
│   ├── models/
│   │   └── schemas.py               # Pydantic models
│   └── routes/
│       ├── dashboard.py             # Dashboard endpoint
│       ├── signals.py               # Signal generation endpoint
│       ├── backtest.py              # Backtest endpoint
│       └── config.py                # Config endpoint
│
├── ui/                              # React Web UI
│   ├── src/
│   │   ├── main.jsx                 # React entry point
│   │   ├── App.jsx                  # Main app component
│   │   ├── components/              # Reusable components
│   │   └── pages/
│   │       ├── Dashboard.jsx        # Dashboard page
│   │       ├── Signals.jsx          # Signal generation page
│   │       └── Backtest.jsx         # Backtest page
│   ├── package.json
│   └── vite.config.js               # Vite build config
│
├── etflist/                         # ETF universe definitions (CSV)
│   ├── sp500_sector_etfs.csv       # 11 S&P 500 sector ETFs
│   ├── developed_market_etfs.csv   # 21 developed market ETFs
│   └── emerging_market_etfs.csv    # 28 emerging market ETFs
│
├── data/                            # Cached price data (gitignored)
│   └── price_data.csv
│
├── output/                          # Results by universe (gitignored)
│   ├── sp500/
│   │   ├── optimization_results.csv
│   │   ├── optimization_summary.txt
│   │   ├── weekly_trading_frequency.csv
│   │   └── ... (backtest/signal results)
│   ├── developed/
│   └── emerging/
│
├── .env                             # FMP API key (gitignored)
├── pyproject.toml                   # UV dependencies
├── uv.lock                          # Dependency lock file
├── start_api.sh                     # API server startup script
├── start_ui.sh                      # UI server startup script
├── cleanup_workspace.py             # Workspace cleanup utility
├── CLEANUP_GUIDE.md                 # Cleanup documentation
├── POST_CLEANUP_TEST_REPORT.md      # Validation test report
└── README.md                        # This file
```

**Note**: This project has been cleaned of all test scripts and temporary documentation. Core functionality (CLI, API, UI) is fully tested and production-ready.

---

## Adding/Modifying ETF Universes

To add or remove ETFs:

1. Edit the relevant CSV file in `etflist/`:
   - Format: `Ticker,ETF_Name,Issuer`
   - Example: `"XLK","Technology","SPDR (State Street)"`

2. Run with `--refresh` to fetch data for new ETFs:
   ```bash
   uv run python -m etfmomentum backtest --universe sp500 --refresh
   ```

To create a new universe:
1. Create new CSV in `etflist/` (e.g., `bond_etfs.csv`)
2. Update `etf_loader.py` to add the new universe name
3. Update `main.py` to add it to CLI choices

---

## Technical Details

### API Integration

- **Endpoint**: `https://financialmodelingprep.com/api/stable/historical-price-eod/full`
- **Response format**: Direct list of price records (not nested dict)
- **Price field**: Uses `"close"` field (not `"adjClose"`)
- **Caching**: Saves to `data/price_data.csv` to minimize API calls
- **Date range**: Automatically calculated based on config dates + 10-month buffer for SMA

### Data Requirements

For signal generation:
- Minimum 11 months of data (10-month SMA + 1 month for ROC)

For backtesting:
- Data start must be 10+ months before backtest start
- Currently: 2015-01-01 to 2026-03-01 (11 years)

### Performance Notes

- Uses pandas for efficient time-series operations
- Data cached to avoid repeated API calls
- Premium FMP plan allows rapid data fetching (3000 calls/min)

---

## Requirements

- **Python**: 3.11+
- **Package Manager**: UV
- **API**: Financial Modeling Prep (premium plan recommended)
- **Dependencies**: pandas, numpy, requests, python-dotenv, tabulate

---

## Common Workflows

### Monthly Signal Generation (Recommended)

On the first trading day of each month:

```bash
# 1. Generate signals with fresh data
uv run python -m etfmomentum signal --universe sp500 --detailed --refresh

# 2. Review recommendations in terminal output

# 3. Check detailed reports
cat output/sp500/current_signals.csv
cat output/sp500/all_etf_status.csv
```

### Quarterly Backtest Review

Every quarter, run updated backtests:

```bash
# 1. Update config.py with new end date
# Edit: BACKTEST_END_DATE = "2026-06-01"

# 2. Run backtests for all universes
uv run python -m etfmomentum backtest --universe sp500 --refresh
uv run python -m etfmomentum backtest --universe developed --refresh
uv run python -m etfmomentum backtest --universe emerging --refresh

# 3. Compare performance metrics
cat output/*/performance_summary.csv
```

### Research and Optimization

```bash
# Run parameter optimization (grid search across 48 combinations)
uv run python -m etfmomentum.optimizer

# Analyze trading frequency (weekly vs monthly)
uv run python -m etfmomentum.trading_frequency_analyzer

# Test defensive strategies in high volatility
uv run python -m etfmomentum.defensive_strategy_tester

# Compare different top-N values
uv run python -m etfmomentum backtest --universe sp500 --top-n 3
uv run python -m etfmomentum backtest --universe sp500 --top-n 7

# Test different universes
uv run python -m etfmomentum signal --universe developed --detailed --refresh
uv run python -m etfmomentum signal --universe emerging --detailed --refresh
```

---

## Troubleshooting

### "Ticker XXX not found in price data"
- Use `--refresh` flag to fetch fresh data
- Check if ticker exists in FMP database
- Verify ticker spelling in CSV file

### "Division by zero" or missing data
- Some ETFs may have limited history (e.g., HEWG, EWGS)
- These are automatically skipped with warnings
- Check `all_etf_status.csv` for data availability

### Cached data is stale
- Delete `data/price_data.csv` manually, or
- Always use `--refresh` flag for signal generation

### Wrong universe data
- Data cache is shared across universes
- Use `--refresh` when switching between universes
- Or delete `data/price_data.csv` before running

---

## License

MIT

---

## Contact

For questions about this framework, refer to the conversation logs or Claude memory files at:
`~/.claude/projects/-Users-jaig-etfmomentum/`

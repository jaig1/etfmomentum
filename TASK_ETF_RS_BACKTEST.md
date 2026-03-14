# TASK: ETF Relative Strength vs SPY — Backtest & Signal Framework

## Status: ✅ IMPLEMENTATION COMPLETE

This document describes the **fully implemented** ETF momentum backtesting and signal generation framework. The system supports both historical backtesting and live signal generation across three distinct ETF universes.

---

## Objective

Build a Python-based system that implements an **ETF Momentum Rotation Strategy** using Relative Strength (RS) vs SPY. The framework:

1. **Backtests** the strategy over historical periods (10 years: 2016-2026)
2. **Generates live signals** for current month portfolio recommendations
3. **Supports 3 ETF universes**: S&P 500 Sectors, Developed Markets, Emerging Markets
4. **Identifies outperformers** systematically and rotates into strongest momentum ETFs

---

## Implementation Summary

### ✅ Completed Features

- [x] Multi-universe support (48 total ETFs across 3 universes)
- [x] 10-year historical backtesting (2016-2026)
- [x] Live signal generation mode
- [x] Dual momentum filters (relative + absolute)
- [x] Top 5 ETF selection with equal weighting
- [x] SPY fallback allocation
- [x] Monthly rebalancing simulation
- [x] Comprehensive performance reporting
- [x] Yearly summary breakdowns
- [x] Data caching with refresh capability
- [x] External ETF universe configuration (CSV files)
- [x] CLI with subcommands and universe selection
- [x] FMP API integration (stable endpoints)

### 📊 Performance Results (10-Year Backtest 2016-2026)

| Universe | Total Return | Annualized | Sharpe | Max DD | vs SPY |
|----------|-------------|------------|--------|--------|--------|
| **S&P 500 Sectors** | +274% | +14.2% | 1.05 | -17.8% | **+33%** ✓ |
| Emerging Markets | +156% | +9.9% | 0.66 | -27.5% | -85% |
| Developed Markets | +107% | +7.5% | 0.50 | -25.3% | -134% |
| SPY (Benchmark) | +241% | +13.1% | 0.95 | -19.6% | — |

**Winner**: S&P 500 Sector ETF rotation (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC)

---

## Data Source

- **Provider:** Financial Modeling Prep (FMP)
- **API Key:** Stored in `.env` file (never hardcoded)
- **Endpoint:** `https://financialmodelingprep.com/api/stable/historical-price-eod/full` (stable, not v3)
- **Data Type:** Daily closing prices (uses `"close"` field)
- **API Plan:** Premium (3000 calls/min, 30 years history)
- **Rate Limiting:** No delay needed (FMP_API_DELAY = 0)
- **Data Period:**
  - Backtest: 2016-01-01 to 2026-03-01 (10 years)
  - Data buffer: Starts 2015-01-01 (10+ months before backtest for SMA calculation)
  - Signal generation: Latest 12 months (automatic)

---

## ETF Universes

### Three Distinct Universes

All universes defined in external CSV files under `/etflist/`:

#### 1. S&P 500 Sector ETFs (`sp500_sector_etfs.csv`)
**11 SPDR Sector ETFs** — **Best performing universe**

| Ticker | Sector | Issuer |
|--------|--------|--------|
| XLK | Technology | SPDR (State Street) |
| XLF | Financials | SPDR (State Street) |
| XLE | Energy | SPDR (State Street) |
| XLV | Health Care | SPDR (State Street) |
| XLY | Consumer Discretionary | SPDR (State Street) |
| XLP | Consumer Staples | SPDR (State Street) |
| XLI | Industrials | SPDR (State Street) |
| XLB | Materials | SPDR (State Street) |
| XLRE | Real Estate | SPDR (State Street) |
| XLU | Utilities | SPDR (State Street) |
| XLC | Communication Services | SPDR (State Street) |

#### 2. Developed Market ETFs (`developed_market_etfs.csv`)
**26 iShares Country ETFs**

Countries: Japan (EWJ), Germany (EWG), UK (EWU), Australia (EWA), Canada (EWC), France (EWQ), Switzerland (EWL), Spain (EWP), Italy (EWI), Netherlands (EWN), Sweden (EWD), Belgium (EWK), Singapore (EWS), Hong Kong (EWH), Norway (ENOR), Denmark (EDEN), Finland (EFNL), Ireland (EIRL), Israel (EIS)

Also includes: Small-cap variants (EWGS, SCJ, EWUS, EWAS) and currency-hedged (HEWJ, HEWG, HEWU)

#### 3. Emerging Market ETFs (`emerging_market_etfs.csv`)
**28 Country/Regional ETFs**

**Asia**: FXI (China Large-Cap), MCHI (China Broad), KWEB (China Internet), INDA (India), SMIN (India Small-Cap), EWT (Taiwan), EWY (South Korea), EWM (Malaysia), EIDO (Indonesia), THD (Thailand), EPHE (Philippines), VNM (Vietnam)

**Latin America**: EWZ (Brazil), EWW (Mexico), ECH (Chile), EPU (Peru), ILF (Latin America 40), ARGT (Argentina), GXG (Colombia)

**EMEA**: TUR (Turkey), EPOL (Poland), KSA (Saudi Arabia), UAE (UAE), QAT (Qatar), EZA (South Africa), EGPT (Egypt), NGE (Nigeria), GREK (Greece)

### Benchmark
- **SPY** — SPDR S&P 500 ETF Trust (used for all three universes)

---

## Strategy Logic — Step by Step

### Step 1: Calculate the Relative Strength (RS) Ratio

For each ETF, on each trading day:

```
RS_Ratio = ETF_Close / SPY_Close
```

This ratio rising = ETF outperforming SPY. Ratio falling = SPY winning.

### Step 2: Apply the RS Filter (Relative Trend)

Calculate a **10-month SMA** of each ETF's RS Ratio.

**Signal Rule:**
- RS Ratio **above** its 10-month SMA → **PASS** ✓ (outperforming SPY)
- RS Ratio **below** its 10-month SMA → **FAIL** ✗ (underperforming SPY)

### Step 3: Apply the Absolute Trend Filter

For each ETF, calculate the **10-month SMA** of its own price.

**Signal Rule:**
- ETF price **above** its own 10-month SMA → **PASS** ✓ (uptrend)
- ETF price **below** its own 10-month SMA → **FAIL** ✗ (downtrend)

**Both filters must be TRUE to hold the ETF.**

### Step 4: Rank by RS Momentum (ROC)

Among ETFs that pass both filters, rank them by **1-month RS Rate of Change**:

```
RS_ROC = (RS_Ratio_today - RS_Ratio_1_month_ago) / RS_Ratio_1_month_ago
```

Higher RS_ROC = stronger recent momentum = higher rank.

### Step 5: Select Top 5 and Allocate

- Select the **top 5 ETFs** by RS_ROC ranking
- Allocate **equal weight** (20% each) across selected ETFs
- If fewer than 5 ETFs pass both filters, allocate remainder to **SPY**
  - Example: 3 ETFs pass → 60% in ETFs (3 × 20%) + 40% in SPY
- If **zero** ETFs pass both filters → 100% in SPY

### Step 6: Rebalance Monthly

- Rebalance on the **first trading day of each month**
- On each rebalance date:
  1. Recalculate RS Ratios and SMAs using data through prior month-end
  2. Apply both filters
  3. Rank qualifying ETFs by RS ROC
  4. Select top 5
  5. Rebalance portfolio to new equal-weight targets
  6. Log portfolio composition

---

## Implementation Architecture

### Project Structure

```
etfmomentum/
├── etfmomentum/               # Main package
│   ├── __init__.py
│   ├── __main__.py           # CLI entry point
│   ├── main.py               # Orchestration (backtest/signal modes)
│   ├── config.py             # Configuration and parameters
│   ├── data_fetcher.py       # FMP API integration
│   ├── etf_loader.py         # Load ETF universes from CSV
│   ├── rs_engine.py          # Signal generation logic
│   ├── backtest.py           # Portfolio simulation engine
│   ├── report.py             # Backtest performance metrics
│   ├── signal_generator.py   # Live signal generation
│   └── signal_report.py      # Signal formatting and output
├── etflist/                  # ETF universe definitions
│   ├── sp500_sector_etfs.csv
│   ├── developed_market_etfs.csv
│   └── emerging_market_etfs.csv
├── data/                     # Cached price data (gitignored)
│   └── price_data.csv
├── output/                   # Results by universe (gitignored)
│   ├── sp500/
│   ├── developed/
│   └── emerging/
├── .env                      # FMP API key (gitignored)
├── .env.example              # API key template
├── pyproject.toml           # UV dependencies
└── README.md                # Documentation
```

### Core Modules

#### `config.py`
- Loads FMP API key from `.env` using `python-dotenv`
- Defines strategy parameters (SMA window, lookback periods, top N)
- Defines backtest period (2016-2026)
- Defines file paths (data, output, etflist directories)
- **Note**: ETF universes externalized to CSV files (not in config)

#### `etf_loader.py`
- `load_etf_universe(csv_file_path)` → reads CSV and returns {ticker: name} dict
- `load_universe_by_name(universe_name, etflist_dir)` → loads by name (sp500/developed/emerging)
- CSV format: `Ticker,ETF_Name,Issuer`

#### `data_fetcher.py`
- `fetch_historical_data(ticker, start_date, end_date, api_key)` → fetches from FMP stable endpoint
- `fetch_all_data(ticker_list, start_date, end_date, api_key)` → fetches all tickers + SPY
- Response handling: Direct list format, uses `"close"` field (not `"adjClose"`)
- Caching: Saves to `data/price_data.csv`
- Returns DataFrame with tickers as columns, dates as index

#### `rs_engine.py`
- `calculate_rs_ratio(etf_prices, spy_prices)` → ETF / SPY ratio
- `calculate_sma(series, window)` → rolling mean
- `apply_rs_filter(rs_ratio, rs_sma)` → boolean (ratio > SMA)
- `apply_absolute_filter(etf_prices, price_sma)` → boolean (price > SMA)
- `calculate_rs_roc(rs_ratio, lookback)` → momentum calculation
- `generate_signals(price_data, etf_tickers, spy_ticker, sma_window, roc_lookback)` → complete signal DataFrame
- `get_all_etf_status(signals, date)` → detailed status table for all ETFs

#### `backtest.py`
- `run_backtest(price_data, signals, etf_tickers, spy_ticker, config)` → full simulation
- Tracks portfolio value daily
- Identifies rebalance dates (first trading day of month)
- On rebalance: applies filters, ranks, selects top 5, calculates new weights
- Calculates daily returns between rebalances
- Also simulates SPY buy-and-hold for comparison
- Returns portfolio values, holdings log, rebalance dates

#### `report.py`
- `calculate_performance_metrics(returns)` → total return, annualized return, Sharpe ratio, max drawdown
- `calculate_yearly_returns(portfolio_values)` → year-by-year breakdown
- `generate_performance_summary(portfolio_metrics, spy_metrics, output_dir)` → comparison table
- `generate_monthly_holdings_report(holdings_log, output_dir, etf_universe)` → what was held each month
- Saves all reports as CSV files in universe-specific output directories

#### `signal_generator.py`
- `generate_current_signals(price_data, etf_tickers, spy_ticker, sma_window, roc_lookback)` → signals for latest date
- `select_current_portfolio(signals, latest_date, top_n, spy_ticker)` → current month recommendations
- `get_all_etf_current_status(signals, latest_date)` → complete ETF status for current month

#### `signal_report.py`
- `generate_signal_report(portfolio, output_dir, etf_universe)` → formatted recommendation table
- `generate_detailed_status_report(status, output_dir, etf_universe)` → all ETF signals
- `print_summary_stats(portfolio, signals)` → console summary

#### `main.py`
- CLI orchestrator using `argparse` with subcommands
- Two modes: `backtest` and `signal`
- Common arguments: `--universe {sp500|developed|emerging}`, `--refresh`
- Backtest mode: runs historical simulation, generates performance reports
- Signal mode: generates current month recommendations
- Creates universe-specific output directories automatically

---

## CLI Usage

### Package Manager
This project uses **UV** (not pip). Install dependencies:
```bash
uv sync
```

### Backtest Mode

```bash
# 10-year backtest for S&P 500 sectors
uv run python -m etfmomentum backtest --universe sp500

# Backtest other universes
uv run python -m etfmomentum backtest --universe developed
uv run python -m etfmomentum backtest --universe emerging

# Force refresh data from FMP API
uv run python -m etfmomentum backtest --universe sp500 --refresh

# Override parameters
uv run python -m etfmomentum backtest --universe sp500 --top-n 3 --initial-capital 50000
```

### Signal Mode (Live Recommendations)

```bash
# Generate current month signals for S&P 500 sectors
uv run python -m etfmomentum signal --universe sp500 --refresh

# Add detailed status for all ETFs
uv run python -m etfmomentum signal --universe sp500 --detailed --refresh

# Generate signals for other universes
uv run python -m etfmomentum signal --universe developed --detailed --refresh
uv run python -m etfmomentum signal --universe emerging --detailed --refresh
```

**Important**: Always use `--refresh` for signal generation to fetch latest data.

### CLI Arguments

**Subcommands:**
- `backtest` - Run historical backtest
- `signal` - Generate current month recommendations

**Common arguments:**
- `--universe {sp500|developed|emerging}` - **Required**: Select ETF universe
- `--refresh` - Force re-download data from FMP API (bypasses cache)

**Backtest-specific:**
- `--top-n N` - Number of ETFs to hold (default: 5)
- `--initial-capital AMOUNT` - Starting capital (default: 100000)

**Signal-specific:**
- `--detailed` - Include comprehensive ETF status report

---

## Output Files

Results saved in universe-specific directories under `output/`:

### Backtest Outputs

```
output/{universe}/
├── backtest_results.csv          # Daily portfolio values and returns
├── performance_summary.csv       # Key metrics vs SPY
├── yearly_summary.csv            # Year-by-year performance
└── monthly_holdings.csv          # Holdings at each rebalance
```

**performance_summary.csv** columns:
- Metric, Strategy, SPY
- Total Return (%), Annualized Return (%), Sharpe Ratio, Max Drawdown (%), Outperformance vs SPY (%)

**yearly_summary.csv** columns:
- Year, Portfolio Return (%), SPY Return (%)

**monthly_holdings.csv** columns:
- Rebalance_Date, Rank_1 through Rank_5, SPY_Allocation (%)

**backtest_results.csv** columns:
- Date, Portfolio_Value, Daily_Return, SPY_Value, SPY_Return

### Signal Outputs

```
output/{universe}/
├── current_signals.csv           # Top 5 recommendations for current month
└── all_etf_status.csv           # Complete status of all ETFs
```

**current_signals.csv** columns:
- Rank, Ticker, Name, RS_ROC (%), Allocation (%)

**all_etf_status.csv** columns:
- Ticker, Name, Price, Price_SMA, RS_Ratio, RS_SMA, RS_Filter, Abs_Filter, RS_ROC, Rank, Selected

---

## Strategy Parameters

Defined in `config.py`:

```python
# Backtest Period
BACKTEST_START_DATE = "2016-01-01"  # 10-year backtest
BACKTEST_END_DATE = "2026-03-01"
DATA_START_DATE = "2015-01-01"      # 10+ months buffer for SMA

# Strategy Parameters
SMA_WINDOW = 10                     # 10-month SMA for both filters
RS_ROC_LOOKBACK = 1                 # 1-month momentum lookback
TOP_N_HOLDINGS = 5                  # Top 5 ETF selection
INITIAL_CAPITAL = 100000            # $100k starting capital

# API Settings
FMP_BASE_URL = "https://financialmodelingprep.com/api"
FMP_ENDPOINT = "/stable/historical-price-eod/full"  # Stable (not v3)
FMP_API_DELAY = 0                   # No delay (3000 calls/min plan)
RISK_FREE_RATE = 0.045              # 4.5% for Sharpe calculation

# File Paths
PROJECT_ROOT = Path(__file__).parent.parent
ETFLIST_DIR = PROJECT_ROOT / "etflist"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
```

---

## Key Implementation Details

### 1. Pandas-Based Time Series

All calculations use pandas for efficient operations:
- `rolling().mean()` for SMA calculations
- `pct_change()` for returns
- `resample('ME')` for monthly data (month-end)
- Date alignment across all ETF price series

### 2. Monthly Rebalancing Detection

- Identifies first trading day of each month from actual trading calendar
- Uses `BMonthBegin()` offset from pandas
- Handles edge cases (holidays, weekends)

### 3. Data Caching

- All fetched data saved to `data/price_data.csv`
- Avoids redundant API calls
- Use `--refresh` to force re-download
- Cache shared across universes (use `--refresh` when switching)

### 4. FMP API Response Handling

- Stable endpoint returns direct list (not nested dict)
- Uses `"close"` field (not `"adjClose"`)
- Graceful error handling for missing tickers
- No rate limiting needed (premium plan)

### 5. Edge Cases

- **Insufficient history**: ETFs without 10+ months data are skipped with warnings
- **Missing data**: Forward-fill or skip ETFs with data gaps
- **No qualifying ETFs**: 100% SPY allocation
- **Delisted ETFs**: Excluded from current signals, kept in historical backtest if data exists

### 6. Performance Calculations

- **Sharpe Ratio**: `(annualized_return - risk_free_rate) / annualized_volatility`
- **Max Drawdown**: Running maximum decline from peak to trough
- **Total Return**: `(final_value - initial_value) / initial_value`
- **Annualized Return**: `(1 + total_return) ^ (1 / years) - 1`

### 7. Pandas 3.0 Compatibility

- Uses `'ME'` for month-end (not deprecated `'M'`)
- Uses `'YE'` for year-end (not deprecated `'Y'`)

---

## Success Criteria

All criteria met ✅:

1. ✅ Data fetched from FMP for all universes (48 ETFs + SPY) using stable endpoints
2. ✅ RS Ratios and SMAs calculated correctly (verified against manual calculations)
3. ✅ Both RS filter and absolute trend filter work as specified
4. ✅ Top 5 ranking and selection logic produces correct results
5. ✅ Portfolio value tracked correctly between rebalances over 10 years
6. ✅ All output reports generated and saved to CSV (backtest + signal modes)
7. ✅ Performance metrics validated (S&P sectors outperformed SPY by 33% over 10 years)
8. ✅ Signal generation provides actionable current month recommendations
9. ✅ Multiple universe support with external CSV configuration
10. ✅ Clean, well-structured code following Python best practices
11. ✅ UV package manager integration
12. ✅ Comprehensive README documentation

---

## Implemented Enhancements

The following features were marked as "future enhancements" but are now **fully implemented**:

- ✅ **Live signal generation** for current month recommendations
- ✅ **Multiple universe support** (3 universes, 48 ETFs)
- ✅ **10-year historical backtesting** (extended from 1 year)
- ✅ **Yearly summary reporting** (in addition to monthly)
- ✅ **External ETF configuration** via CSV files
- ✅ **Universe-specific output directories**
- ✅ **CLI subcommands** (backtest/signal modes)
- ✅ **Detailed status reporting** for all ETFs

---

## Remaining Future Enhancements (Not Yet Implemented)

- Transaction costs and slippage modeling
- Multiple SMA lookback period optimization (6, 8, 10, 12 months)
- Cumulative return charts (matplotlib/plotly visualization)
- Automated rebalance alerts/notifications
- Additional data sources (Tiingo, EODHD)
- Additional metrics (Sortino ratio, Calmar ratio)
- Web dashboard for visualization
- Walk-forward optimization
- Monte Carlo simulation
- Risk parity weighting (vs equal weight)

---

## Usage Recommendations

### For Monthly Signal Generation
Run on the first trading day of each month:
```bash
uv run python -m etfmomentum signal --universe sp500 --detailed --refresh
```

### For Quarterly Performance Review
Update `BACKTEST_END_DATE` in config.py, then:
```bash
uv run python -m etfmomentum backtest --universe sp500 --refresh
uv run python -m etfmomentum backtest --universe developed --refresh
uv run python -m etfmomentum backtest --universe emerging --refresh
```

### For Testing Different Parameters
```bash
# Test top 3 vs top 5 vs top 7
uv run python -m etfmomentum backtest --universe sp500 --top-n 3
uv run python -m etfmomentum backtest --universe sp500 --top-n 7
```

---

## Key Learnings from 10-Year Backtest

1. **S&P 500 Sector rotation outperforms** country/regional ETF rotation significantly
2. **Developed markets underperform** due to slower growth and weaker momentum
3. **Emerging markets show high volatility** with higher returns but much larger drawdowns
4. **Dual filters provide downside protection** during bear markets (2022 drawdown limited)
5. **Monthly rebalancing** provides good balance between signal quality and turnover
6. **SPY fallback mechanism** reduces drawdowns when no ETFs qualify (defensive positioning)

---

## Documentation

- **README.md**: Comprehensive user guide and quick start
- **This file (TASK_ETF_RS_BACKTEST.md)**: Technical specification and implementation details
- **Code comments**: Inline documentation throughout all modules
- **Example .env**: Template for API key configuration

---

## Contact & Support

For questions or issues:
- Review README.md for usage instructions
- Check Claude conversation logs at `~/.claude/projects/-Users-jaig-etfmomentum/`
- Review this implementation specification for technical details

---

**Last Updated**: March 13, 2026
**Implementation Status**: Complete and Production-Ready ✅

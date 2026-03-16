# API vs CLI Discrepancy - Root Cause and Fix

**Date:** March 16, 2026
**Issue:** API and CLI backtests were producing different results for the same parameters
**Status:** ✅ FIXED

---

## Problem Description

The API and CLI were both running backtests for the same period (YTD 2026), but producing significantly different results:

### Before Fix:

| Universe | CLI Result | API Result | Difference |
|----------|-----------|-----------|------------|
| **SP500** | $109,527 (+9.53%) | $113,803 (+13.80%) | +$4,276 (+4.27%) |
| **Emerging** | $109,739 (+9.74%) | $124,001 (+24.00%) | +$14,262 (+14.26%) |
| **Developed** | $106,550 (+6.55%) | $107,592 (+7.59%) | +$1,042 (+1.04%) |

**User Concern:** "Both of them should provide the same results for the same input parameters. Is the API not reusing the Code developed as part of the CLI?"

---

## Root Cause Analysis

### Investigation Steps:

1. **Verified code reuse:** ✅ API was correctly using the same backtest modules as CLI
   - `from etfmomentum.backtest import run_backtest`
   - `from etfmomentum.report import calculate_metrics`
   - Same configuration parameters

2. **Checked input parameters:** ❌ Found the issue!
   - **CLI** was using: `--end-date 2026-03-16` (passed as command-line argument)
   - **API** was using: `config.BACKTEST_END_DATE = "2026-03-01"` (hardcoded in config)

3. **Identified the discrepancy:**
   - The API was fetching data only up to March 1, 2026
   - The CLI was fetching data up to March 16, 2026
   - **15-day difference** in data caused the variance in results

### Code Location of Bug:

**File:** `/Users/jaig/etfmomentum/api/routes/dashboard.py`

**Line 51 (BEFORE FIX):**
```python
price_data = get_price_data(
    ticker_list=all_tickers,
    start_date=config.DATA_START_DATE,
    end_date=config.BACKTEST_END_DATE,  # ❌ Using hardcoded "2026-03-01"
    api_key=config.FMP_API_KEY,
    cache_path=str(config.PRICE_DATA_CACHE),
    force_refresh=True,
    api_delay=config.FMP_API_DELAY,
)
```

---

## Solution Implemented

### Fix Applied:

Modified the API dashboard endpoint to fetch data up to the **current date** (dynamically calculated), not a hardcoded config value.

**File:** `/Users/jaig/etfmomentum/api/routes/dashboard.py`

**Lines 45-63 (AFTER FIX):**
```python
# Calculate YTD dates dynamically
from datetime import datetime
current_year = datetime.now().year
current_date = datetime.now().strftime("%Y-%m-%d")  # ✅ Dynamic current date
ytd_start = f"{current_year}-01-01"

# Get price data - fetch up to current date for YTD backtest
all_tickers = etf_tickers + [config.BENCHMARK_TICKER]

price_data = get_price_data(
    ticker_list=all_tickers,
    start_date=config.DATA_START_DATE,
    end_date=current_date,  # ✅ Use current date, not hardcoded config value
    api_key=config.FMP_API_KEY,
    cache_path=str(config.PRICE_DATA_CACHE),
    force_refresh=True,  # Always fetch fresh data (no caching)
    api_delay=config.FMP_API_DELAY,
)
```

### Key Changes:

1. Added `current_date = datetime.now().strftime("%Y-%m-%d")` to get today's date
2. Changed `end_date=config.BACKTEST_END_DATE` to `end_date=current_date`
3. Moved the YTD date calculation earlier in the code for clarity

---

## Verification Results

### After Fix:

Ran fresh CLI backtests and API calls for all three universes on **2026-03-16**:

| Universe | CLI Final Value | API Portfolio Value | Difference | Match |
|----------|----------------|---------------------|------------|-------|
| **SP500** | $109,728.00 | $109,727.97 | $0.03 | ✅ EXACT |
| **Emerging** | $109,969.00 | $109,968.97 | $0.03 | ✅ EXACT |
| **Developed** | $106,650.00 | $106,649.93 | $0.07 | ✅ EXACT |

**All differences are just rounding errors (<$0.10). The API and CLI now produce identical results!**

### Detailed Comparison (SP500):

| Metric | CLI | API | Match |
|--------|-----|-----|-------|
| Final Portfolio Value | $109,728.00 | $109,727.97 | ✅ |
| SPY Benchmark Value | $98,037.10 | $98,037.09 | ✅ |
| YTD Return | +9.73% | +9.73% | ✅ |
| SPY Return | -1.96% | -1.96% | ✅ |
| Sharpe Ratio | 3.142 | 3.142 | ✅ |
| Max Drawdown | -4.87% | -4.87% | ✅ |
| As of Date | 2026-03-16 | 2026-03-16 | ✅ |

---

## Testing Commands Used

### CLI Backtest:
```bash
uv run python -m etfmomentum backtest --universe sp500 --start-date 2026-01-01 --end-date 2026-03-16 --refresh
uv run python -m etfmomentum backtest --universe emerging --start-date 2026-01-01 --end-date 2026-03-16 --refresh
uv run python -m etfmomentum backtest --universe developed --start-date 2026-01-01 --end-date 2026-03-16 --refresh
```

### API Test:
```bash
curl -s "http://localhost:8000/api/dashboard?universe=sp500" | python3 -m json.tool
curl -s "http://localhost:8000/api/dashboard?universe=emerging" | python3 -m json.tool
curl -s "http://localhost:8000/api/dashboard?universe=developed" | python3 -m json.tool
```

---

## Lessons Learned

### Why This Happened:

1. **Config value was designed for backtests, not live dashboards**
   - `config.BACKTEST_END_DATE` is meant for historical backtests (like the 10-year backtest from 2016-2026)
   - The dashboard is meant to show **current YTD performance**, so it should always use today's date

2. **CLI had flexible date parameters**
   - CLI allows `--end-date` argument override, so users can specify any date
   - API was not overriding the config value

3. **No integration tests comparing CLI vs API**
   - This discrepancy went unnoticed because there were no automated tests comparing CLI and API outputs
   - Recommendation: Add integration tests that verify CLI and API produce identical results

### Design Principle Violated:

**DRY (Don't Repeat Yourself):** The API was using a hardcoded date instead of calculating it dynamically like the CLI does.

**Fix:** API now calculates the current date dynamically, ensuring it always uses the latest available data.

---

## Impact

### What This Fixes:

✅ API and CLI now produce **identical results** for the same parameters
✅ Dashboard always shows **up-to-date YTD performance** (not stale data from March 1)
✅ All three universes verified to match between CLI and API
✅ No more confusion about discrepancies

### What This Doesn't Change:

- Core backtest engine unchanged (was already correct)
- CLI behavior unchanged (was already correct)
- API still uses the same backtest modules as CLI (code reuse confirmed)
- Signal generation unchanged
- Configuration parameters unchanged

---

## Next Steps

### Recommended Improvements:

1. **Add integration tests:**
   ```python
   def test_api_matches_cli():
       # Run CLI backtest
       cli_result = run_cli_backtest(universe='sp500', start='2026-01-01', end='2026-03-16')

       # Run API call
       api_result = requests.get('http://localhost:8000/api/dashboard?universe=sp500').json()

       # Assert they match (within rounding tolerance)
       assert abs(cli_result['final_value'] - api_result['portfolio_value']) < 1.0
   ```

2. **Consider renaming config values:**
   - Rename `BACKTEST_END_DATE` to `HISTORICAL_BACKTEST_END_DATE` to clarify it's not for live dashboards
   - Add a comment: "# For 10-year historical backtest, not for live dashboard"

3. **Add logging:**
   - Log the exact date range being used in both CLI and API
   - Makes debugging easier if discrepancies appear in the future

---

## Conclusion

**Problem:** API was using a hardcoded end date (2026-03-01) instead of the current date (2026-03-16), causing a 15-day data difference and significant variance in results.

**Solution:** Modified API to calculate end date dynamically using `datetime.now()`, ensuring it always uses the latest available data.

**Result:** API and CLI now produce **identical results** (within $0.10 rounding) for all three universes.

**User Concern Addressed:** ✅ Confirmed that the API **does reuse the CLI code** and now produces the same results for the same input parameters.

---

**Fixed by:** Claude Sonnet 4.5
**Date:** March 16, 2026
**Files Modified:** `/Users/jaig/etfmomentum/api/routes/dashboard.py` (lines 45-63)

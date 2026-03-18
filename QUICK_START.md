# Quick Start: Using ETF Momentum in Another Project

## ⚠️ PREREQUISITE (Required!)

**You MUST have a Financial Modeling Prep API key before installation.**

Get one here: https://financialmodelingprep.com/developer/docs/

---

## Install (2 minutes)

### Step 1: Create .env file (REQUIRED)
```bash
# In your other project directory
echo "FMP_API_KEY=your_key_here" > .env
echo ".env" >> .gitignore  # Keep it private!
```

### Step 2: Install the package
```bash
pip install -e /Users/jaig/etfmomentum
```

### Step 3: Test it worked
```bash
python -c "import etfmomentum; print('✓ Installed v' + etfmomentum.__version__)"
```

**Error about FMP_API_KEY?** Make sure you completed Step 1.

## Use It (3 ways)

### 1. Generate Current Signals (Most Common)

```python
from etfmomentum import generate_current_signals

# Get buy signals for S&P 500 sectors
signals = generate_current_signals(universe='sp500')
print(signals)
```

### 2. Run a Backtest

```python
from etfmomentum import (
    load_universe_by_name,
    get_price_data,
    run_backtest,
    get_rebalance_dates,
    config,
)
from datetime import datetime

# Load data
universe = load_universe_by_name('sp500')
prices = get_price_data(
    tickers=list(universe.keys()),
    start_date='2020-01-01',
    end_date='2024-01-01',
)

# Run backtest
dates = get_rebalance_dates(
    datetime(2020, 1, 1),
    datetime(2024, 1, 1),
    'monthly'
)

results = run_backtest(
    price_data=prices,
    rebalance_dates=dates,
    benchmark_ticker='SPY',
    top_n=config.TOP_N_HOLDINGS,
)

print(f"Return: {results['cumulative_returns'].iloc[-1]:.2%}")
```

### 3. Use CLI Commands

```bash
# Generate signals
etfmomentum signal --universe sp500 --detailed --refresh

# Run backtest
etfmomentum backtest --universe sp500 --refresh

# Help
etfmomentum --help
```

## Configuration

```python
from etfmomentum import config

# View settings
print(config.TOP_N_HOLDINGS)        # 3
print(config.SMA_LOOKBACK_DAYS)     # 210
print(config.RS_ROC_LOOKBACK_DAYS)  # 63

# Override for your project
config.TOP_N_HOLDINGS = 5
```

## Available Functions

```python
from etfmomentum import (
    # Main functions
    generate_current_signals,  # Get buy/sell signals
    run_backtest,              # Run historical backtest
    generate_signals,          # Generate signals from data

    # Data functions
    load_universe_by_name,     # Load ETF list
    get_price_data,            # Fetch price data

    # Reporting
    calculate_metrics,         # Performance metrics
    print_performance_summary, # Print results

    # Config
    config,                    # All settings
)
```

## Need Help?

- **Quick start:** `INSTALL_IN_OTHER_PROJECT.md`
- **Full docs:** `LIBRARY_USAGE.md`
- **Test install:** Run `python test_installation.py`
- **Summary:** `IMPLEMENTATION_SUMMARY.md`

## Troubleshooting

**Import error?**
```bash
pip install -e /Users/jaig/etfmomentum
```

**Missing API key?**
```bash
# Copy .env file
cp /Users/jaig/etfmomentum/.env .

# Or set manually
export FMP_API_KEY="your_key"
```

**Want to test?**
```bash
python /Users/jaig/etfmomentum/test_installation.py
```

---

That's it! You're ready to use ETF Momentum in your projects.

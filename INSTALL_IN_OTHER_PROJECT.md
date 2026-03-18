# Install ETF Momentum in Your Other Project

## ⚠️ PREREQUISITE: FMP API Key Required

**Before installation**, you MUST have a Financial Modeling Prep API key.

This is a **strict requirement** - the package will not import without it.

```bash
# Get a free API key (required!)
# Visit: https://financialmodelingprep.com/developer/docs/
```

---

## Quick Start (5 minutes)

### 1. Navigate to your other project
```bash
cd /path/to/your/other/project
```

### 2. Create .env file with your API key (REQUIRED)
```bash
echo "FMP_API_KEY=your_key_here" > .env

# Add .env to .gitignore to keep it private
echo ".env" >> .gitignore
```

### 3. Install etfmomentum in editable mode
```bash
# With pip
pip install -e /Users/jaig/etfmomentum

# Or with uv (recommended)
uv pip install -e /Users/jaig/etfmomentum
```

### 4. Test the installation
```bash
python -c "import etfmomentum; print(f'✓ Installed version {etfmomentum.__version__}')"
```

**If you see an error about FMP_API_KEY**, go back to step 2.

### 4. Use it in your code!
```python
# your_script.py
from etfmomentum import generate_current_signals

# Get current buy signals
signals = generate_current_signals(universe='sp500')
print(signals)
```

---

## What Happens

✅ **Editable install means:**
- The package is NOT copied to your project
- It creates a link to `/Users/jaig/etfmomentum/`
- Any changes you make to the original code are immediately available
- No need to reinstall after updates!

✅ **You can now:**
- Import etfmomentum functions in your code
- Run CLI commands: `etfmomentum signal --universe sp500`
- Use all strategy, backtest, and signal generation features

---

## Add to Your Project's Requirements

### Option A: requirements.txt
```bash
echo "-e /Users/jaig/etfmomentum" >> requirements.txt
```

Then teammates can install with:
```bash
pip install -r requirements.txt
```

### Option B: pyproject.toml (for uv projects)
Add this to your project's `pyproject.toml`:
```toml
[project]
dependencies = [
    # ... your other dependencies
]

[tool.uv]
dev-dependencies = [
    "etfmomentum @ file:///Users/jaig/etfmomentum",
]
```

Then install with:
```bash
uv sync
```

---

## Example Usage

### Simple: Get Current Signals
```python
from etfmomentum import generate_current_signals

signals_df = generate_current_signals(universe='sp500')
print(signals_df)
```

### Advanced: Custom Backtest
```python
from etfmomentum import (
    load_universe_by_name,
    get_price_data,
    run_backtest,
    get_rebalance_dates,
    config,
)
from datetime import datetime

# Load universe
universe = load_universe_by_name('sp500')

# Get data
price_data = get_price_data(
    tickers=universe.tickers,
    start_date='2020-01-01',
    end_date='2024-01-01',
)

# Run backtest
rebalance_dates = get_rebalance_dates(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 1, 1),
    frequency='monthly',
)

results = run_backtest(
    price_data=price_data,
    rebalance_dates=rebalance_dates,
    benchmark_ticker='SPY',
    top_n=config.TOP_N_HOLDINGS,
)

print(f"Total Return: {results['cumulative_returns'].iloc[-1]:.2%}")
```

### CLI Commands (after install)
```bash
# Generate signals
etfmomentum signal --universe sp500 --detailed --refresh

# Run backtest
etfmomentum backtest --universe sp500 --refresh

# Get help
etfmomentum --help
```

---

## Environment Variables

The package needs FMP_API_KEY to fetch data. Options:

### Option 1: Copy .env file
```bash
cp /Users/jaig/etfmomentum/.env /path/to/your/project/.env
```

### Option 2: Export environment variable
```bash
export FMP_API_KEY="your_key_here"
```

### Option 3: Load from etfmomentum directory
```python
from dotenv import load_dotenv
load_dotenv('/Users/jaig/etfmomentum/.env')
```

---

## Full Documentation

See **LIBRARY_USAGE.md** for:
- Complete API reference
- All available functions
- Advanced examples
- Integration patterns
- Troubleshooting

---

## Uninstall (if needed)

```bash
pip uninstall etfmomentum
```

This removes the link but doesn't delete the original code in `/Users/jaig/etfmomentum/`.

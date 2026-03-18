# Using ETF Momentum as a Library in Other Projects

## Installation (Local Editable Mode)

Install this package in your other project:

```bash
# Navigate to your other project
cd /path/to/your/other/project

# Install etfmomentum in editable mode
pip install -e /Users/jaig/etfmomentum

# Or with uv
uv pip install -e /Users/jaig/etfmomentum
```

**Benefits of editable install:**
- Any changes you make to `/Users/jaig/etfmomentum/` are immediately available
- No need to reinstall after updates
- Single source of truth for the code

## Add to Your Project's Requirements

```bash
# Add to requirements.txt
echo "-e /Users/jaig/etfmomentum" >> requirements.txt
```

Or in `pyproject.toml`:
```toml
[tool.uv]
dependencies = [
    "etfmomentum @ file:///Users/jaig/etfmomentum",
]
```

---

## Usage Examples

### 1. Generate Current Signals

```python
from etfmomentum import generate_current_signals

# Get current buy signals for S&P 500 sectors
signals_df = generate_current_signals(universe='sp500')
print(signals_df)

# With custom configuration
from etfmomentum import config

config.TOP_N_HOLDINGS = 5  # Override default
signals_df = generate_current_signals(universe='sp500')
```

### 2. Load ETF Universe and Price Data

```python
from etfmomentum import load_universe_by_name, get_price_data

# Load ETF universe
etf_universe = load_universe_by_name('sp500')
print(f"ETFs: {etf_universe.tickers}")

# Get historical price data
price_data = get_price_data(
    tickers=etf_universe.tickers,
    start_date='2020-01-01',
    end_date='2024-01-01',
    refresh=False  # Use cached data if available
)
print(price_data.head())
```

### 3. Generate Momentum Signals

```python
from etfmomentum import generate_signals, config
import pandas as pd

# Your price data (DataFrame with date index and ticker columns)
price_data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)

# Generate signals
signals = generate_signals(
    price_data=price_data,
    benchmark_ticker='SPY',
    top_n=config.TOP_N_HOLDINGS,
    sma_window=config.SMA_LOOKBACK_DAYS,
    rs_roc_window=config.RS_ROC_LOOKBACK_DAYS,
)

# Signals DataFrame contains:
# - rs_ratio: Relative strength vs benchmark
# - sma_filter: True if above SMA trend
# - final_rank: Final ranking (1 = best)
print(signals.tail())
```

### 4. Run Backtest Programmatically

```python
from etfmomentum import run_backtest, get_rebalance_dates, config
from etfmomentum import load_universe_by_name, get_price_data
from datetime import datetime

# Setup
etf_universe = load_universe_by_name('sp500')
price_data = get_price_data(
    tickers=etf_universe.tickers,
    start_date='2016-01-01',
    end_date='2026-01-01',
)

# Get rebalance dates
rebalance_dates = get_rebalance_dates(
    start_date=datetime(2016, 1, 1),
    end_date=datetime(2026, 1, 1),
    frequency=config.REBALANCE_FREQUENCY,
)

# Run backtest
portfolio_history = run_backtest(
    price_data=price_data,
    rebalance_dates=rebalance_dates,
    benchmark_ticker='SPY',
    top_n=config.TOP_N_HOLDINGS,
    sma_window=config.SMA_LOOKBACK_DAYS,
    rs_roc_window=config.RS_ROC_LOOKBACK_DAYS,
)

# Portfolio history contains daily returns, holdings, etc.
print(f"Total Return: {portfolio_history['cumulative_returns'].iloc[-1]:.2%}")
```

### 5. Calculate Performance Metrics

```python
from etfmomentum import calculate_metrics, print_performance_summary
import pandas as pd

# Your portfolio returns (Series or DataFrame)
portfolio_returns = pd.Series([...])  # Daily returns
benchmark_returns = pd.Series([...])   # SPY returns

# Calculate metrics
metrics = calculate_metrics(
    portfolio_returns=portfolio_returns,
    benchmark_returns=benchmark_returns,
)

# Print formatted summary
print_performance_summary(metrics)

# Or access individual metrics
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Total Return: {metrics['total_return']:.2%}")
```

### 6. Volatility Regime Detection

```python
from etfmomentum import create_regime_detector, get_price_data

# Get SPY data
spy_data = get_price_data(
    tickers=['SPY'],
    start_date='2020-01-01',
    end_date='2024-01-01',
)

# Create regime detector
regime_detector = create_regime_detector(
    price_data=spy_data,
    ticker='SPY',
    use_vix=False,  # Use SPY volatility
)

# Detect current regime
current_regime = regime_detector.get_current_regime()
print(f"Current volatility regime: {current_regime}")
# Returns: "low", "medium", or "high"

# Adjust portfolio based on regime
if current_regime == "high":
    top_n = 5  # More diversification
else:
    top_n = 3  # Concentrated positions
```

### 7. Access Configuration

```python
from etfmomentum import config

# View current settings
print(f"Top N Holdings: {config.TOP_N_HOLDINGS}")
print(f"SMA Window: {config.SMA_LOOKBACK_DAYS}")
print(f"Momentum Window: {config.RS_ROC_LOOKBACK_DAYS}")
print(f"Rebalance Frequency: {config.REBALANCE_FREQUENCY}")

# Temporarily override for your project
config.TOP_N_HOLDINGS = 5
config.ENABLE_VOLATILITY_REGIME_SWITCHING = False

# Or create custom config
class MyConfig:
    TOP_N_HOLDINGS = 7
    SMA_LOOKBACK_DAYS = 180
    RS_ROC_LOOKBACK_DAYS = 90
```

---

## CLI Usage (After Installation)

Once installed, you can use CLI commands from anywhere:

```bash
# Generate current signals
etfmomentum signal --universe sp500 --detailed --refresh

# Run backtest
etfmomentum backtest --universe sp500 --refresh

# Custom date range
etfmomentum backtest --universe sp500 \
    --start-date 2020-01-01 \
    --end-date 2024-01-01 \
    --refresh

# Help
etfmomentum --help
etfmomentum signal --help
etfmomentum backtest --help
```

---

## Integration Example: Building a Custom Strategy

```python
"""
Example: Custom momentum strategy using etfmomentum library
"""
from etfmomentum import (
    load_universe_by_name,
    get_price_data,
    generate_signals,
    config,
)
import pandas as pd
from datetime import datetime, timedelta

class CustomMomentumStrategy:
    def __init__(self, universe='sp500', top_n=3):
        self.universe = universe
        self.top_n = top_n
        self.etf_universe = load_universe_by_name(universe)

    def get_latest_signals(self, lookback_days=365):
        """Get signals using last year of data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Get price data
        price_data = get_price_data(
            tickers=self.etf_universe.tickers,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            refresh=True,
        )

        # Generate signals
        signals = generate_signals(
            price_data=price_data,
            benchmark_ticker=config.BENCHMARK_TICKER,
            top_n=self.top_n,
            sma_window=config.SMA_LOOKBACK_DAYS,
            rs_roc_window=config.RS_ROC_LOOKBACK_DAYS,
        )

        return signals

    def get_portfolio_allocation(self):
        """Get current portfolio allocation."""
        signals = self.get_latest_signals()

        # Get top N ETFs
        top_etfs = signals[signals['final_rank'] <= self.top_n]

        # Equal weight allocation
        allocation = {
            ticker: 1.0 / self.top_n
            for ticker in top_etfs.index
        }

        return allocation

# Usage
if __name__ == "__main__":
    strategy = CustomMomentumStrategy(universe='sp500', top_n=3)
    allocation = strategy.get_portfolio_allocation()

    print("Current Portfolio Allocation:")
    for ticker, weight in allocation.items():
        print(f"  {ticker}: {weight:.1%}")
```

---

## Environment Setup

The package needs a `.env` file with your FMP API key. Make sure your other project can access it:

**Option 1: Copy .env to your project**
```bash
cp /Users/jaig/etfmomentum/.env /path/to/your/project/.env
```

**Option 2: Set environment variable**
```bash
export FMP_API_KEY="your_key_here"
```

**Option 3: Load from etfmomentum directory**
```python
from dotenv import load_dotenv
load_dotenv('/Users/jaig/etfmomentum/.env')
```

---

## Available Functions and Classes

### Core Functions
- `generate_signals()` - Generate momentum signals for ETFs
- `run_backtest()` - Run portfolio backtest
- `generate_current_signals()` - Get current buy signals
- `select_current_portfolio()` - Select top N holdings
- `get_rebalance_dates()` - Get rebalancing dates

### Data Functions
- `load_universe_by_name()` - Load ETF universe (sp500, emerging, developed)
- `get_price_data()` - Fetch historical price data

### Reporting Functions
- `calculate_metrics()` - Calculate performance metrics
- `generate_performance_summary()` - Generate summary report
- `print_performance_summary()` - Print formatted report

### Volatility Functions
- `create_regime_detector()` - Create volatility regime detector
- `VolatilityRegime` - Volatility regime class

### Configuration
- `config` - Module with all strategy parameters

---

## Testing Your Integration

```python
# Quick test to verify installation
try:
    import etfmomentum
    print(f"✓ etfmomentum version {etfmomentum.__version__}")

    # Test core imports
    from etfmomentum import (
        generate_signals,
        run_backtest,
        generate_current_signals,
        load_universe_by_name,
    )
    print("✓ All core functions imported successfully")

    # Test universe loading
    universe = load_universe_by_name('sp500')
    print(f"✓ Loaded {len(universe.tickers)} ETFs from sp500 universe")

    print("\n✅ Integration successful!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install -e /Users/jaig/etfmomentum")
```

---

## Troubleshooting

### Import Errors
```bash
# Reinstall in editable mode
pip uninstall etfmomentum
pip install -e /Users/jaig/etfmomentum
```

### Missing Dependencies
```bash
# Install from etfmomentum directory
cd /Users/jaig/etfmomentum
pip install -e .
```

### API Key Issues
Make sure `.env` file is accessible:
```python
import os
from pathlib import Path

env_path = Path('/Users/jaig/etfmomentum/.env')
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"FMP_API_KEY loaded: {bool(os.getenv('FMP_API_KEY'))}")
```

---

## Next Steps

1. Install the package: `pip install -e /Users/jaig/etfmomentum`
2. Test imports: Run the testing code above
3. Try examples: Start with `generate_current_signals()`
4. Build your integration: Use the functions in your project
5. Iterate: Changes to etfmomentum code reflect immediately!

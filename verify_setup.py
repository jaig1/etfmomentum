"""Verification script to test the backtest framework setup."""

import sys
from etfmomentum import config
from etfmomentum.data_fetcher import fetch_historical_data
from etfmomentum.rs_engine import calculate_rs_ratio, calculate_sma
import pandas as pd

print("="*70)
print("ETF RELATIVE STRENGTH BACKTEST - SETUP VERIFICATION")
print("="*70)

# Test 1: Configuration
print("\n[1/5] Testing configuration...")
try:
    assert config.FMP_API_KEY is not None, "API key not found"
    assert len(config.ETF_UNIVERSE) == 28, "ETF universe should have 28 tickers"
    assert config.BENCHMARK_TICKER == "SPY", "Benchmark should be SPY"
    print("✓ Configuration loaded successfully")
    print(f"  - {len(config.ETF_UNIVERSE)} ETFs configured")
    print(f"  - Benchmark: {config.BENCHMARK_TICKER}")
    print(f"  - Backtest period: {config.BACKTEST_START_DATE} to {config.BACKTEST_END_DATE}")
except AssertionError as e:
    print(f"✗ Configuration error: {e}")
    sys.exit(1)

# Test 2: API Connection
print("\n[2/5] Testing API connection...")
try:
    df = fetch_historical_data('SPY', '2025-01-01', '2025-01-31', config.FMP_API_KEY)
    assert not df.empty, "No data returned from API"
    assert len(df) > 0, "Empty dataset"
    print("✓ API connection successful")
    print(f"  - Fetched {len(df)} records for SPY (Jan 2025)")
except Exception as e:
    print(f"✗ API error: {e}")
    sys.exit(1)

# Test 3: RS Calculations
print("\n[3/5] Testing RS calculations...")
try:
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='D')
    etf_prices = pd.Series(range(100, 350), index=dates)
    spy_prices = pd.Series(range(200, 450), index=dates)

    rs_ratio = calculate_rs_ratio(etf_prices, spy_prices)
    assert len(rs_ratio) == 250, "RS ratio length mismatch"

    rs_sma = calculate_sma(rs_ratio, 200)
    assert len(rs_sma) == 250, "SMA length mismatch"

    print("✓ RS calculation functions working")
    print(f"  - RS ratio calculation: OK")
    print(f"  - SMA calculation: OK")
except Exception as e:
    print(f"✗ RS calculation error: {e}")
    sys.exit(1)

# Test 4: Directory Structure
print("\n[4/5] Testing directory structure...")
try:
    assert config.DATA_DIR.exists(), "data/ directory missing"
    assert config.OUTPUT_DIR.exists(), "output/ directory missing"
    print("✓ Directory structure correct")
    print(f"  - Data directory: {config.DATA_DIR}")
    print(f"  - Output directory: {config.OUTPUT_DIR}")
except AssertionError as e:
    print(f"✗ Directory error: {e}")
    sys.exit(1)

# Test 5: Module Imports
print("\n[5/5] Testing all module imports...")
try:
    from etfmomentum import config
    from etfmomentum import data_fetcher
    from etfmomentum import rs_engine
    from etfmomentum import backtest
    from etfmomentum import report
    from etfmomentum.main import main
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("ALL TESTS PASSED ✓")
print("="*70)
print("\nThe backtest framework is ready to run!")
print("\nTo execute the backtest, run:")
print("  uv run python -m etfmomentum")
print("\nFor more options:")
print("  uv run python -m etfmomentum --help")
print("="*70)

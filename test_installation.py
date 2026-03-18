"""
Quick test script to validate etfmomentum installation in another project.

PREREQUISITE: You must have FMP_API_KEY set in .env file or environment.
              The package will not import without it!

Usage:
    python test_installation.py
"""

def test_imports():
    """Test basic imports."""
    print("Testing imports...")
    try:
        import etfmomentum
        print(f"  ✓ Package version: {etfmomentum.__version__}")

        from etfmomentum import (
            generate_signals,
            run_backtest,
            generate_current_signals,
            load_universe_by_name,
            get_price_data,
            config,
        )
        print(f"  ✓ Core functions imported ({len(etfmomentum.__all__)} exports)")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration access."""
    print("\nTesting configuration...")
    try:
        from etfmomentum import config

        print(f"  ✓ TOP_N_HOLDINGS: {config.TOP_N_HOLDINGS}")
        print(f"  ✓ SMA_LOOKBACK_DAYS: {config.SMA_LOOKBACK_DAYS}")
        print(f"  ✓ RS_ROC_LOOKBACK_DAYS: {config.RS_ROC_LOOKBACK_DAYS}")
        print(f"  ✓ REBALANCE_FREQUENCY: {config.REBALANCE_FREQUENCY}")
        return True
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        return False


def test_universe_loading():
    """Test ETF universe loading."""
    print("\nTesting universe loading...")
    try:
        from etfmomentum import load_universe_by_name

        universe = load_universe_by_name('sp500')
        tickers = list(universe.keys())
        print(f"  ✓ Loaded sp500 universe: {len(tickers)} ETFs")
        print(f"  ✓ Sample tickers: {', '.join(tickers[:5])}")
        return True
    except Exception as e:
        print(f"  ✗ Universe loading failed: {e}")
        return False


def test_env_file():
    """Test environment configuration."""
    print("\nTesting environment...")
    import os

    api_key = os.getenv('FMP_API_KEY')
    if api_key:
        print(f"  ✓ FMP_API_KEY found (length: {len(api_key)})")
        return True
    else:
        print("  ⚠ FMP_API_KEY not found")
        print("    Set it in .env file or export FMP_API_KEY=your_key")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("ETF Momentum Installation Test")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("Universe", test_universe_loading()))
    results.append(("Environment", test_env_file()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! Package is ready to use.")
        print("\nNext steps:")
        print("  1. Try: from etfmomentum import generate_current_signals")
        print("  2. Run: etfmomentum signal --universe sp500 --refresh")
        print("  3. See: LIBRARY_USAGE.md for examples")
    else:
        print("⚠️  Some tests failed. Check errors above.")
        print("\nTo fix:")
        print("  pip install -e /Users/jaig/etfmomentum")
    print("=" * 60)


if __name__ == "__main__":
    main()

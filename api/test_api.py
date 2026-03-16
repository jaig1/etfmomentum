"""Test script for API endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Health check passed\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False


def test_dashboard():
    """Test dashboard endpoint."""
    print("Testing /api/dashboard endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard?universe=sp500")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Portfolio Value: ${data['portfolio_value']:,.2f}")
        print(f"YTD Return: {data['ytd_return']:.2f}%")
        print(f"Current Holdings: {len(data['current_holdings'])}")
        print("✅ Dashboard test passed\n")
        return True
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}\n")
        return False


def test_signals():
    """Test signals endpoint."""
    print("Testing /api/signals endpoint...")
    try:
        payload = {
            "universe": "sp500",
            "top_n": 3
        }
        response = requests.post(
            f"{BASE_URL}/api/signals",
            json=payload
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"As of Date: {data['as_of_date']}")
        print(f"Recommended Portfolio: {len(data['recommended_portfolio'])} holdings")
        print(f"Rebalancing Summary: {data['rebalancing_summary']}")
        print("✅ Signals test passed\n")
        return True
    except Exception as e:
        print(f"❌ Signals test failed: {e}\n")
        return False


def test_config():
    """Test config endpoint."""
    print("Testing /api/config endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/config")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available Universes: {data['universes']}")
        print(f"Default Top N: {data['default_top_n']}")
        print("✅ Config test passed\n")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}\n")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("ETF MOMENTUM STRATEGY - API TEST SUITE")
    print("=" * 70)
    print()

    print("Make sure the API server is running:")
    print("  uvicorn api.main:app --reload --port 8000")
    print()
    print("-" * 70)
    print()

    results = []
    results.append(("Health", test_health()))
    results.append(("Config", test_config()))
    results.append(("Dashboard", test_dashboard()))
    results.append(("Signals", test_signals()))

    print("-" * 70)
    print("SUMMARY:")
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")
    print("-" * 70)

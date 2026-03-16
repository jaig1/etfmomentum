"""Dashboard API routes."""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import sys
from pathlib import Path
import math

# Import from etfmomentum package
from etfmomentum import config
from etfmomentum.data_fetcher import get_price_data
from etfmomentum.rs_engine import generate_signals, get_qualifying_etfs
from etfmomentum.signal_generator import get_latest_trading_date
from etfmomentum.etf_loader import load_universe_by_name
from etfmomentum.backtest import run_backtest
from etfmomentum.report import calculate_metrics
from etfmomentum.volatility_regime import create_regime_detector

from api.models.schemas import DashboardResponse, HoldingItem

router = APIRouter()


def sanitize_float(value):
    """Convert NaN and Infinity to None or 0.0 for JSON serialization."""
    if value is None:
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    universe: str = Query("sp500", description="ETF universe")
):
    """
    Get dashboard data including portfolio overview, current holdings, and YTD summary.
    """
    try:
        # Load ETF universe
        etf_universe = load_universe_by_name(universe, config.ETFLIST_DIR)
        etf_tickers = list(etf_universe.keys())

        # Get price data - use cached data
        all_tickers = etf_tickers + [config.BENCHMARK_TICKER]

        price_data = get_price_data(
            ticker_list=all_tickers,
            start_date=config.DATA_START_DATE,
            end_date=config.BACKTEST_END_DATE,
            api_key=config.FMP_API_KEY,
            cache_path=str(config.PRICE_DATA_CACHE),
            force_refresh=False,  # Use cache for dashboard
            api_delay=config.FMP_API_DELAY,
        )

        # Calculate YTD dates dynamically
        from datetime import datetime
        current_year = datetime.now().year
        ytd_start = f"{current_year}-01-01"

        # Generate signals
        signals = generate_signals(
            price_data=price_data,
            spy_ticker=config.BENCHMARK_TICKER,
            etf_tickers=etf_tickers,
            sma_window=config.SMA_LOOKBACK_DAYS,
            roc_lookback=config.RS_ROC_LOOKBACK_DAYS,
        )

        # Get latest date
        latest_date = get_latest_trading_date(price_data)

        # Get current holdings
        qualifying = get_qualifying_etfs(signals, latest_date)
        current_holdings = []

        if len(qualifying) >= config.TOP_N_HOLDINGS:
            selected = qualifying.head(config.TOP_N_HOLDINGS)
            for _, row in selected.iterrows():
                current_holdings.append(HoldingItem(
                    rank=int(row['rank']),
                    ticker=row['ticker'],
                    name=etf_universe.get(row['ticker'], row['ticker']),
                    weight=1.0 / config.TOP_N_HOLDINGS,
                    rs_roc=sanitize_float(row['rs_roc'])
                ))

        # Run YTD backtest to get performance metrics
        regime_detector = create_regime_detector(config) if config.ENABLE_VOLATILITY_REGIME_SWITCHING else None

        # Use YTD dates for dashboard backtest
        latest_date_str = latest_date.strftime("%Y-%m-%d")

        strategy_values, benchmark_values, rebalance_log = run_backtest(
            signals=signals,
            price_data=price_data,
            spy_ticker=config.BENCHMARK_TICKER,
            start_date=ytd_start,
            end_date=latest_date_str,
            initial_capital=config.INITIAL_CAPITAL,
            top_n=config.TOP_N_HOLDINGS,
            regime_detector=regime_detector,
            rebalance_frequency=config.REBALANCE_FREQUENCY,
        )

        # Calculate metrics
        strategy_metrics = calculate_metrics(
            portfolio_values=strategy_values['portfolio_value'],
            initial_capital=config.INITIAL_CAPITAL,
            risk_free_rate=config.RISK_FREE_RATE,
        )

        benchmark_metrics = calculate_metrics(
            portfolio_values=benchmark_values['portfolio_value'],
            initial_capital=config.INITIAL_CAPITAL,
            risk_free_rate=config.RISK_FREE_RATE,
        )

        # Get volatility regime
        regime_info = "MEDIUM_VOLATILITY"
        if regime_detector:
            regime = regime_detector.detect_regime(price_data[config.BENCHMARK_TICKER], latest_date)
            regime_params = regime_detector.get_regime_parameters(regime)
            regime_info = regime_params['regime']

        # Calculate YTD summary (monthly breakdown)
        ytd_summary = []
        strategy_returns = strategy_values['portfolio_value'].pct_change()
        benchmark_returns = benchmark_values['portfolio_value'].pct_change()

        # Group by month
        strategy_monthly = strategy_values['portfolio_value'].resample('ME').last().pct_change()
        benchmark_monthly = benchmark_values['portfolio_value'].resample('ME').last().pct_change()

        for date_idx, strategy_ret in strategy_monthly.items():
            if date_idx in benchmark_monthly.index:
                bench_ret = benchmark_monthly.loc[date_idx]
                ytd_summary.append({
                    "month": date_idx.strftime("%B %Y"),
                    "strategy_return": sanitize_float(strategy_ret * 100),
                    "spy_return": sanitize_float(bench_ret * 100),
                    "outperformance": sanitize_float((strategy_ret - bench_ret) * 100)
                })

        # Return dashboard data
        return DashboardResponse(
            as_of_date=latest_date.strftime("%Y-%m-%d"),
            universe=universe.upper(),
            portfolio_value=sanitize_float(strategy_values['portfolio_value'].iloc[-1]),
            ytd_return=sanitize_float(strategy_metrics['total_return'] * 100),
            spy_value=sanitize_float(benchmark_values['portfolio_value'].iloc[-1]),
            spy_return=sanitize_float(benchmark_metrics['total_return'] * 100),
            outperformance=sanitize_float((strategy_metrics['total_return'] - benchmark_metrics['total_return']) * 100),
            sharpe_ratio=sanitize_float(strategy_metrics['sharpe_ratio']),
            max_drawdown=sanitize_float(strategy_metrics['max_drawdown'] * 100),
            volatility_regime=regime_info,
            current_holdings=current_holdings,
            ytd_summary=ytd_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard data: {str(e)}")

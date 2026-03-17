"""Backtest API routes."""

from fastapi import APIRouter, HTTPException
import math

from etfmomentum import config as etf_config
from etfmomentum.data_fetcher import get_price_data
from etfmomentum.rs_engine import generate_signals
from etfmomentum.etf_loader import load_universe_by_name
from etfmomentum.backtest import run_backtest
from etfmomentum.report import calculate_metrics
from etfmomentum.volatility_regime import create_regime_detector

from api.models.schemas import BacktestRequest, BacktestResponse, YearlyPerformance

router = APIRouter()


def sanitize_float(value):
    """Convert NaN and Infinity to None or 0.0 for JSON serialization."""
    if value is None:
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest_analysis(request: BacktestRequest):
    """
    Run historical backtest with specified parameters.
    """
    try:
        # Load ETF universe
        etf_universe = load_universe_by_name(request.universe, etf_config.ETFLIST_DIR)
        etf_tickers = list(etf_universe.keys())

        # Calculate data start date (need buffer for SMA)
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(request.start_date, "%Y-%m-%d")
        data_start_date = (start_dt - timedelta(days=250)).strftime("%Y-%m-%d")

        # Get price data
        all_tickers = etf_tickers + [etf_config.BENCHMARK_TICKER]

        # Add VIX if needed
        if request.enable_volatility_regime and etf_config.USE_VIX_FOR_REGIME:
            all_tickers.append(etf_config.VIX_TICKER)

        price_data = get_price_data(
            ticker_list=all_tickers,
            start_date=data_start_date,
            end_date=request.end_date,
            api_key=etf_config.FMP_API_KEY,
            cache_path=str(etf_config.PRICE_DATA_CACHE),
            force_refresh=True,  # Always fetch fresh data (no caching)
            api_delay=etf_config.FMP_API_DELAY,
        )

        # Generate signals
        signals = generate_signals(
            price_data=price_data,
            spy_ticker=etf_config.BENCHMARK_TICKER,
            etf_tickers=etf_tickers,
            sma_window=etf_config.SMA_LOOKBACK_DAYS,
            roc_lookback=etf_config.RS_ROC_LOOKBACK_DAYS,
        )

        # Create regime detector if enabled
        regime_detector = None
        if request.enable_volatility_regime:
            regime_detector = create_regime_detector(etf_config)

        # Run backtest
        strategy_values, benchmark_values, rebalance_log = run_backtest(
            signals=signals,
            price_data=price_data,
            spy_ticker=etf_config.BENCHMARK_TICKER,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            top_n=request.top_n,
            regime_detector=regime_detector,
            rebalance_frequency=request.rebalance_frequency,
        )

        # Calculate metrics
        strategy_metrics = calculate_metrics(
            portfolio_values=strategy_values['portfolio_value'],
            initial_capital=request.initial_capital,
            risk_free_rate=etf_config.RISK_FREE_RATE,
        )

        benchmark_metrics = calculate_metrics(
            portfolio_values=benchmark_values['portfolio_value'],
            initial_capital=request.initial_capital,
            risk_free_rate=etf_config.RISK_FREE_RATE,
        )

        # Calculate yearly breakdown
        strategy_yearly = strategy_values['portfolio_value'].resample('YE').last().pct_change()
        benchmark_yearly = benchmark_values['portfolio_value'].resample('YE').last().pct_change()

        yearly_breakdown = []
        for date_idx, strategy_ret in strategy_yearly.items():
            if date_idx in benchmark_yearly.index:
                bench_ret = benchmark_yearly.loc[date_idx]
                yearly_breakdown.append(YearlyPerformance(
                    year=date_idx.year,
                    strategy_return=sanitize_float(strategy_ret * 100),
                    spy_return=sanitize_float(bench_ret * 100),
                    outperformance=sanitize_float((strategy_ret - bench_ret) * 100)
                ))

        # Calculate win rate
        wins = sum(1 for yp in yearly_breakdown if yp.outperformance > 0)
        win_rate = (wins / len(yearly_breakdown) * 100) if yearly_breakdown else 0.0

        return BacktestResponse(
            universe=request.universe.upper(),
            start_date=request.start_date,
            end_date=request.end_date,
            total_return=sanitize_float(strategy_metrics['total_return'] * 100),
            annualized_return=sanitize_float(strategy_metrics['annualized_return'] * 100),
            sharpe_ratio=sanitize_float(strategy_metrics['sharpe_ratio']),
            max_drawdown=sanitize_float(strategy_metrics['max_drawdown'] * 100),
            final_value=sanitize_float(strategy_values['portfolio_value'].iloc[-1]),
            spy_total_return=sanitize_float(benchmark_metrics['total_return'] * 100),
            spy_annualized_return=sanitize_float(benchmark_metrics['annualized_return'] * 100),
            spy_sharpe_ratio=sanitize_float(benchmark_metrics['sharpe_ratio']),
            spy_max_drawdown=sanitize_float(benchmark_metrics['max_drawdown'] * 100),
            spy_final_value=sanitize_float(benchmark_values['portfolio_value'].iloc[-1]),
            outperformance=sanitize_float((strategy_metrics['total_return'] - benchmark_metrics['total_return']) * 100),
            yearly_breakdown=yearly_breakdown,
            win_rate=sanitize_float(win_rate)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

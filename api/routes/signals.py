"""Signal generation API routes."""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from etfmomentum import config
from etfmomentum.data_fetcher import get_price_data
from etfmomentum.rs_engine import generate_signals, get_qualifying_etfs, get_all_etf_status
from etfmomentum.signal_generator import calculate_signal_data_dates, get_latest_trading_date
from etfmomentum.etf_loader import load_universe_by_name

from api.models.schemas import SignalRequest, SignalResponse, HoldingItem, RebalancingAction, ETFStatus

router = APIRouter()


@router.post("/signals", response_model=SignalResponse)
async def generate_current_signals(request: SignalRequest):
    """
    Generate current portfolio signals with rebalancing recommendations.
    """
    try:
        # Load ETF universe
        etf_universe = load_universe_by_name(request.universe, config.ETFLIST_DIR)
        etf_tickers = list(etf_universe.keys())

        # Calculate data dates
        start_date, end_date = calculate_signal_data_dates(config.SIGNAL_DATA_LOOKBACK_DAYS)

        # Get price data (always refresh for signals)
        all_tickers = etf_tickers + [config.BENCHMARK_TICKER]
        price_data = get_price_data(
            ticker_list=all_tickers,
            start_date=start_date,
            end_date=end_date,
            api_key=config.FMP_API_KEY,
            cache_path=str(config.PRICE_DATA_CACHE),
            force_refresh=True,  # Always refresh for signals
            api_delay=config.FMP_API_DELAY,
        )

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

        # Get qualifying ETFs
        qualifying = get_qualifying_etfs(signals, latest_date)

        # Build recommended portfolio
        recommended_portfolio = []
        if len(qualifying) >= request.top_n:
            selected = qualifying.head(request.top_n)
            weight = 1.0 / request.top_n
            for _, row in selected.iterrows():
                recommended_portfolio.append(HoldingItem(
                    rank=int(row['rank']),
                    ticker=row['ticker'],
                    name=etf_universe.get(row['ticker'], row['ticker']),
                    weight=weight,
                    rs_roc=float(row['rs_roc'])
                ))

        # Get current holdings (mock for now - in real app, would come from user's portfolio)
        # For demo purposes, assume current holdings are same as recommended
        current_holdings = {item.ticker: item.weight for item in recommended_portfolio}
        recommended_holdings = {item.ticker: item.weight for item in recommended_portfolio}

        # Calculate rebalancing actions
        rebalancing_actions = []
        all_tickers_set = set(list(current_holdings.keys()) + list(recommended_holdings.keys()))

        for ticker in all_tickers_set:
            current_w = current_holdings.get(ticker, 0.0)
            recommended_w = recommended_holdings.get(ticker, 0.0)

            if current_w == recommended_w:
                action = "HOLD"
            elif current_w > 0 and recommended_w == 0:
                action = f"SELL {current_w:.1%}"
            elif current_w == 0 and recommended_w > 0:
                action = f"BUY {recommended_w:.1%}"
            elif current_w != recommended_w:
                diff = recommended_w - current_w
                action = f"{'BUY' if diff > 0 else 'SELL'} {abs(diff):.1%}"
            else:
                action = "HOLD"

            rebalancing_actions.append(RebalancingAction(
                ticker=ticker,
                current_weight=current_w,
                recommended_weight=recommended_w,
                action=action
            ))

        # Determine rebalancing summary
        needs_rebalancing = any(action.action != "HOLD" for action in rebalancing_actions)
        rebalancing_summary = "No rebalancing needed - portfolio is optimal" if not needs_rebalancing else "Rebalancing required"

        # Get all ETF status
        all_status = get_all_etf_status(signals, latest_date)
        etf_status_list = []

        for _, row in all_status.iterrows():
            etf_status_list.append(ETFStatus(
                ticker=row['ticker'],
                price=float(row['price']) if not pd.isna(row['price']) else 0.0,
                rs_ratio=float(row['rs_ratio']) if not pd.isna(row['rs_ratio']) else 0.0,
                rs_filter=bool(row['rs_filter']),
                abs_filter=bool(row['abs_filter']),
                rs_roc=float(row['rs_roc']) if not pd.isna(row['rs_roc']) else 0.0,
                rank=int(row['rank']) if not pd.isna(row['rank']) else None
            ))

        return SignalResponse(
            as_of_date=latest_date.strftime("%Y-%m-%d"),
            universe=request.universe.upper(),
            recommended_portfolio=recommended_portfolio,
            rebalancing_actions=rebalancing_actions,
            rebalancing_summary=rebalancing_summary,
            all_etf_status=etf_status_list
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signals: {str(e)}")


import pandas as pd

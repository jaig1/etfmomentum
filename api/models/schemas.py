"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


# Request Models

class SignalRequest(BaseModel):
    """Request model for signal generation."""
    universe: str = Field(..., description="ETF universe (sp500, emerging, developed)")
    top_n: int = Field(3, description="Number of top holdings", ge=1, le=10)


class BacktestRequest(BaseModel):
    """Request model for backtest execution."""
    universe: str = Field(..., description="ETF universe")
    start_date: str = Field(..., description="Backtest start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Backtest end date (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, description="Initial capital", ge=1000)
    top_n: int = Field(3, description="Number of top holdings", ge=1, le=10)
    rebalance_frequency: str = Field("weekly", description="Rebalance frequency (weekly/monthly)")
    enable_volatility_regime: bool = Field(True, description="Enable volatility regime switching")
    refresh_data: bool = Field(True, description="Force refresh data from API")


# Response Models

class HoldingItem(BaseModel):
    """Individual holding in portfolio."""
    rank: int
    ticker: str
    name: str
    weight: float
    rs_roc: float


class RebalancingAction(BaseModel):
    """Rebalancing action for a ticker."""
    ticker: str
    current_weight: float
    recommended_weight: float
    action: str  # HOLD, BUY, SELL


class ETFStatus(BaseModel):
    """Status of individual ETF."""
    ticker: str
    price: float
    rs_ratio: float
    rs_filter: bool
    abs_filter: bool
    rs_roc: float
    rank: Optional[int] = None


class DashboardResponse(BaseModel):
    """Response model for dashboard data."""
    as_of_date: str
    universe: str
    portfolio_value: float
    ytd_return: float
    spy_value: float
    spy_return: float
    outperformance: float
    sharpe_ratio: float
    max_drawdown: float
    volatility_regime: str
    current_holdings: List[HoldingItem]
    ytd_summary: List[Dict[str, Any]]


class SignalResponse(BaseModel):
    """Response model for signal generation."""
    as_of_date: str
    universe: str
    recommended_portfolio: List[HoldingItem]
    rebalancing_actions: List[RebalancingAction]
    rebalancing_summary: str
    all_etf_status: List[ETFStatus]


class YearlyPerformance(BaseModel):
    """Yearly performance breakdown."""
    year: int
    strategy_return: float
    spy_return: float
    outperformance: float


class BacktestResponse(BaseModel):
    """Response model for backtest results."""
    universe: str
    start_date: str
    end_date: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    final_value: float
    spy_total_return: float
    spy_annualized_return: float
    spy_sharpe_ratio: float
    spy_max_drawdown: float
    spy_final_value: float
    outperformance: float
    yearly_breakdown: List[YearlyPerformance]
    win_rate: float


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    universes: List[str]
    default_top_n: int
    rebalance_frequencies: List[str]
    sma_lookback_days: int
    rs_roc_lookback_days: int
    volatility_regime_enabled: bool

"""Volatility regime detection and parameter adjustment."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class VolatilityRegime:
    """Detect market volatility regime and adjust strategy parameters."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def __init__(
        self,
        lookback_days: int,
        low_vol_threshold: float,
        high_vol_threshold: float,
        low_vol_top_n: int,
        medium_vol_top_n: int,
        high_vol_top_n: int,
        high_vol_spy_allocation: float,
    ):
        """
        Initialize volatility regime detector.

        Args:
            lookback_days: Days to calculate volatility
            low_vol_threshold: Threshold for low volatility (annualized)
            high_vol_threshold: Threshold for high volatility (annualized)
            low_vol_top_n: Number of holdings in low vol regime
            medium_vol_top_n: Number of holdings in medium vol regime
            high_vol_top_n: Number of holdings in high vol regime
            high_vol_spy_allocation: Minimum SPY allocation in high vol
        """
        self.lookback_days = lookback_days
        self.low_vol_threshold = low_vol_threshold
        self.high_vol_threshold = high_vol_threshold
        self.low_vol_top_n = low_vol_top_n
        self.medium_vol_top_n = medium_vol_top_n
        self.high_vol_top_n = high_vol_top_n
        self.high_vol_spy_allocation = high_vol_spy_allocation

    def calculate_volatility(
        self,
        price_series: pd.Series,
        date: pd.Timestamp,
    ) -> float:
        """
        Calculate annualized volatility for a given date.

        Args:
            price_series: Price series (e.g., SPY)
            date: Date to calculate volatility for

        Returns:
            Annualized volatility
        """
        # Get data up to the date
        data = price_series.loc[:date]

        # Need enough data
        if len(data) < self.lookback_days + 1:
            logger.warning(f"Insufficient data for volatility calculation at {date}")
            return np.nan

        # Get last N days
        recent_data = data.tail(self.lookback_days + 1)

        # Calculate daily returns
        returns = recent_data.pct_change().dropna()

        if len(returns) < self.lookback_days:
            return np.nan

        # Calculate annualized volatility
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(252)  # 252 trading days

        return annualized_vol

    def detect_regime(
        self,
        spy_prices: pd.Series,
        date: pd.Timestamp,
    ) -> str:
        """
        Detect current volatility regime.

        Args:
            spy_prices: SPY price series
            date: Date to detect regime for

        Returns:
            Regime string: 'low', 'medium', or 'high'
        """
        vol = self.calculate_volatility(spy_prices, date)

        if pd.isna(vol):
            logger.warning(f"Could not calculate volatility for {date}, defaulting to medium")
            return self.MEDIUM

        if vol < self.low_vol_threshold:
            regime = self.LOW
        elif vol > self.high_vol_threshold:
            regime = self.HIGH
        else:
            regime = self.MEDIUM

        logger.debug(f"{date.date()}: Volatility={vol:.2%}, Regime={regime}")

        return regime

    def get_regime_parameters(
        self,
        regime: str,
    ) -> Dict[str, any]:
        """
        Get strategy parameters for a given regime.

        Args:
            regime: Volatility regime ('low', 'medium', 'high')

        Returns:
            Dictionary with regime-specific parameters
        """
        if regime == self.LOW:
            return {
                'top_n': self.low_vol_top_n,
                'min_spy_allocation': 0.0,
                'regime': 'LOW_VOLATILITY',
            }
        elif regime == self.HIGH:
            return {
                'top_n': self.high_vol_top_n,
                'min_spy_allocation': self.high_vol_spy_allocation,
                'regime': 'HIGH_VOLATILITY',
            }
        else:  # MEDIUM
            return {
                'top_n': self.medium_vol_top_n,
                'min_spy_allocation': 0.0,
                'regime': 'MEDIUM_VOLATILITY',
            }

    def adjust_portfolio_for_regime(
        self,
        portfolio: Dict[str, float],
        regime_params: Dict[str, any],
        spy_ticker: str,
    ) -> Dict[str, float]:
        """
        Adjust portfolio allocation based on regime parameters.

        Args:
            portfolio: Initial portfolio allocation
            regime_params: Regime parameters from get_regime_parameters()
            spy_ticker: SPY ticker symbol

        Returns:
            Adjusted portfolio allocation
        """
        min_spy_allocation = regime_params['min_spy_allocation']

        # If no minimum SPY allocation required, return as-is
        if min_spy_allocation == 0.0:
            return portfolio

        # Calculate current SPY allocation
        current_spy = portfolio.get(spy_ticker, 0.0)

        # If already above minimum, no adjustment needed
        if current_spy >= min_spy_allocation:
            return portfolio

        # Need to add SPY allocation
        additional_spy_needed = min_spy_allocation - current_spy

        # Scale down other holdings proportionally
        other_holdings = {k: v for k, v in portfolio.items() if k != spy_ticker}
        total_other = sum(other_holdings.values())

        if total_other == 0:
            # Edge case: no other holdings, just allocate to SPY
            return {spy_ticker: 1.0}

        # Scale factor for other holdings
        scale_factor = (1.0 - min_spy_allocation) / total_other

        # Create adjusted portfolio
        adjusted = {}
        for ticker, weight in other_holdings.items():
            adjusted[ticker] = weight * scale_factor

        adjusted[spy_ticker] = min_spy_allocation

        return adjusted


def create_regime_detector(config) -> VolatilityRegime:
    """
    Create volatility regime detector from config.

    Args:
        config: Configuration module

    Returns:
        VolatilityRegime instance
    """
    return VolatilityRegime(
        lookback_days=config.VOLATILITY_LOOKBACK_DAYS,
        low_vol_threshold=config.LOW_VOL_THRESHOLD,
        high_vol_threshold=config.HIGH_VOL_THRESHOLD,
        low_vol_top_n=config.LOW_VOL_TOP_N,
        medium_vol_top_n=config.MEDIUM_VOL_TOP_N,
        high_vol_top_n=config.HIGH_VOL_TOP_N,
        high_vol_spy_allocation=config.HIGH_VOL_SPY_MIN_ALLOCATION,
    )

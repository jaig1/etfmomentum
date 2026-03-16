"""Volatility regime detection and parameter adjustment."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any
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
        use_vix: bool = False,
        vix_smoothing_days: int = 5,
        vix_current_weight: float = 0.3,
        vix_low_threshold: float = 14,
        vix_high_enter: float = 26,
        vix_high_exit: float = 20,
        vix_low_exit: float = 16,
        defensive_mode: str = None,
        defensive_sectors: list = None,
        tbill_ticker: str = None,
        tbill_allocation: float = 0.50,
        extreme_vol_threshold: float = 0.35,
    ):
        """
        Initialize volatility regime detector.

        Args:
            lookback_days: Days to calculate volatility (SPY-based)
            low_vol_threshold: Threshold for low volatility (annualized, SPY-based)
            high_vol_threshold: Threshold for high volatility (annualized, SPY-based)
            low_vol_top_n: Number of holdings in low vol regime
            medium_vol_top_n: Number of holdings in medium vol regime
            high_vol_top_n: Number of holdings in high vol regime
            high_vol_spy_allocation: Minimum SPY allocation in high vol
            use_vix: Use VIX ticker (True) or calculate from SPY (False)
            vix_smoothing_days: Days to average VIX readings
            vix_current_weight: Weight for current VIX vs average (0-1)
            vix_low_threshold: VIX threshold for LOW regime
            vix_high_enter: VIX threshold to enter HIGH regime
            vix_high_exit: VIX threshold to exit HIGH regime (hysteresis)
            vix_low_exit: VIX threshold to exit LOW regime (hysteresis)
            defensive_mode: Defensive allocation mode ('baseline', 'defensive_sectors', 'tbills', 'hybrid', 'tiered', None)
            defensive_sectors: List of defensive sector tickers (e.g., ['XLP', 'XLU', 'XLV'])
            tbill_ticker: T-Bill ETF ticker (e.g., 'BIL', 'SGOV')
            tbill_allocation: Allocation to T-Bills in hybrid mode (0-1)
            extreme_vol_threshold: Volatility threshold for extreme regime in tiered mode
        """
        # SPY-based parameters
        self.lookback_days = lookback_days
        self.low_vol_threshold = low_vol_threshold
        self.high_vol_threshold = high_vol_threshold

        # VIX-based parameters
        self.use_vix = use_vix
        self.vix_smoothing_days = vix_smoothing_days
        self.vix_current_weight = vix_current_weight
        self.vix_avg_weight = 1.0 - vix_current_weight
        self.vix_low_threshold = vix_low_threshold
        self.vix_high_enter = vix_high_enter
        self.vix_high_exit = vix_high_exit
        self.vix_low_exit = vix_low_exit

        # Strategy parameters
        self.low_vol_top_n = low_vol_top_n
        self.medium_vol_top_n = medium_vol_top_n
        self.high_vol_top_n = high_vol_top_n
        self.high_vol_spy_allocation = high_vol_spy_allocation

        # State tracking for hysteresis
        self.current_regime = self.MEDIUM  # Start in medium regime

        # Defensive allocation parameters
        self.defensive_mode = defensive_mode  # None, 'baseline', 'defensive_sectors', 'tbills', 'hybrid', 'tiered'
        self.defensive_sectors = defensive_sectors or []
        self.tbill_ticker = tbill_ticker
        self.tbill_allocation = tbill_allocation
        self.extreme_vol_threshold = extreme_vol_threshold

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

    def calculate_vix_smoothed(
        self,
        vix_prices: pd.Series,
        date: pd.Timestamp,
    ) -> float:
        """
        Calculate smoothed VIX value using trailing average + current.

        Args:
            vix_prices: VIX price series
            date: Date to calculate for

        Returns:
            Smoothed VIX value
        """
        # Get data up to the date
        data = vix_prices.loc[:date]

        # Need enough data
        if len(data) < self.vix_smoothing_days + 1:
            logger.warning(f"Insufficient VIX data for smoothing at {date}")
            return vix_prices.loc[date] if date in vix_prices.index else np.nan

        # Get recent window
        recent_data = data.tail(self.vix_smoothing_days + 1)

        # Current VIX
        vix_current = recent_data.iloc[-1]

        # Average VIX over smoothing period
        vix_avg = recent_data.iloc[:-1].mean()  # Exclude current day from average

        # Weighted combination
        vix_smoothed = self.vix_avg_weight * vix_avg + self.vix_current_weight * vix_current

        return vix_smoothed

    def detect_regime_vix(
        self,
        vix_prices: pd.Series,
        date: pd.Timestamp,
    ) -> str:
        """
        Detect regime using VIX with hysteresis.

        Args:
            vix_prices: VIX price series
            date: Date to detect regime for

        Returns:
            Regime string: 'low', 'medium', or 'high'
        """
        vix_smoothed = self.calculate_vix_smoothed(vix_prices, date)

        if pd.isna(vix_smoothed):
            logger.warning(f"Could not calculate VIX for {date}, staying in {self.current_regime}")
            return self.current_regime

        # Apply hysteresis based on current regime
        if self.current_regime == self.MEDIUM:
            # In MEDIUM, check if we should transition
            if vix_smoothed > self.vix_high_enter:
                new_regime = self.HIGH
            elif vix_smoothed < self.vix_low_threshold:
                new_regime = self.LOW
            else:
                new_regime = self.MEDIUM

        elif self.current_regime == self.HIGH:
            # In HIGH, need VIX to drop below exit threshold to leave
            if vix_smoothed < self.vix_high_exit:
                new_regime = self.MEDIUM
            else:
                new_regime = self.HIGH

        elif self.current_regime == self.LOW:
            # In LOW, need VIX to rise above exit threshold to leave
            if vix_smoothed > self.vix_low_exit:
                new_regime = self.MEDIUM
            else:
                new_regime = self.LOW
        else:
            new_regime = self.MEDIUM

        # Update state
        self.current_regime = new_regime

        logger.debug(f"{date.date()}: VIX_smoothed={vix_smoothed:.1f}, Regime={new_regime}")

        return new_regime

    def detect_regime(
        self,
        spy_prices: pd.Series,
        date: pd.Timestamp,
        vix_prices: pd.Series = None,
    ) -> str:
        """
        Detect current volatility regime.

        Args:
            spy_prices: SPY price series
            date: Date to detect regime for
            vix_prices: VIX price series (optional, required if use_vix=True)

        Returns:
            Regime string: 'low', 'medium', or 'high'
        """
        if self.use_vix:
            if vix_prices is None:
                logger.error("VIX prices required when use_vix=True, falling back to SPY calculation")
                return self._detect_regime_spy(spy_prices, date)
            return self.detect_regime_vix(vix_prices, date)
        else:
            return self._detect_regime_spy(spy_prices, date)

    def _detect_regime_spy(
        self,
        spy_prices: pd.Series,
        date: pd.Timestamp,
    ) -> str:
        """
        Detect regime using calculated SPY volatility (original method).

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

        logger.debug(f"{date.date()}: SPY_Volatility={vol:.2%}, Regime={regime}")

        return regime

    def get_regime_parameters(
        self,
        regime: str,
    ) -> Dict[str, Any]:
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
        regime_params: Dict[str, Any],
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

    def is_extreme_volatility(
        self,
        spy_prices: pd.Series,
        date: pd.Timestamp,
    ) -> bool:
        """
        Check if volatility is at extreme levels (for tiered mode).

        Args:
            spy_prices: SPY price series
            date: Date to check

        Returns:
            True if extreme volatility, False otherwise
        """
        vol = self.calculate_volatility(spy_prices, date)

        if pd.isna(vol):
            return False

        return vol > self.extreme_vol_threshold

    def get_defensive_portfolio_allocation(
        self,
        regime: str,
        qualifying_etfs: pd.DataFrame,
        spy_prices: pd.Series,
        date: pd.Timestamp,
    ) -> Dict[str, Any]:
        """
        Get defensive portfolio allocation based on regime and mode.

        Args:
            regime: Current volatility regime
            qualifying_etfs: DataFrame of qualifying ETFs with RS scores
            spy_prices: SPY price series (for extreme vol check)
            date: Current date

        Returns:
            Dictionary with 'mode' and 'tickers' for defensive allocation
            Returns None if no defensive override needed
        """
        # Only apply defensive logic in HIGH volatility regime
        if regime != self.HIGH:
            return None

        # No defensive mode specified - use baseline behavior
        if self.defensive_mode is None or self.defensive_mode == 'baseline':
            return None

        # Check for extreme volatility (for tiered mode)
        is_extreme = False
        if self.defensive_mode == 'tiered':
            is_extreme = self.is_extreme_volatility(spy_prices, date)

        # Determine allocation based on mode
        if self.defensive_mode == 'defensive_sectors':
            # Force allocation to defensive sectors, ranked by RS
            return {
                'mode': 'defensive_sectors',
                'tickers': self.defensive_sectors,
                'rank_by_rs': True,
                'equal_weight': False,
            }

        elif self.defensive_mode == 'tbills':
            # 100% T-Bills
            return {
                'mode': 'tbills',
                'tickers': [self.tbill_ticker],
                'allocation': {self.tbill_ticker: 1.0},
            }

        elif self.defensive_mode == 'hybrid':
            # 50% T-Bills + 50% defensive sectors (equal-weight)
            return {
                'mode': 'hybrid',
                'tbill_ticker': self.tbill_ticker,
                'tbill_allocation': self.tbill_allocation,
                'defensive_sectors': self.defensive_sectors,
                'sector_allocation': 1.0 - self.tbill_allocation,
            }

        elif self.defensive_mode == 'tiered':
            if is_extreme:
                # Extreme volatility: 100% T-Bills
                return {
                    'mode': 'tiered_extreme',
                    'tickers': [self.tbill_ticker],
                    'allocation': {self.tbill_ticker: 1.0},
                }
            else:
                # High (not extreme): Defensive sectors
                return {
                    'mode': 'tiered_high',
                    'tickers': self.defensive_sectors,
                    'rank_by_rs': True,
                    'equal_weight': False,
                }

        return None


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
        use_vix=config.USE_VIX_FOR_REGIME,
        vix_smoothing_days=config.VIX_SMOOTHING_DAYS,
        vix_current_weight=config.VIX_CURRENT_WEIGHT,
        vix_low_threshold=config.VIX_LOW_THRESHOLD,
        vix_high_enter=config.VIX_HIGH_ENTER_THRESHOLD,
        vix_high_exit=config.VIX_HIGH_EXIT_THRESHOLD,
        vix_low_exit=config.VIX_LOW_EXIT_THRESHOLD,
    )


# Alias for backward compatibility and clarity
VolatilityRegimeDetector = VolatilityRegime

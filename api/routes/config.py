"""Configuration API routes."""

from fastapi import APIRouter

from etfmomentum import config as etf_config
from api.models.schemas import ConfigResponse

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
async def get_configuration():
    """
    Get current strategy configuration and available options.
    """
    return ConfigResponse(
        universes=["sp500", "emerging", "developed"],
        default_top_n=etf_config.TOP_N_HOLDINGS,
        rebalance_frequencies=["weekly", "monthly"],
        sma_lookback_days=etf_config.SMA_LOOKBACK_DAYS,
        rs_roc_lookback_days=etf_config.RS_ROC_LOOKBACK_DAYS,
        volatility_regime_enabled=etf_config.ENABLE_VOLATILITY_REGIME_SWITCHING
    )


@router.get("/universes")
async def get_universes():
    """
    Get list of available ETF universes.
    """
    return {
        "universes": [
            {
                "id": "sp500",
                "name": "S&P 500 Sectors",
                "description": "11 SPDR sector ETFs",
                "count": 11
            },
            {
                "id": "emerging",
                "name": "Emerging Markets",
                "description": "28 country/regional ETFs",
                "count": 28
            },
            {
                "id": "developed",
                "name": "Developed Markets",
                "description": "26 iShares country ETFs",
                "count": 26
            }
        ]
    }

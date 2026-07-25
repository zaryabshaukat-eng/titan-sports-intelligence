"""Version 1 API composition for TITAN domain capabilities."""

from fastapi import APIRouter

from app.modules.ingestion.api import router as ingestion_router
from app.modules.market_data.api import router as market_data_router
from app.modules.sports.api import router as sports_router
from app.modules.statistics.api import router as statistics_router

router = APIRouter()
router.include_router(sports_router)
router.include_router(ingestion_router)
router.include_router(market_data_router)
router.include_router(statistics_router)

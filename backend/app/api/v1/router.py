"""Version 1 API composition for TITAN domain capabilities."""

from fastapi import APIRouter

from app.modules.ingestion.api import router as ingestion_router
from app.modules.sports.api import router as sports_router

router = APIRouter()
router.include_router(sports_router)
router.include_router(ingestion_router)

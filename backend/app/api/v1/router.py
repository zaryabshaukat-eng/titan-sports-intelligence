"""Version 1 API composition for TITAN domain capabilities."""

from fastapi import APIRouter

from app.modules.sports.api import router as sports_router

router = APIRouter()
router.include_router(sports_router)

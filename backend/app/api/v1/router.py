"""Version 1 API composition for TITAN domain capabilities."""

from fastapi import APIRouter

from app.modules.consensus.api import router as consensus_router
from app.modules.continuous_improvement.api import router as continuous_improvement_router
from app.modules.evaluation.api import router as evaluation_router
from app.modules.evaluation_monitoring.api import router as evaluation_monitoring_router
from app.modules.explainability.api import router as explainability_router
from app.modules.feature_store.api import router as feature_store_router
from app.modules.infrastructure.api import router as infrastructure_router
from app.modules.ingestion.api import router as ingestion_router
from app.modules.market_data.api import router as market_data_router
from app.modules.probability.api import router as probability_router
from app.modules.research.api import router as research_router
from app.modules.risk.api import router as risk_router
from app.modules.sports.api import router as sports_router
from app.modules.statistics.api import router as statistics_router

router = APIRouter()
router.include_router(sports_router)
router.include_router(ingestion_router)
router.include_router(market_data_router)
router.include_router(statistics_router)
router.include_router(feature_store_router)
router.include_router(research_router)
router.include_router(probability_router)
router.include_router(consensus_router)
router.include_router(risk_router)
router.include_router(explainability_router)
router.include_router(evaluation_router)
router.include_router(evaluation_monitoring_router)
router.include_router(continuous_improvement_router)
router.include_router(infrastructure_router)

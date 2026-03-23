from fastapi import APIRouter

from app.api.routes import health
from app.api.routes import affirmation
from app.api.routes import journal
from app.api.routes import activity_suggestion
from app.api.routes import insight_advice

router = APIRouter(prefix="/api")

# Register module routers here
router.include_router(health.router)
router.include_router(affirmation.router)
router.include_router(journal.router)
router.include_router(activity_suggestion.router)
router.include_router(insight_advice.router)

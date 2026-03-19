from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cache.factory import CacheService
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exception_handlers import register_exception_handlers
from app.core.middlewares import request_id_middleware
from app.db.session import init_db, close_db
from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # STARTUP
        await init_db()
        # For now cache is not required.
        # CacheService.initialize()
        yield
    finally:
        # SHUTDOWN
        await close_db()
        # await CacheService.close()


# set up the logger
setup_logging()

app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Middlewares
app.middleware("http")(request_id_middleware)

register_exception_handlers(app)
app.include_router(router)

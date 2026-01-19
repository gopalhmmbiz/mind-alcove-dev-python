from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.middlewares import auth_middleware
from app.db.session import init_db, close_db
from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # STARTUP
        await init_db()
        yield
    finally:
        # SHUTDOWN
        await close_db()


app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(router)

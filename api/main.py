"""FastAPI application for the E-Council API prototype."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.database import create_tables, engine
from api.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup and dispose of the engine on shutdown."""
    create_tables()
    yield
    engine.dispose()


app = FastAPI(
    title="E-Council API",
    description="FastAPI prototype for the E-Council API/SPA architecture.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")

"""FastAPI application for the E-Council API."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.database import create_tables, get_engine
from api.exceptions import register_exception_handlers
from api.routers.account import router as account_router
from api.routers.admin import router as admin_router
from api.routers.auth import router as auth_router
from api.routers.board_resolutions import router as board_resolutions_router
from api.routers.concept_papers import router as concept_papers_router
from api.routers.dashboard import router as dashboard_router
from api.routers.documentation import router as documentation_router
from api.routers.events import router as events_router
from api.routers.financial import router as financial_router
from api.routers.meetings import router as meetings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup and dispose of the engine on shutdown."""
    create_tables()
    yield
    get_engine().dispose()


_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app = FastAPI(
    title="E-Council API",
    description="FastAPI backend for the E-Council API/SPA architecture.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        _frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:4173",
        "http://localhost:4174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(account_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(concept_papers_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(meetings_router, prefix="/api/v1")
app.include_router(board_resolutions_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(financial_router, prefix="/api/v1")
app.include_router(documentation_router, prefix="/api/v1")


@app.get("/", tags=["root"])
def read_root():
    """Root endpoint with basic API metadata."""
    return {
        "name": app.title,
        "version": app.version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["health"])
def read_health():
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok"})


@app.get("/api/v1/", tags=["root"])
def read_api_root():
    """List the top-level API feature groups."""
    return {
        "version": "v1",
        "features": [
            "auth",
            "account",
            "admin",
            "concept-papers",
            "events",
            "meetings",
            "board-resolutions",
            "dashboard",
            "financial",
            "documentation",
        ],
    }

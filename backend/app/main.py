from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config import settings
from app.database import ensure_data_directory, init_db
from app.fixtures.router import fixture_router
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure local data directory is created on startup
    ensure_data_directory()
    # Create all database tables deterministically
    init_db()
    # Run deterministic idempotent seed
    seed_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Duolingo clone backend API",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount real health check on both /health and /api/health
app.include_router(health_router, prefix="")
app.include_router(health_router, prefix="/api")

# Mount Phase-0 fixture routes (provides locked API endpoints for openapi & frontend)
app.include_router(fixture_router)

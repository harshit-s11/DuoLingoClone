from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attempts import router as attempts_router
from app.api.courses import router as courses_router
from app.api.debug import router as debug_router
from app.api.gamification import router as gamification_router
from app.api.health import router as health_router
from app.api.lessons import router as lessons_router
from app.api.users import router as users_router
from app.config import settings
from app.database import ensure_data_directory, init_db
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

# Mount real Phase-1B production routers
app.include_router(users_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
app.include_router(attempts_router, prefix="/api")
app.include_router(gamification_router, prefix="/api")
app.include_router(debug_router, prefix="/api")

"""Phase-0 stub / fixture router.

Provides representative responses matching docs/API.md so frontend development
and OpenAPI type generation can begin in parallel with the backend.
Isomorphic with future Phase 1 real routers.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status

from app.config import settings
from app.fixtures.fixture_data import (
    MOCK_ACHIEVEMENTS,
    MOCK_COURSE_PATH,
    MOCK_COURSES,
    MOCK_EXERCISES,
    MOCK_LEADERBOARD,
    MOCK_USER,
)
from app.schemas.attempt import (
    AbandonAttemptResponse,
    CheckAnswerRequest,
    CheckAnswerResponse,
    CompleteAttemptResponse,
    StartAttemptResponse,
)
from app.schemas.course import CourseItem, CoursePathResponse
from app.schemas.debug import AdvanceDayRequest, AdvanceDayResponse, SimpleMessageResponse
from app.schemas.gamification import (
    AchievementItem,
    LeaderboardResponse,
    RefillHeartsRequest,
    RefillHeartsResponse,
)
from app.schemas.lesson import LessonMetadataResponse
from app.schemas.user import (
    ProfileResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    UserResponse,
)

fixture_router = APIRouter(prefix="/api", tags=["Phase-0 Fixtures"])


def check_debug_access(x_user_id: int):
    """Enforce that debug endpoints are gated by ENABLE_DEBUG=true and scoped to user 1."""
    if not settings.enable_debug or x_user_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints are disabled or unauthorized for this user",
        )


@fixture_router.get("/me", response_model=UserResponse)
def get_current_user(x_user_id: int = Header(default=1)) -> UserResponse:
    """Retrieve current authenticated user stats."""
    return UserResponse(**MOCK_USER)


@fixture_router.get("/profile", response_model=ProfileResponse)
def get_user_profile(x_user_id: int = Header(default=1)) -> ProfileResponse:
    """Retrieve full user profile with stats and recent activity."""
    return ProfileResponse(
        user={
            "id": 1,
            "username": MOCK_USER["username"],
            "created_at": "2026-10-01T08:00:00Z",
            "xp_total": MOCK_USER["xp_total"],
            "streak_current": MOCK_USER["streak_current"],
            "total_crowns": 4,
        },
        recent_activity=[
            {
                "activity_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "xp_earned": 30,
                "lessons_completed": 2,
            }
        ],
        unlocked_achievements_count=len([a for a in MOCK_ACHIEVEMENTS if a["is_unlocked"]]),
    )


@fixture_router.get("/settings", response_model=SettingsResponse)
def get_settings(x_user_id: int = Header(default=1)) -> SettingsResponse:
    """Retrieve user preferences."""
    return SettingsResponse(
        timezone=MOCK_USER["timezone"],
        date_offset_days=MOCK_USER["date_offset_days"],
    )


@fixture_router.patch("/settings", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdateRequest,
    x_user_id: int = Header(default=1),
) -> SettingsResponse:
    """Update user preferences."""
    tz = payload.timezone or MOCK_USER["timezone"]
    return SettingsResponse(
        timezone=tz,
        date_offset_days=MOCK_USER["date_offset_days"],
    )


@fixture_router.get("/courses", response_model=list[CourseItem])
def list_courses() -> list[CourseItem]:
    """List available courses."""
    return [CourseItem(**c) for c in MOCK_COURSES]


@fixture_router.get("/courses/{course_id}/path", response_model=CoursePathResponse)
def get_course_path(course_id: int) -> CoursePathResponse:
    """Get hierarchical learning path (units -> skills -> lessons)."""
    return CoursePathResponse(**MOCK_COURSE_PATH)


@fixture_router.get("/lessons/{lesson_id}", response_model=LessonMetadataResponse)
def get_lesson_metadata(lesson_id: int) -> LessonMetadataResponse:
    """Get lesson exercises (payloads only, answer keys strictly omitted)."""
    return LessonMetadataResponse(
        id=lesson_id,
        skill_id=1,
        title=f"Lesson {lesson_id}",
        exercises=MOCK_EXERCISES,
    )


@fixture_router.post(
    "/lessons/{lesson_id}/start",
    response_model=StartAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_lesson_attempt(
    lesson_id: int,
    x_user_id: int = Header(default=1),
) -> StartAttemptResponse:
    """Authoritatively start a server-side lesson attempt."""
    return StartAttemptResponse(
        attempt_id=10,
        lesson_id=lesson_id,
        status="in_progress",
        hearts_remaining=MOCK_USER["hearts"],
        exercises=MOCK_EXERCISES,
    )


@fixture_router.post("/attempts/{attempt_id}/check", response_model=CheckAnswerResponse)
def check_attempt_answer(
    attempt_id: int,
    submission: CheckAnswerRequest,
    x_user_id: int = Header(default=1),
) -> CheckAnswerResponse:
    """Validate submitted answer and enforce heart rules."""
    return CheckAnswerResponse(
        is_correct=True,
        correct_answer="El niño",
        hearts_remaining=5,
        attempt_status="in_progress",
    )


@fixture_router.post("/attempts/{attempt_id}/complete", response_model=CompleteAttemptResponse)
def complete_attempt(
    attempt_id: int,
    x_user_id: int = Header(default=1),
) -> CompleteAttemptResponse:
    """Authoritatively complete an attempt, awarding XP and crowns."""
    return CompleteAttemptResponse(
        attempt_id=attempt_id,
        status="completed",
        xp_earned=15,
        accuracy=1.0,
        hearts_lost=0,
        is_replay=False,
        new_crown_earned=True,
        streak_current=4,
    )


@fixture_router.post("/attempts/{attempt_id}/abandon", response_model=AbandonAttemptResponse)
def abandon_attempt(
    attempt_id: int,
    x_user_id: int = Header(default=1),
) -> AbandonAttemptResponse:
    """Abandon an active attempt."""
    return AbandonAttemptResponse(
        attempt_id=attempt_id,
        status="abandoned",
    )


@fixture_router.post("/hearts/refill", response_model=RefillHeartsResponse)
def refill_hearts(
    request: RefillHeartsRequest,
    x_user_id: int = Header(default=1),
) -> RefillHeartsResponse:
    """Refill hearts via gems (350) or practice."""
    if request.method == "gems" and MOCK_USER["gems"] < 350:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="INSUFFICIENT_GEMS",
        )
    return RefillHeartsResponse(
        hearts=5,
        gems=MOCK_USER["gems"] - (350 if request.method == "gems" else 0),
        hearts_updated_at=datetime.now(timezone.utc).isoformat(),
    )


@fixture_router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(x_user_id: int = Header(default=1)) -> LeaderboardResponse:
    """Get current week's leaderboard standings."""
    return LeaderboardResponse(**MOCK_LEADERBOARD)


@fixture_router.get("/achievements", response_model=list[AchievementItem])
def list_achievements(x_user_id: int = Header(default=1)) -> list[AchievementItem]:
    """List achievements and progress."""
    return [AchievementItem(**a) for a in MOCK_ACHIEVEMENTS]


@fixture_router.post("/debug/advance-day", response_model=AdvanceDayResponse)
def debug_advance_day(
    payload: AdvanceDayRequest,
    x_user_id: int = Header(default=1),
) -> AdvanceDayResponse:
    """Simulate advancing logical clock."""
    check_debug_access(x_user_id)
    return AdvanceDayResponse(
        date_offset_days=payload.days,
        logical_now=datetime.now(timezone.utc).isoformat(),
    )


@fixture_router.post("/debug/unlock-all", response_model=SimpleMessageResponse)
def debug_unlock_all(x_user_id: int = Header(default=1)) -> SimpleMessageResponse:
    """Debug helper: unlock all lessons for user 1."""
    check_debug_access(x_user_id)
    return SimpleMessageResponse(message="All lessons unlocked for user 1")


@fixture_router.post("/debug/reset-demo", response_model=SimpleMessageResponse)
def debug_reset_demo(x_user_id: int = Header(default=1)) -> SimpleMessageResponse:
    """Debug helper: reset user 1 progress and stats."""
    check_debug_access(x_user_id)
    return SimpleMessageResponse(message="Demo data reset successfully")

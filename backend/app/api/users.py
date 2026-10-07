"""User endpoints: /api/me, /api/profile, /api/settings."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_dep
from app.database import get_db
from app.models.gamification import DailyActivity, UserAchievement
from app.models.user import User
from app.schemas.user import (
    ActivityItem,
    ProfileResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    UserProfileStats,
    UserResponse,
)
from app.services.clock import get_user_logical_date, get_user_logical_now
from app.services.hearts import ensure_utc, get_next_heart_in_seconds
from app.services.progress_service import get_user_total_crowns

router = APIRouter(tags=["User"])


@router.get("/me", response_model=UserResponse)
def get_me(
    user: User = Depends(get_current_user_dep), db: Session = Depends(get_db)
) -> UserResponse:
    """Retrieve current authenticated user state, hearts, streak, and daily progress."""
    logical_date = get_user_logical_date(user)
    daily_act = (
        db.query(DailyActivity)
        .filter(DailyActivity.user_id == user.id, DailyActivity.activity_date == logical_date)
        .first()
    )

    streak_active_today = daily_act is not None and daily_act.lessons_completed > 0
    daily_xp_progress = daily_act.xp_earned if daily_act else 0
    next_heart_secs = get_next_heart_in_seconds(user)

    next_heart_at: Optional[str] = None
    if next_heart_secs is not None:
        next_dt = get_user_logical_now(user) + timedelta(seconds=next_heart_secs)
        next_heart_at = next_dt.isoformat()

    updated_at_utc = ensure_utc(user.hearts_updated_at).isoformat()

    return UserResponse(
        id=user.id,
        username=user.username,
        hearts=user.hearts,
        max_hearts=5,
        hearts_updated_at=updated_at_utc,
        next_heart_in_seconds=next_heart_secs,
        next_heart_at=next_heart_at,
        xp_total=user.xp_total,
        gems=user.gems,
        streak_current=user.streak_current,
        streak_active_today=streak_active_today,
        daily_xp_goal=user.daily_xp_goal,
        daily_xp_progress=daily_xp_progress,
        date_offset_days=user.date_offset_days,
        timezone=user.timezone,
    )


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    user: User = Depends(get_current_user_dep), db: Session = Depends(get_db)
) -> ProfileResponse:
    """Retrieve full user profile with stats and recent activity."""
    total_crowns = get_user_total_crowns(user.id, db)
    recent_acts = (
        db.query(DailyActivity)
        .filter(DailyActivity.user_id == user.id)
        .order_by(DailyActivity.activity_date.desc())
        .limit(7)
        .all()
    )

    activity_items = [
        ActivityItem(
            activity_date=a.activity_date.isoformat(),
            xp_earned=a.xp_earned,
            lessons_completed=a.lessons_completed,
        )
        for a in recent_acts
    ]

    unlocked_count = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id, UserAchievement.is_unlocked.is_(True))
        .count()
    )

    created_at_utc = ensure_utc(user.created_at).isoformat()

    return ProfileResponse(
        user=UserProfileStats(
            id=user.id,
            username=user.username,
            created_at=created_at_utc,
            xp_total=user.xp_total,
            streak_current=user.streak_current,
            total_crowns=total_crowns,
        ),
        recent_activity=activity_items,
        unlocked_achievements_count=unlocked_count,
    )


@router.get("/settings", response_model=SettingsResponse)
def get_settings(user: User = Depends(get_current_user_dep)) -> SettingsResponse:
    """Retrieve user preferences."""
    return SettingsResponse(
        timezone=user.timezone,
        date_offset_days=user.date_offset_days,
    )


@router.patch("/settings", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdateRequest,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> SettingsResponse:
    """Update user preferences."""
    if payload.timezone is not None:
        user.timezone = payload.timezone
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

    return SettingsResponse(
        timezone=user.timezone,
        date_offset_days=user.date_offset_days,
    )

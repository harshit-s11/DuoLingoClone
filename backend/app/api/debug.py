"""Debug endpoints: /api/debug/advance-day, unlock-all, reset-demo."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_dep
from app.config import settings
from app.database import get_db
from app.models.gamification import DailyActivity, UserAchievement, WeeklyXP
from app.models.progress import AttemptAnswer, LessonAttempt, UserLessonProgress
from app.models.user import User
from app.schemas.debug import AdvanceDayRequest, AdvanceDayResponse, SimpleMessageResponse
from app.seed import seed_database
from app.services.clock import get_user_logical_now
from app.services.hearts import calculate_heart_regen
from app.services.progress_service import clear_debug_unlock_all, set_debug_unlock_all

router = APIRouter(tags=["Debug"])


def check_debug_access(user: User):
    """Enforce that debug endpoints are gated by ENABLE_DEBUG=true and scoped to user 1."""
    if not settings.enable_debug or user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints are disabled or unauthorized for this user",
        )


@router.post("/debug/advance-day", response_model=AdvanceDayResponse)
def advance_day(
    payload: AdvanceDayRequest,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> AdvanceDayResponse:
    """Advance the user's logical clock by N days to simulate time progression."""
    check_debug_access(user)
    user.date_offset_days += payload.days
    db.commit()
    db.refresh(user)

    # Re-evaluate heart regeneration with the new logical time
    user = calculate_heart_regen(user, db)

    return AdvanceDayResponse(
        date_offset_days=user.date_offset_days,
        logical_now=get_user_logical_now(user).isoformat(),
    )


@router.post("/debug/unlock-all", response_model=SimpleMessageResponse)
def unlock_all(
    user: User = Depends(get_current_user_dep),
) -> SimpleMessageResponse:
    """Debug helper: unlock all lessons and skills for user 1."""
    check_debug_access(user)
    set_debug_unlock_all(user.id)
    return SimpleMessageResponse(message="All lessons unlocked for user 1")


@router.post("/debug/reset-demo", response_model=SimpleMessageResponse)
def reset_demo(
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> SimpleMessageResponse:
    """Debug helper: reset user 1 progress, hearts, gems, streak, and restore seed baseline."""
    check_debug_access(user)
    clear_debug_unlock_all(user.id)

    # Delete runtime progress for user 1
    db.query(AttemptAnswer).filter(
        AttemptAnswer.attempt_id.in_(
            db.query(LessonAttempt.id).filter(LessonAttempt.user_id == user.id)
        )
    ).delete(synchronize_session=False)

    db.query(LessonAttempt).filter(LessonAttempt.user_id == user.id).delete()
    db.query(UserLessonProgress).filter(UserLessonProgress.user_id == user.id).delete()
    db.query(DailyActivity).filter(DailyActivity.user_id == user.id).delete()
    db.query(WeeklyXP).filter(WeeklyXP.user_id == user.id).delete()
    db.query(UserAchievement).filter(UserAchievement.user_id == user.id).delete()

    now_utc = datetime.now(timezone.utc)
    user.hearts = 5
    user.hearts_updated_at = now_utc
    user.xp_total = 0
    user.gems = 500
    user.streak_current = 0
    user.date_offset_days = 0
    db.commit()

    # Restore deterministic seed baseline
    seed_database(db)

    return SimpleMessageResponse(message="Demo data reset successfully")

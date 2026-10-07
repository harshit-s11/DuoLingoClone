"""Gamification endpoints: /api/hearts/refill, /api/leaderboard, /api/achievements."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_dep
from app.database import get_db
from app.models.gamification import Achievement, UserAchievement
from app.models.user import User
from app.schemas.gamification import (
    AchievementItem,
    LeaderboardResponse,
    RefillHeartsRequest,
    RefillHeartsResponse,
)
from app.services.hearts import ensure_utc, refill_user_hearts
from app.services.leaderboard_service import get_weekly_leaderboard_data

router = APIRouter(tags=["Gamification"])


@router.post("/hearts/refill", response_model=RefillHeartsResponse)
def refill_hearts(
    payload: RefillHeartsRequest,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> RefillHeartsResponse:
    """Refill hearts back to 5 via gems (350) or practice (free)."""
    try:
        user = refill_user_hearts(user=user, method=payload.method, db=db)
    except ValueError as e:
        if str(e) == "INSUFFICIENT_GEMS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="INSUFFICIENT_GEMS",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return RefillHeartsResponse(
        hearts=user.hearts,
        gems=user.gems,
        hearts_updated_at=ensure_utc(user.hearts_updated_at).isoformat(),
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    """Get current week's leaderboard standings."""
    data = get_weekly_leaderboard_data(user=user, db=db)
    return LeaderboardResponse(**data)


@router.get("/achievements", response_model=list[AchievementItem])
def list_achievements(
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> list[AchievementItem]:
    """List achievements and user unlocking milestones."""
    achievements = db.query(Achievement).order_by(Achievement.id.asc()).all()
    user_achs = {
        ua.achievement_id: ua
        for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    }

    results = []
    for ach in achievements:
        ua = user_achs.get(ach.id)
        current_val = ua.current_value if ua else 0
        is_unl = ua.is_unlocked if ua else False
        unl_at = ensure_utc(ua.unlocked_at).isoformat() if (ua and ua.unlocked_at) else None

        results.append(
            AchievementItem(
                id=ach.id,
                code=ach.code,
                title=ach.title,
                description=ach.description,
                badge_icon=ach.badge_icon,
                target_value=ach.threshold,
                current_value=current_val,
                is_unlocked=is_unl,
                unlocked_at=unl_at,
            )
        )

    return results

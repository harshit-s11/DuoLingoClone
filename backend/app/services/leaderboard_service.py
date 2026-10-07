"""Weekly Leaderboard service with bot synchronization."""

from sqlalchemy.orm import Session

from app.models.gamification import WeeklyXP
from app.models.user import User
from app.seed.curriculum_data import BOT_USERS_DATA
from app.services.clock import get_user_logical_date, get_user_logical_now, get_week_start_date


def ensure_weekly_leaderboard(user: User, db: Session) -> str:
    """Ensure WeeklyXP entries exist for all bots and the current user
    for the user's current logical week.
    """
    logical_date = get_user_logical_date(user)
    week_start = get_week_start_date(logical_date)
    now_utc = get_user_logical_now(user)

    # Ensure bots have entries for this week
    for b_def in BOT_USERS_DATA:
        bot = db.query(User).filter(User.username == b_def["username"]).first()
        if bot:
            b_wxp = (
                db.query(WeeklyXP)
                .filter(WeeklyXP.user_id == bot.id, WeeklyXP.week_start_date == week_start)
                .first()
            )
            if not b_wxp:
                b_wxp = WeeklyXP(
                    user_id=bot.id,
                    week_start_date=week_start,
                    xp_earned=b_def["xp_weekly"],
                    updated_at=now_utc,
                )
                db.add(b_wxp)

    # Ensure current user has an entry for this week
    user_wxp = (
        db.query(WeeklyXP)
        .filter(WeeklyXP.user_id == user.id, WeeklyXP.week_start_date == week_start)
        .first()
    )
    if not user_wxp:
        user_wxp = WeeklyXP(
            user_id=user.id,
            week_start_date=week_start,
            xp_earned=0,
            updated_at=now_utc,
        )
        db.add(user_wxp)

    db.commit()
    return week_start.isoformat()


def get_weekly_leaderboard_data(user: User, db: Session) -> dict:
    """Retrieve ranked leaderboard standings for the user's active week."""
    week_start_str = ensure_weekly_leaderboard(user, db)
    logical_date = get_user_logical_date(user)
    week_start = get_week_start_date(logical_date)

    entries = (
        db.query(WeeklyXP, User)
        .join(User, WeeklyXP.user_id == User.id)
        .filter(WeeklyXP.week_start_date == week_start)
        .order_by(WeeklyXP.xp_earned.desc(), User.id.asc())
        .all()
    )

    rankings = []
    for rank, (wxp, u) in enumerate(entries, start=1):
        rankings.append(
            {
                "rank": rank,
                "username": u.username,
                "xp_earned": wxp.xp_earned,
                "is_current_user": u.id == user.id,
            }
        )

    return {
        "week_start_date": week_start_str,
        "rankings": rankings,
    }

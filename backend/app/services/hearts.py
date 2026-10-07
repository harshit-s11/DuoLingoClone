"""Heart system service: lazy regeneration, heart deduction, and refills."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.clock import get_user_logical_now

HEART_REGEN_INTERVAL_SECONDS = 18000  # 5 hours
MAX_HEARTS = 5


def ensure_utc(dt: Optional[datetime]) -> datetime:
    """Ensure datetime has UTC timezone."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calculate_heart_regen(user: User, db: Session) -> User:
    """Lazily compute and apply heart regeneration based on elapsed logical time.

    Regeneration rate: +1 heart every 5 hours (18,000s) up to MAX_HEARTS (5).
    """
    if user.hearts >= MAX_HEARTS:
        return user

    logical_now = get_user_logical_now(user)
    updated_at = ensure_utc(user.hearts_updated_at)
    elapsed_seconds = (logical_now - updated_at).total_seconds()

    if elapsed_seconds <= 0:
        return user

    intervals = int(elapsed_seconds // HEART_REGEN_INTERVAL_SECONDS)
    if intervals > 0:
        gain = min(intervals, MAX_HEARTS - user.hearts)
        user.hearts += gain
        user.hearts_updated_at = updated_at + timedelta(seconds=gain * HEART_REGEN_INTERVAL_SECONDS)
        if user.hearts >= MAX_HEARTS:
            user.hearts = MAX_HEARTS
            user.hearts_updated_at = logical_now
        db.commit()
        db.refresh(user)

    return user


def get_next_heart_in_seconds(user: User) -> Optional[int]:
    """Calculate remaining seconds until the next heart regenerates."""
    if user.hearts >= MAX_HEARTS:
        return None

    logical_now = get_user_logical_now(user)
    updated_at = ensure_utc(user.hearts_updated_at)
    elapsed_seconds = (logical_now - updated_at).total_seconds()

    if elapsed_seconds < 0:
        return HEART_REGEN_INTERVAL_SECONDS

    remaining = HEART_REGEN_INTERVAL_SECONDS - (elapsed_seconds % HEART_REGEN_INTERVAL_SECONDS)
    return max(0, int(remaining))


def deduct_heart(user: User, db: Session) -> tuple[int, bool]:
    """Deduct 1 heart from user following critical invariant.

    Critical Invariant:
    If user currently has 5 hearts, hearts_updated_at MUST be set to logical_now
    BEFORE decrementing to 4. This guarantees the 5-hour regeneration timer
    for heart #5 starts precisely at the moment of failure.

    Returns: (hearts_remaining, is_exhausted)
    """
    logical_now = get_user_logical_now(user)

    if user.hearts == MAX_HEARTS:
        user.hearts_updated_at = logical_now

    user.hearts = max(0, user.hearts - 1)
    db.commit()
    db.refresh(user)

    is_exhausted = user.hearts == 0
    return user.hearts, is_exhausted


def refill_user_hearts(user: User, method: str, db: Session) -> User:
    """Refill hearts back to MAX_HEARTS via gems (costs 350) or practice (free)."""
    if method == "gems":
        if user.gems < 350:
            raise ValueError("INSUFFICIENT_GEMS")
        user.gems -= 350

    logical_now = get_user_logical_now(user)
    user.hearts = MAX_HEARTS
    user.hearts_updated_at = logical_now
    db.commit()
    db.refresh(user)
    return user

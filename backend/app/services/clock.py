"""Logical Clock service for user-relative temporal calculations."""

import zoneinfo
from datetime import date, datetime, timedelta, timezone
from typing import Any


def get_logical_now(date_offset_days: int = 0) -> datetime:
    """Return the logical current timestamp in UTC, adjusted by date_offset_days."""
    return datetime.now(timezone.utc) + timedelta(days=date_offset_days)


def get_user_logical_now(user: Any) -> datetime:
    """Return the logical current timestamp in UTC for a specific user."""
    offset = getattr(user, "date_offset_days", 0) if user else 0
    return get_logical_now(offset)


def get_logical_date(date_offset_days: int = 0, timezone_str: str = "UTC") -> date:
    """Return the logical calendar date in the user's localized timezone."""
    now_utc = get_logical_now(date_offset_days)
    try:
        tz = zoneinfo.ZoneInfo(timezone_str)
        return now_utc.astimezone(tz).date()
    except Exception:
        # Fallback to UTC if timezone string is invalid
        return now_utc.date()


def get_user_logical_date(user: Any) -> date:
    """Return the logical calendar date for a user."""
    offset = getattr(user, "date_offset_days", 0) if user else 0
    tz_str = getattr(user, "timezone", "UTC") if user else "UTC"
    return get_logical_date(date_offset_days=offset, timezone_str=tz_str)


def get_week_start_date(target_date: date) -> date:
    """Return the Monday (week start) for a given calendar date."""
    return target_date - timedelta(days=target_date.weekday())

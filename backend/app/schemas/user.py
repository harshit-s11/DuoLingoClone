from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    hearts: int
    max_hearts: int = 5
    hearts_updated_at: str
    next_heart_in_seconds: Optional[int] = None
    xp_total: int
    gems: int
    streak_current: int
    date_offset_days: int
    timezone: str

    model_config = ConfigDict(extra="forbid")


class ActivityItem(BaseModel):
    activity_date: str
    xp_earned: int
    lessons_completed: int

    model_config = ConfigDict(extra="forbid")


class UserProfileStats(BaseModel):
    id: int
    username: str
    created_at: str
    xp_total: int
    streak_current: int
    total_crowns: int

    model_config = ConfigDict(extra="forbid")


class ProfileResponse(BaseModel):
    user: UserProfileStats
    recent_activity: list[ActivityItem]
    unlocked_achievements_count: int

    model_config = ConfigDict(extra="forbid")


class SettingsResponse(BaseModel):
    timezone: str
    date_offset_days: int

    model_config = ConfigDict(extra="forbid")


class SettingsUpdateRequest(BaseModel):
    timezone: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

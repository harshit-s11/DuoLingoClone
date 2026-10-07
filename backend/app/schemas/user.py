from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: int
    username: str
    hearts: int
    max_hearts: int = 5
    hearts_updated_at: str
    next_heart_in_seconds: Optional[int] = None
    next_heart_at: Optional[str] = None
    xp_total: int
    gems: int
    streak_current: int
    streak_active_today: Optional[bool] = False
    daily_xp_goal: Optional[int] = 20
    daily_xp_progress: Optional[int] = 0
    date_offset_days: int
    timezone: str

    model_config = ConfigDict(extra="ignore")


class ActivityItem(BaseModel):
    activity_date: str
    xp_earned: int
    lessons_completed: int

    model_config = ConfigDict(extra="ignore")


class UserProfileStats(BaseModel):
    id: int
    username: str
    created_at: str
    xp_total: int
    streak_current: int
    total_crowns: int

    model_config = ConfigDict(extra="ignore")


class ProfileResponse(BaseModel):
    user: UserProfileStats
    recent_activity: list[ActivityItem]
    unlocked_achievements_count: int

    model_config = ConfigDict(extra="ignore")


class SettingsResponse(BaseModel):
    timezone: str
    date_offset_days: int

    model_config = ConfigDict(extra="ignore")


class SettingsUpdateRequest(BaseModel):
    timezone: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

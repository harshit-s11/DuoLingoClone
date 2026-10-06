from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class RefillHeartsRequest(BaseModel):
    method: Literal["gems", "practice"]

    model_config = ConfigDict(extra="forbid")


class RefillHeartsResponse(BaseModel):
    hearts: int
    gems: int
    hearts_updated_at: str

    model_config = ConfigDict(extra="forbid")


class LeaderboardRanking(BaseModel):
    rank: int
    username: str
    xp_earned: int
    is_current_user: bool

    model_config = ConfigDict(extra="forbid")


class LeaderboardResponse(BaseModel):
    week_start_date: str
    rankings: list[LeaderboardRanking]

    model_config = ConfigDict(extra="forbid")


class AchievementItem(BaseModel):
    id: int
    code: str
    title: str
    description: str
    badge_icon: str
    target_value: int
    current_value: int
    is_unlocked: bool
    unlocked_at: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

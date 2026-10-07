from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.lesson import ExerciseClientView


class StartAttemptResponse(BaseModel):
    attempt_id: int
    lesson_id: int
    status: str
    hearts_remaining: int
    exercises: list[ExerciseClientView]

    model_config = ConfigDict(extra="ignore")


class CheckAnswerRequest(BaseModel):
    exercise_id: int
    user_answer: Optional[Any] = None
    answer: Optional[Any] = None

    def get_submitted_answer(self) -> Any:
        return self.answer if self.answer is not None else self.user_answer

    model_config = ConfigDict(extra="ignore")


class CheckAnswerResponse(BaseModel):
    is_correct: bool
    correct: Optional[bool] = None
    correct_answer: Any
    hearts_remaining: int
    hearts: Optional[int] = None
    attempt_status: str
    lesson_failed: Optional[bool] = False
    explanation: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class CompleteAttemptResponse(BaseModel):
    attempt_id: int
    status: str
    xp_earned: int
    accuracy: float
    hearts_lost: int
    is_replay: bool
    new_crown_earned: bool
    streak_current: int
    time_spent_seconds: Optional[int] = None
    crowns_after: Optional[int] = None
    skill_completed: Optional[bool] = None
    unit_completed: Optional[bool] = None
    new_achievements: Optional[list[str]] = None
    streak_extended: Optional[bool] = None

    model_config = ConfigDict(extra="ignore")


class AbandonAttemptResponse(BaseModel):
    attempt_id: int
    status: str

    model_config = ConfigDict(extra="ignore")

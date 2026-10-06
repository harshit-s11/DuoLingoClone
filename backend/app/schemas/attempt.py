from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.lesson import ExerciseClientView


class StartAttemptResponse(BaseModel):
    attempt_id: int
    lesson_id: int
    status: str
    hearts_remaining: int
    exercises: list[ExerciseClientView]

    model_config = ConfigDict(extra="forbid")


class CheckAnswerRequest(BaseModel):
    exercise_id: int
    user_answer: Any

    model_config = ConfigDict(extra="forbid")


class CheckAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: Any
    hearts_remaining: int
    attempt_status: str

    model_config = ConfigDict(extra="forbid")


class CompleteAttemptResponse(BaseModel):
    attempt_id: int
    status: str
    xp_earned: int
    accuracy: float
    hearts_lost: int
    is_replay: bool
    new_crown_earned: bool
    streak_current: int

    model_config = ConfigDict(extra="forbid")


class AbandonAttemptResponse(BaseModel):
    attempt_id: int
    status: str

    model_config = ConfigDict(extra="forbid")

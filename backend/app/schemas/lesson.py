from typing import Any

from pydantic import BaseModel, ConfigDict


class ExerciseClientView(BaseModel):
    id: int
    exercise_order: int
    type: str  # multiple_choice, translate, match_pairs, fill_blank, type_answer
    payload: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class LessonMetadataResponse(BaseModel):
    id: int
    skill_id: int
    title: str
    exercises: list[ExerciseClientView]

    model_config = ConfigDict(extra="forbid")

"""Lesson endpoints: /api/lessons/{id}, /api/lessons/{id}/start."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_dep
from app.database import get_db
from app.models.course import Exercise, Lesson
from app.models.user import User
from app.schemas.attempt import StartAttemptResponse
from app.schemas.lesson import ExerciseClientView, LessonMetadataResponse
from app.services.progress_service import start_lesson_attempt

router = APIRouter(tags=["Lessons"])


@router.get("/lessons/{lesson_id}", response_model=LessonMetadataResponse)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)) -> LessonMetadataResponse:
    """Retrieve lesson metadata and public exercises. answer_json is NEVER included."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson {lesson_id} not found",
        )

    exercises = (
        db.query(Exercise)
        .filter(Exercise.lesson_id == lesson.id)
        .order_by(Exercise.exercise_order.asc())
        .all()
    )

    exercise_views = [
        ExerciseClientView(
            id=ex.id,
            exercise_order=ex.exercise_order,
            type=ex.type,
            payload=json.loads(ex.payload_json),
        )
        for ex in exercises
    ]

    return LessonMetadataResponse(
        id=lesson.id,
        skill_id=lesson.skill_id,
        title=lesson.title,
        exercises=exercise_views,
    )


@router.post(
    "/lessons/{lesson_id}/start",
    response_model=StartAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_lesson(
    lesson_id: int,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> StartAttemptResponse:
    """Authoritatively initiate a lesson attempt.

    Rules:
    - 409 OUT_OF_HEARTS if user has 0 hearts.
    - 403 LESSON_LOCKED if lesson is locked.
    - Abandons existing in_progress attempt if one exists.
    - Exercises delivered in deterministic exercise_order without answers.
    """
    try:
        attempt_data = start_lesson_attempt(user=user, lesson_id=lesson_id, db=db)
    except ValueError as e:
        if str(e) == "OUT_OF_HEARTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="OUT_OF_HEARTS",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        if str(e) == "LESSON_LOCKED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="LESSON_LOCKED",
            )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return StartAttemptResponse(**attempt_data)

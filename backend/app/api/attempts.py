"""Attempt engine endpoints: /api/attempts/{id}/check, complete, abandon."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_dep
from app.database import get_db
from app.models.progress import LessonAttempt
from app.models.user import User
from app.schemas.attempt import (
    AbandonAttemptResponse,
    CheckAnswerRequest,
    CheckAnswerResponse,
    CompleteAttemptResponse,
)
from app.services.progress_service import check_attempt_answer, complete_lesson_attempt

router = APIRouter(tags=["Attempts"])


@router.post("/attempts/{attempt_id}/check", response_model=CheckAnswerResponse)
def check_answer(
    attempt_id: int,
    payload: CheckAnswerRequest,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> CheckAnswerResponse:
    """Authoritatively check a submitted exercise answer against server answer keys."""
    try:
        submitted = payload.get_submitted_answer()
        result = check_attempt_answer(
            user=user,
            attempt_id=attempt_id,
            exercise_id=payload.exercise_id,
            user_answer=submitted,
            db=db,
        )
        return CheckAnswerResponse(**result)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/attempts/{attempt_id}/complete", response_model=CompleteAttemptResponse)
def complete_attempt(
    attempt_id: int,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> CompleteAttemptResponse:
    """Authoritatively complete an attempt, deriving accuracy and awarding XP."""
    try:
        completion_data = complete_lesson_attempt(
            user=user,
            attempt_id=attempt_id,
            db=db,
        )
        return CompleteAttemptResponse(**completion_data)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        err_msg = str(e)
        if "INVALID_COMPLETION" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_COMPLETION",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


@router.post("/attempts/{attempt_id}/abandon", response_model=AbandonAttemptResponse)
def abandon_attempt(
    attempt_id: int,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> AbandonAttemptResponse:
    """Abandon an active lesson attempt."""
    attempt = db.query(LessonAttempt).filter(LessonAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attempt {attempt_id} not found",
        )
    if attempt.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized attempt access",
        )

    attempt.status = "abandoned"
    db.commit()
    return AbandonAttemptResponse(attempt_id=attempt.id, status=attempt.status)

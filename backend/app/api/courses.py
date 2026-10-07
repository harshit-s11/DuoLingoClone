"""Course and learning path endpoints: /api/courses, /api/courses/{course_id}/path."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_dep
from app.database import get_db
from app.models.course import Course, Unit
from app.models.progress import UserLessonProgress
from app.models.user import User
from app.schemas.course import (
    CourseItem,
    CoursePathResponse,
    LessonSummary,
    SkillSummary,
    UnitSummary,
)
from app.services.progress_service import get_skill_crowns, is_lesson_unlocked

router = APIRouter(tags=["Courses"])


@router.get("/courses", response_model=list[CourseItem])
def list_courses(db: Session = Depends(get_db)) -> list[CourseItem]:
    """List all available courses."""
    courses = db.query(Course).all()
    return [
        CourseItem(
            id=c.id,
            code=c.code,
            title=c.title,
            description=c.description,
            flag_emoji=c.flag_emoji,
        )
        for c in courses
    ]


@router.get("/courses/{course_id}/path", response_model=CoursePathResponse)
def get_course_path(
    course_id: int,
    user: User = Depends(get_current_user_dep),
    db: Session = Depends(get_db),
) -> CoursePathResponse:
    """Retrieve full hierarchical learning tree (units -> skills -> lessons)
    with user completion and locking.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found",
        )

    # Prefetch completed lesson IDs for this user
    completed_rows = (
        db.query(UserLessonProgress.lesson_id)
        .filter(UserLessonProgress.user_id == user.id, UserLessonProgress.is_completed.is_(True))
        .all()
    )
    completed_lesson_ids = {row[0] for row in completed_rows}

    units_data = []
    units = db.query(Unit).filter(Unit.course_id == course.id).order_by(Unit.unit_order.asc()).all()

    for unit in units:
        skills_data = []
        for skill in unit.skills:
            lessons_data = []
            for lesson in skill.lessons:
                is_comp = lesson.id in completed_lesson_ids
                is_unlocked = is_lesson_unlocked(user, lesson, db)
                lessons_data.append(
                    LessonSummary(
                        id=lesson.id,
                        lesson_order=lesson.lesson_order,
                        title=lesson.title,
                        is_completed=is_comp,
                        is_locked=not is_unlocked,
                    )
                )

            crowns_earned, total_crowns = get_skill_crowns(user.id, skill, db)
            skills_data.append(
                SkillSummary(
                    id=skill.id,
                    skill_order=skill.skill_order,
                    name=skill.name,
                    description=skill.description,
                    icon_name=skill.icon_name,
                    total_crowns=total_crowns,
                    crowns_earned=crowns_earned,
                    lessons=lessons_data,
                )
            )

        units_data.append(
            UnitSummary(
                id=unit.id,
                unit_order=unit.unit_order,
                title=unit.title,
                description=unit.description,
                skills=skills_data,
            )
        )

    return CoursePathResponse(
        course_id=course.id,
        title=course.title,
        units=units_data,
    )

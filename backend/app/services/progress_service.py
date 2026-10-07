"""Lesson progress, attempt engine, streaks, unlocking, and achievements service."""

import json
from datetime import timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.course import Exercise, Lesson, Skill, Unit
from app.models.gamification import Achievement, DailyActivity, UserAchievement, WeeklyXP
from app.models.progress import AttemptAnswer, LessonAttempt, UserLessonProgress
from app.models.user import User
from app.services.clock import get_user_logical_date, get_user_logical_now, get_week_start_date
from app.services.exercise_evaluator import evaluate_exercise
from app.services.hearts import calculate_heart_regen, deduct_heart

# In-memory debug flag for unlock-all scoped to user 1
_DEBUG_UNLOCKED_USERS = set()


def set_debug_unlock_all(user_id: int) -> None:
    _DEBUG_UNLOCKED_USERS.add(user_id)


def clear_debug_unlock_all(user_id: int) -> None:
    _DEBUG_UNLOCKED_USERS.discard(user_id)


def is_skill_completed(user_id: int, skill: Skill, db: Session) -> bool:
    """Check if all lessons in a skill are completed by the user."""
    lesson_ids = [les.id for les in skill.lessons]
    if not lesson_ids:
        return True
    completed_count = (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id.in_(lesson_ids),
            UserLessonProgress.is_completed.is_(True),
        )
        .count()
    )
    return completed_count >= len(lesson_ids)


def is_unit_completed(user_id: int, unit: Unit, db: Session) -> bool:
    """Check if all skills in a unit are completed by the user."""
    return all(is_skill_completed(user_id, s, db) for s in unit.skills)


def is_skill_unlocked(user: User, skill: Skill, db: Session) -> bool:
    """Check if a skill is unlocked for the user."""
    if user.id in _DEBUG_UNLOCKED_USERS:
        return True

    unit = skill.unit
    # If first skill of first unit, always unlocked
    if unit.unit_order == 1 and skill.skill_order == 1:
        return True

    # If subsequent skill in the same unit, unlocked if previous skill in that unit is completed
    if skill.skill_order > 1:
        prev_skill = (
            db.query(Skill)
            .filter(
                Skill.unit_id == unit.id,
                Skill.skill_order == skill.skill_order - 1,
            )
            .first()
        )
        if prev_skill:
            return is_skill_completed(user.id, prev_skill, db)

    # If first skill of subsequent unit, unlocked if entire previous unit is completed
    if skill.skill_order == 1 and unit.unit_order > 1:
        prev_unit = (
            db.query(Unit)
            .filter(
                Unit.course_id == unit.course_id,
                Unit.unit_order == unit.unit_order - 1,
            )
            .first()
        )
        if prev_unit:
            return is_unit_completed(user.id, prev_unit, db)

    return False


def is_lesson_unlocked(user: User, lesson: Lesson, db: Session) -> bool:
    """Check if a lesson is unlocked for the user."""
    if user.id in _DEBUG_UNLOCKED_USERS:
        return True

    skill = lesson.skill
    if not is_skill_unlocked(user, skill, db):
        return False

    # Within an unlocked skill, lesson 1 is always unlocked
    if lesson.lesson_order == 1:
        return True

    # Lesson k > 1 is unlocked if lesson k-1 is completed
    prev_lesson = (
        db.query(Lesson)
        .filter(
            Lesson.skill_id == skill.id,
            Lesson.lesson_order == lesson.lesson_order - 1,
        )
        .first()
    )
    if not prev_lesson:
        return True

    prev_prog = (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id == prev_lesson.id,
            UserLessonProgress.is_completed.is_(True),
        )
        .first()
    )
    return prev_prog is not None


def get_skill_crowns(user_id: int, skill: Skill, db: Session) -> tuple[int, int]:
    """Calculate (crowns_earned, total_crowns) for a skill."""
    lesson_ids = [les.id for les in skill.lessons]
    total_crowns = len(lesson_ids) or skill.total_crowns
    if not lesson_ids:
        return 0, total_crowns

    completed_count = (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id.in_(lesson_ids),
            UserLessonProgress.is_completed.is_(True),
        )
        .count()
    )
    return min(completed_count, total_crowns), total_crowns


def get_user_total_crowns(user_id: int, db: Session) -> int:
    """Calculate total crowns earned across all completed lessons."""
    return (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.is_completed.is_(True),
        )
        .count()
    )


def start_lesson_attempt(user: User, lesson_id: int, db: Session) -> dict[str, Any]:
    """Start an authoritative server-side lesson attempt."""
    user = calculate_heart_regen(user, db)

    if user.hearts <= 0:
        raise ValueError("OUT_OF_HEARTS")

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise LookupError(f"Lesson {lesson_id} not found")

    if not is_lesson_unlocked(user, lesson, db):
        raise PermissionError("LESSON_LOCKED")

    # If an existing in_progress attempt exists, mark it abandoned to preserve partial unique index
    existing_attempt = (
        db.query(LessonAttempt)
        .filter(
            LessonAttempt.user_id == user.id,
            LessonAttempt.lesson_id == lesson.id,
            LessonAttempt.status == "in_progress",
        )
        .first()
    )
    if existing_attempt:
        existing_attempt.status = "abandoned"
        db.commit()

    # Create new attempt
    attempt = LessonAttempt(
        user_id=user.id,
        lesson_id=lesson.id,
        status="in_progress",
        started_at=get_user_logical_now(user),
        hearts_lost=0,
        xp_earned=0,
        accuracy=0.0,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Return safe exercise views (NEVER answer_json)
    exercises = (
        db.query(Exercise)
        .filter(Exercise.lesson_id == lesson.id)
        .order_by(Exercise.exercise_order.asc())
        .all()
    )
    exercise_views = [
        {
            "id": ex.id,
            "exercise_order": ex.exercise_order,
            "type": ex.type,
            "payload": json.loads(ex.payload_json),
        }
        for ex in exercises
    ]

    return {
        "attempt_id": attempt.id,
        "lesson_id": lesson.id,
        "status": attempt.status,
        "hearts_remaining": user.hearts,
        "exercises": exercise_views,
    }


def check_attempt_answer(
    user: User,
    attempt_id: int,
    exercise_id: int,
    user_answer: Any,
    db: Session,
) -> dict[str, Any]:
    """Check a submitted exercise answer against authoritative server keys."""
    attempt = db.query(LessonAttempt).filter(LessonAttempt.id == attempt_id).first()
    if not attempt:
        raise LookupError(f"Attempt {attempt_id} not found")

    if attempt.user_id != user.id:
        raise PermissionError("UNAUTHORIZED_ATTEMPT")

    if attempt.status != "in_progress":
        raise ValueError(f"Attempt is not in_progress (status: {attempt.status})")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise or exercise.lesson_id != attempt.lesson_id:
        raise LookupError("EXERCISE_NOT_IN_LESSON")

    is_correct, correct_answer_display, explanation = evaluate_exercise(
        exercise_type=exercise.type,
        payload_json_str=exercise.payload_json,
        answer_json_str=exercise.answer_json,
        user_answer=user_answer,
    )

    # Log attempt_answer
    ans_record = AttemptAnswer(
        attempt_id=attempt.id,
        exercise_id=exercise.id,
        user_answer_json=json.dumps(user_answer),
        is_correct=is_correct,
        answered_at=get_user_logical_now(user),
    )
    db.add(ans_record)

    lesson_failed = False
    if not is_correct:
        hearts_rem, exhausted = deduct_heart(user, db)
        attempt.hearts_lost += 1
        if exhausted:
            attempt.status = "failed"
            lesson_failed = True
    else:
        hearts_rem = user.hearts

    db.commit()
    db.refresh(attempt)

    return {
        "is_correct": is_correct,
        "correct": is_correct,
        "correct_answer": correct_answer_display,
        "hearts_remaining": hearts_rem,
        "hearts": hearts_rem,
        "attempt_status": attempt.status,
        "lesson_failed": lesson_failed,
        "explanation": explanation,
    }


def complete_lesson_attempt(user: User, attempt_id: int, db: Session) -> dict[str, Any]:
    """Authoritatively complete an attempt, deriving accuracy, XP, streaks, and achievements."""
    attempt = db.query(LessonAttempt).filter(LessonAttempt.id == attempt_id).first()
    if not attempt:
        raise LookupError(f"Attempt {attempt_id} not found")

    if attempt.user_id != user.id:
        raise PermissionError("UNAUTHORIZED_ATTEMPT")

    # Idempotent response if already completed
    if attempt.status == "completed":
        total_crowns = get_user_total_crowns(user.id, db)
        return {
            "attempt_id": attempt.id,
            "status": "completed",
            "xp_earned": attempt.xp_earned,
            "accuracy": attempt.accuracy,
            "hearts_lost": attempt.hearts_lost,
            "is_replay": False,
            "new_crown_earned": False,
            "streak_current": user.streak_current,
            "time_spent_seconds": 30,
            "crowns_after": total_crowns,
            "skill_completed": False,
            "unit_completed": False,
            "new_achievements": [],
            "streak_extended": False,
        }

    if attempt.status != "in_progress":
        raise ValueError(f"Cannot complete attempt with status {attempt.status}")

    lesson = db.query(Lesson).filter(Lesson.id == attempt.lesson_id).first()
    exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson.id).all()
    all_answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .order_by(AttemptAnswer.answered_at.asc())
        .all()
    )

    # Check that EVERY exercise has at least one correct answer logged
    correct_ex_ids = {a.exercise_id for a in all_answers if a.is_correct}
    expected_ex_ids = {e.id for e in exercises}
    if not expected_ex_ids.issubset(correct_ex_ids):
        raise ValueError("INVALID_COMPLETION")

    # Derive first-try accuracy
    first_answers: dict[int, bool] = {}
    for ans in all_answers:
        if ans.exercise_id not in first_answers:
            first_answers[ans.exercise_id] = ans.is_correct

    first_try_correct_count = sum(1 for ex_id in expected_ex_ids if first_answers.get(ex_id, False))
    total_count = len(expected_ex_ids) or 1
    accuracy = round(first_try_correct_count / total_count, 2)

    # Derive XP
    base_xp = 10
    bonus_xp = 5 if accuracy >= 1.0 else (2 if accuracy >= 0.8 else 0)
    xp_earned = base_xp + bonus_xp

    # Logical time
    completed_at = get_user_logical_now(user)
    started_at = attempt.started_at
    if started_at is not None and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    time_spent_seconds = (
        max(1, int((completed_at - started_at).total_seconds())) if started_at else 30
    )

    # Check replay
    existing_progress = (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    is_replay = existing_progress is not None and existing_progress.is_completed
    new_crown_earned = not is_replay

    # Update attempt
    attempt.status = "completed"
    attempt.completed_at = completed_at
    attempt.xp_earned = xp_earned
    attempt.accuracy = accuracy

    # Update user XP
    user.xp_total += xp_earned

    # Update or create UserLessonProgress
    if not existing_progress:
        existing_progress = UserLessonProgress(
            user_id=user.id,
            lesson_id=lesson.id,
            is_completed=True,
            score=int(accuracy * 100),
            completed_at=completed_at,
        )
        db.add(existing_progress)
    else:
        existing_progress.is_completed = True
        existing_progress.completed_at = completed_at
        existing_progress.score = max(existing_progress.score or 0, int(accuracy * 100))
        existing_progress.updated_at = completed_at

    # Update DailyActivity & Streak
    logical_date = get_user_logical_date(user)
    daily_act = (
        db.query(DailyActivity)
        .filter(
            DailyActivity.user_id == user.id,
            DailyActivity.activity_date == logical_date,
        )
        .first()
    )

    streak_extended = False
    if not daily_act:
        daily_act = DailyActivity(
            user_id=user.id,
            activity_date=logical_date,
            xp_earned=xp_earned,
            lessons_completed=1,
        )
        db.add(daily_act)
        # Check yesterday's activity
        yesterday = logical_date - timedelta(days=1)
        yesterday_act = (
            db.query(DailyActivity)
            .filter(
                DailyActivity.user_id == user.id,
                DailyActivity.activity_date == yesterday,
            )
            .first()
        )
        if yesterday_act and yesterday_act.lessons_completed > 0:
            user.streak_current += 1
        else:
            user.streak_current = 1
        streak_extended = True
    else:
        daily_act.xp_earned += xp_earned
        daily_act.lessons_completed += 1

    # Update WeeklyXP
    week_start = get_week_start_date(logical_date)
    weekly_xp = (
        db.query(WeeklyXP)
        .filter(
            WeeklyXP.user_id == user.id,
            WeeklyXP.week_start_date == week_start,
        )
        .first()
    )
    if not weekly_xp:
        weekly_xp = WeeklyXP(
            user_id=user.id,
            week_start_date=week_start,
            xp_earned=xp_earned,
        )
        db.add(weekly_xp)
    else:
        weekly_xp.xp_earned += xp_earned

    # Check skill and unit completion
    skill = lesson.skill
    unit = skill.unit
    skill_completed = is_skill_completed(user.id, skill, db)
    unit_completed = is_unit_completed(user.id, unit, db)

    # Evaluate achievements
    new_achievements = update_user_achievements(
        user=user,
        accuracy=accuracy,
        skill_completed=skill_completed,
        unit_completed=unit_completed,
        db=db,
    )

    db.commit()
    db.refresh(user)
    db.refresh(attempt)

    crowns_after = get_user_total_crowns(user.id, db)

    return {
        "attempt_id": attempt.id,
        "status": "completed",
        "xp_earned": xp_earned,
        "accuracy": accuracy,
        "hearts_lost": attempt.hearts_lost,
        "is_replay": is_replay,
        "new_crown_earned": new_crown_earned,
        "streak_current": user.streak_current,
        "time_spent_seconds": time_spent_seconds,
        "crowns_after": crowns_after,
        "skill_completed": skill_completed,
        "unit_completed": unit_completed,
        "new_achievements": new_achievements,
        "streak_extended": streak_extended,
    }


def update_user_achievements(
    user: User,
    accuracy: float,
    skill_completed: bool,
    unit_completed: bool,
    db: Session,
) -> list[str]:
    """Evaluate and unlock milestones for all 8 seeded achievements."""
    achievements = db.query(Achievement).all()
    newly_unlocked = []
    completed_lessons_count = (
        db.query(UserLessonProgress)
        .filter(UserLessonProgress.user_id == user.id, UserLessonProgress.is_completed.is_(True))
        .count()
    )

    for ach in achievements:
        user_ach = (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == ach.id,
            )
            .first()
        )
        if not user_ach:
            user_ach = UserAchievement(
                user_id=user.id,
                achievement_id=ach.id,
                current_value=0,
                is_unlocked=False,
            )
            db.add(user_ach)

        if user_ach.is_unlocked:
            continue

        # Evaluate progress based on condition_type / code
        target = ach.threshold
        is_met = False

        if ach.code == "first_lesson":
            user_ach.current_value = min(target, completed_lessons_count)
            is_met = completed_lessons_count >= target
        elif ach.code == "streak_3":
            user_ach.current_value = min(target, user.streak_current)
            is_met = user.streak_current >= target
        elif ach.code == "streak_7":
            user_ach.current_value = min(target, user.streak_current)
            is_met = user.streak_current >= target
        elif ach.code == "xp_100":
            user_ach.current_value = min(target, user.xp_total)
            is_met = user.xp_total >= target
        elif ach.code == "xp_500":
            user_ach.current_value = min(target, user.xp_total)
            is_met = user.xp_total >= target
        elif ach.code == "perfect_lesson":
            if accuracy >= 1.0:
                user_ach.current_value = 1
                is_met = True
        elif ach.code == "skill_complete":
            if skill_completed:
                user_ach.current_value = 1
                is_met = True
        elif ach.code == "unit_complete":
            if unit_completed:
                user_ach.current_value = 1
                is_met = True

        if is_met:
            user_ach.is_unlocked = True
            user_ach.unlocked_at = get_user_logical_now(user)
            newly_unlocked.append(ach.code)

    return newly_unlocked

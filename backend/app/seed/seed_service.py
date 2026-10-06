"""Deterministic, idempotent seed service for LinguaQuest database."""

import json
import logging
import random
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.course import Course, Exercise, Lesson, Skill, Unit
from app.models.gamification import Achievement, DailyActivity, UserAchievement, WeeklyXP
from app.models.progress import UserLessonProgress
from app.models.user import User
from app.seed.curriculum_data import (
    ACHIEVEMENTS_DATA,
    BOT_USERS_DATA,
    COURSE_DATA,
    UNITS_DATA,
)
from app.services.clock import get_logical_date, get_logical_now, get_week_start_date

logger = logging.getLogger(__name__)


def build_exercise_payload_and_answer(ex_def: dict) -> tuple[str, str]:
    """Transform exercise definition into client-safe payload_json and authoritative answer_json."""
    ex_type = ex_def["type"]

    if ex_type == "match_pairs":
        raw_pairs = ex_def["pairs"]  # list of (left_text, right_text)
        left_items = []
        right_items = []
        matches = {}

        for i, (l_text, r_text) in enumerate(raw_pairs):
            l_id = f"l_{i + 1}"
            r_id = f"r_{i + 1}"
            left_items.append({"id": l_id, "text": l_text})
            right_items.append({"id": r_id, "text": r_text})
            matches[l_id] = r_id

        # Deterministically permute the right items so they don't line up with left items
        # Rotate right items by fixed offset
        n = len(right_items)
        if n > 1:
            permuted_right = [right_items[(j + 1) % n] for j in range(n)]
        else:
            permuted_right = right_items

        payload = {
            "prompt": "Match the pairs",
            "left": left_items,
            "right": permuted_right,
        }
        answer = {
            "matches": matches,
        }

    elif ex_type == "translate":
        tokens = ex_def["tokens"]
        distractors = ex_def.get("distractors", [])
        # Combine tokens and distractors and sort/shuffle deterministically
        word_bank = list(tokens) + list(distractors)
        # Deterministic shuffle using fixed seed based on prompt length
        rng = random.Random(len(ex_def["prompt"]))
        rng.shuffle(word_bank)

        payload = {
            "prompt": ex_def["prompt"],
            "direction": ex_def["direction"],
            "word_bank": word_bank,
        }
        answer = {
            "tokens": tokens,
            "accepted_token_sequences": [
                tokens,
                [t.lower() for t in tokens],
            ],
        }

    elif ex_type == "multiple_choice":
        payload = {
            "prompt": ex_def["prompt"],
            "options": ex_def["options"],
        }
        answer = {
            "correct_option": ex_def["correct"],
        }

    elif ex_type == "fill_blank":
        payload = {
            "prompt": ex_def["prompt"],
            "options": ex_def["options"],
        }
        answer = {
            "correct_option": ex_def["correct"],
        }

    elif ex_type == "type_answer":
        payload = {
            "prompt": ex_def["prompt"],
            "placeholder": "Type in Spanish...",
        }
        answer = {
            "accepted_answers": ex_def["accepted"],
        }

    else:
        raise ValueError(f"Unsupported exercise type: {ex_type}")

    return json.dumps(payload, ensure_ascii=False), json.dumps(answer, ensure_ascii=False)


def seed_database(db: Optional[Session] = None) -> dict[str, int]:
    """Execute deterministic, idempotent database seeding.

    Never overwrites user 1 progress on subsequent executions.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        now_utc = get_logical_now(0)
        today_date = get_logical_date(0, "UTC")
        week_start = get_week_start_date(today_date)

        # -------------------------------------------------------------
        # 1. Course Seeding (Upsert by code)
        # -------------------------------------------------------------
        course = db.query(Course).filter(Course.code == COURSE_DATA["code"]).first()
        if not course:
            course = Course(
                code=COURSE_DATA["code"],
                title=COURSE_DATA["title"],
                description=COURSE_DATA["description"],
                flag_emoji=COURSE_DATA["flag_emoji"],
                created_at=now_utc,
            )
            db.add(course)
            db.flush()
        else:
            course.title = COURSE_DATA["title"]
            course.description = COURSE_DATA["description"]
            course.flag_emoji = COURSE_DATA["flag_emoji"]
            db.flush()

        # -------------------------------------------------------------
        # 2. Units, Skills, Lessons, Exercises Seeding
        # -------------------------------------------------------------
        lesson_cache: dict[str, Lesson] = {}

        for u_def in UNITS_DATA:
            unit = (
                db.query(Unit)
                .filter(Unit.course_id == course.id, Unit.slug == u_def["slug"])
                .first()
            )
            if not unit:
                unit = Unit(
                    course_id=course.id,
                    unit_order=u_def["unit_order"],
                    slug=u_def["slug"],
                    title=u_def["title"],
                    description=u_def["description"],
                    created_at=now_utc,
                )
                db.add(unit)
                db.flush()
            else:
                unit.unit_order = u_def["unit_order"]
                unit.title = u_def["title"]
                unit.description = u_def["description"]
                db.flush()

            for s_def in u_def["skills"]:
                skill = (
                    db.query(Skill)
                    .filter(Skill.unit_id == unit.id, Skill.slug == s_def["slug"])
                    .first()
                )
                if not skill:
                    skill = Skill(
                        unit_id=unit.id,
                        skill_order=s_def["skill_order"],
                        slug=s_def["slug"],
                        name=s_def["name"],
                        description=s_def["description"],
                        icon_name=s_def["icon_name"],
                        total_crowns=5,
                        created_at=now_utc,
                    )
                    db.add(skill)
                    db.flush()
                else:
                    skill.skill_order = s_def["skill_order"]
                    skill.name = s_def["name"]
                    skill.description = s_def["description"]
                    skill.icon_name = s_def["icon_name"]
                    db.flush()

                for l_def in s_def["lessons"]:
                    lesson = (
                        db.query(Lesson)
                        .filter(Lesson.skill_id == skill.id, Lesson.slug == l_def["slug"])
                        .first()
                    )
                    if not lesson:
                        lesson = Lesson(
                            skill_id=skill.id,
                            lesson_order=l_def["lesson_order"],
                            slug=l_def["slug"],
                            title=l_def["title"],
                            created_at=now_utc,
                        )
                        db.add(lesson)
                        db.flush()
                    else:
                        lesson.lesson_order = l_def["lesson_order"]
                        lesson.title = l_def["title"]
                        db.flush()

                    lesson_cache[l_def["slug"]] = lesson

                    for e_def in l_def["exercises"]:
                        payload_json, answer_json = build_exercise_payload_and_answer(e_def)
                        exercise = (
                            db.query(Exercise)
                            .filter(Exercise.lesson_id == lesson.id, Exercise.slug == e_def["slug"])
                            .first()
                        )
                        if not exercise:
                            exercise = Exercise(
                                lesson_id=lesson.id,
                                exercise_order=e_def["exercise_order"],
                                slug=e_def["slug"],
                                type=e_def["type"],
                                payload_json=payload_json,
                                answer_json=answer_json,
                                created_at=now_utc,
                            )
                            db.add(exercise)
                        else:
                            exercise.exercise_order = e_def["exercise_order"]
                            exercise.type = e_def["type"]
                            exercise.payload_json = payload_json
                            exercise.answer_json = answer_json
                        db.flush()

        # -------------------------------------------------------------
        # 3. Achievements Seeding (Upsert by code)
        # -------------------------------------------------------------
        achievement_cache: dict[str, Achievement] = {}
        for a_def in ACHIEVEMENTS_DATA:
            ach = db.query(Achievement).filter(Achievement.code == a_def["code"]).first()
            if not ach:
                ach = Achievement(
                    code=a_def["code"],
                    title=a_def["title"],
                    description=a_def["description"],
                    badge_icon=a_def["badge_icon"],
                    condition_type=a_def["condition_type"],
                    threshold=a_def["threshold"],
                    created_at=now_utc,
                )
                db.add(ach)
                db.flush()
            else:
                ach.title = a_def["title"]
                ach.description = a_def["description"]
                ach.badge_icon = a_def["badge_icon"]
                ach.condition_type = a_def["condition_type"]
                ach.threshold = a_def["threshold"]
                db.flush()
            achievement_cache[a_def["code"]] = ach

        # -------------------------------------------------------------
        # 4. Default Learner (User 1) - ONLY SEEDED IF MISSING
        # -------------------------------------------------------------
        user_1 = db.query(User).filter((User.id == 1) | (User.username == "duo_learner")).first()
        if user_1:
            logger.info("User 1 already exists. Preserving existing user 1 progress.")
        else:
            # Seed default learner baseline
            user_1 = User(
                id=1,
                username="duo_learner",
                is_bot=False,
                hearts=4,
                hearts_updated_at=now_utc,
                xp_total=125,
                gems=500,
                streak_current=3,
                daily_xp_goal=20,
                dark_mode=False,
                sound_enabled=True,
                date_offset_days=0,
                timezone="UTC",
                created_at=now_utc - timedelta(days=3),
                updated_at=now_utc,
            )
            db.add(user_1)
            db.flush()

            # Baseline Progress:
            # Skill 1 complete (all 3 lessons)
            s1_lessons = ["greetings-l1", "greetings-l2", "greetings-l3"]
            for days_ago, l_slug in enumerate([2, 1, 1]):
                lesson_obj = lesson_cache.get(s1_lessons[days_ago])
                if lesson_obj:
                    p = UserLessonProgress(
                        user_id=user_1.id,
                        lesson_id=lesson_obj.id,
                        is_completed=True,
                        score=100,
                        completed_at=now_utc - timedelta(days=l_slug, hours=2),
                        updated_at=now_utc - timedelta(days=l_slug, hours=2),
                    )
                    db.add(p)

            # Skill 2 has 1 lesson completed (introductions-l1)
            s2_l1 = lesson_cache.get("introductions-l1")
            if s2_l1:
                p2 = UserLessonProgress(
                    user_id=user_1.id,
                    lesson_id=s2_l1.id,
                    is_completed=True,
                    score=100,
                    completed_at=now_utc - timedelta(hours=1),
                    updated_at=now_utc - timedelta(hours=1),
                )
                db.add(p2)

            # Daily activity for User 1: 3-day streak
            # Day -2: 45 XP, 2 lessons
            # Day -1: 45 XP, 2 lessons
            # Today:  35 XP, 1 lesson
            # Total XP: 125 XP, 5 completed lessons!
            day_records = [
                (today_date - timedelta(days=2), 45, 2),
                (today_date - timedelta(days=1), 45, 2),
                (today_date, 35, 1),
            ]
            for act_date, xp, l_count in day_records:
                da = DailyActivity(
                    user_id=user_1.id,
                    activity_date=act_date,
                    xp_earned=xp,
                    lessons_completed=l_count,
                    created_at=now_utc,
                )
                db.add(da)

            # Weekly XP for User 1
            u1_wxp = WeeklyXP(
                user_id=user_1.id,
                week_start_date=week_start,
                xp_earned=125,
                updated_at=now_utc,
            )
            db.add(u1_wxp)

            # User achievements baseline
            initial_user_achievements = [
                ("first_lesson", 4, True, now_utc - timedelta(days=2)),
                ("streak_3", 3, True, now_utc),
                ("streak_7", 3, False, None),
                ("xp_100", 125, True, now_utc),
                ("xp_500", 125, False, None),
                ("perfect_lesson", 4, True, now_utc - timedelta(days=2)),
                ("skill_complete", 1, True, now_utc - timedelta(days=1)),
                ("unit_complete", 0, False, None),
            ]
            for ach_code, curr_val, is_unlocked, unl_at in initial_user_achievements:
                ach_obj = achievement_cache.get(ach_code)
                if ach_obj:
                    ua = UserAchievement(
                        user_id=user_1.id,
                        achievement_id=ach_obj.id,
                        current_value=curr_val,
                        is_unlocked=is_unlocked,
                        unlocked_at=unl_at,
                        created_at=now_utc,
                        updated_at=now_utc,
                    )
                    db.add(ua)

            db.flush()

        # -------------------------------------------------------------
        # 5. Bot Users & Bot Weekly XP Seeding
        # -------------------------------------------------------------
        for b_def in BOT_USERS_DATA:
            bot = db.query(User).filter(User.username == b_def["username"]).first()
            if not bot:
                bot = User(
                    username=b_def["username"],
                    is_bot=True,
                    hearts=5,
                    hearts_updated_at=now_utc,
                    xp_total=b_def["xp_total"],
                    gems=500,
                    streak_current=b_def["streak"],
                    daily_xp_goal=20,
                    dark_mode=False,
                    sound_enabled=True,
                    date_offset_days=0,
                    timezone="UTC",
                    created_at=now_utc - timedelta(days=30),
                    updated_at=now_utc,
                )
                db.add(bot)
                db.flush()
            else:
                bot.xp_total = b_def["xp_total"]
                bot.streak_current = b_def["streak"]
                db.flush()

            # Bot weekly XP for current week
            bot_wxp = (
                db.query(WeeklyXP)
                .filter(WeeklyXP.user_id == bot.id, WeeklyXP.week_start_date == week_start)
                .first()
            )
            if not bot_wxp:
                bot_wxp = WeeklyXP(
                    user_id=bot.id,
                    week_start_date=week_start,
                    xp_earned=b_def["xp_weekly"],
                    updated_at=now_utc,
                )
                db.add(bot_wxp)
            else:
                bot_wxp.xp_earned = b_def["xp_weekly"]
            db.flush()

        db.commit()

        # Compute count summaries
        counts = {
            "courses": db.query(Course).count(),
            "units": db.query(Unit).count(),
            "skills": db.query(Skill).count(),
            "lessons": db.query(Lesson).count(),
            "exercises": db.query(Exercise).count(),
            "achievements": db.query(Achievement).count(),
            "users": db.query(User).count(),
            "weekly_xp": db.query(WeeklyXP).count(),
        }
        return counts

    except Exception:
        db.rollback()
        raise
    finally:
        if should_close:
            db.close()

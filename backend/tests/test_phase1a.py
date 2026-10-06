"""Focused tests verifying the Phase 1A database models, seed idempotency, and constraints."""

import json

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine, init_db
from app.models.course import Exercise, Lesson
from app.models.progress import LessonAttempt
from app.models.user import User
from app.seed.seed_service import seed_database


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure database tables and clean seed data are initialized."""
    init_db()
    yield


def test_all_13_tables_created():
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "users",
        "courses",
        "units",
        "skills",
        "lessons",
        "exercises",
        "user_lesson_progress",
        "lesson_attempts",
        "attempt_answers",
        "daily_activity",
        "weekly_xp",
        "achievements",
        "user_achievements",
    }
    for expected in expected_tables:
        assert expected in table_names, f"Table {expected} was not created!"


def test_legacy_tables_do_not_exist():
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert "lesson_completions" not in table_names
    assert "user_skill_progress" not in table_names


def test_skills_table_omits_crown_count_and_xp_reward():
    inspector = inspect(engine)
    skill_cols = {col["name"] for col in inspector.get_columns("skills")}
    assert "crown_count" not in skill_cols, "skills table must not contain crown_count"
    assert "xp_reward" not in skill_cols, "skills table must not contain xp_reward"


def test_users_table_columns_and_constraints():
    inspector = inspect(engine)
    user_cols = {col["name"] for col in inspector.get_columns("users")}
    # Locked user columns
    assert "is_bot" in user_cols
    assert "date_offset_days" in user_cols
    assert "timezone" in user_cols
    assert "dark_mode" in user_cols
    assert "sound_enabled" in user_cols
    assert "daily_xp_goal" in user_cols
    assert "hearts" in user_cols
    assert "hearts_updated_at" in user_cols
    assert "gems" in user_cols
    assert "xp_total" in user_cols
    # Verify unauthorized email field is NOT in users table
    assert "email" not in user_cols

    # Verify check constraints
    db = SessionLocal()
    try:
        # Invalid hearts (> 5) should fail CHECK constraint
        with pytest.raises(IntegrityError):
            invalid_user = User(username="invalid_hearts", hearts=6, xp_total=0)
            db.add(invalid_user)
            db.commit()
        db.rollback()

        # Negative XP should fail CHECK constraint
        with pytest.raises(IntegrityError):
            invalid_xp_user = User(username="invalid_xp", hearts=5, xp_total=-10)
            db.add(invalid_xp_user)
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_sqlite_foreign_keys_pragma_enabled():
    with engine.connect() as conn:
        fk_status = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_status == 1, "PRAGMA foreign_keys must be 1 (ON)"


def test_seed_idempotency_and_counts():
    """Verify seed runs cleanly twice without duplicating rows."""
    db = SessionLocal()
    try:
        counts_first = seed_database(db)

        # Baseline expected row counts
        assert counts_first["courses"] == 1
        assert counts_first["units"] == 3
        assert counts_first["skills"] == 9
        assert counts_first["lessons"] == 27
        assert counts_first["exercises"] == 216
        assert counts_first["achievements"] == 8
        assert counts_first["users"] >= 16  # User 1 + 15 bots

        # Run seed second time
        counts_second = seed_database(db)

        assert counts_second["courses"] == counts_first["courses"]
        assert counts_second["units"] == counts_first["units"]
        assert counts_second["skills"] == counts_first["skills"]
        assert counts_second["lessons"] == counts_first["lessons"]
        assert counts_second["exercises"] == counts_first["exercises"]
        assert counts_second["achievements"] == counts_first["achievements"]
        assert counts_second["users"] == counts_first["users"]
        assert counts_second["weekly_xp"] == counts_first["weekly_xp"]
    finally:
        db.close()


def test_user_1_progress_not_overwritten_on_second_seed():
    """Verify user 1's state is preserved if seed runs again."""
    db = SessionLocal()
    try:
        seed_database(db)

        user_1 = db.query(User).filter(User.id == 1).first()
        assert user_1 is not None
        initial_xp = user_1.xp_total
        initial_gems = user_1.gems

        # Simulate user 1 earning extra XP and spending gems
        user_1.xp_total = 999
        user_1.gems = 150
        db.commit()

        # Re-run seed
        seed_database(db)

        # Reload user 1
        db.refresh(user_1)
        assert user_1.xp_total == 999, "User 1 XP was overwritten by seed!"
        assert user_1.gems == 150, "User 1 gems were overwritten by seed!"

        # Reset back for clean testing
        user_1.xp_total = initial_xp
        user_1.gems = initial_gems
        db.commit()
    finally:
        db.close()


def test_exercise_payload_never_leaks_answer():
    """Verify payload_json across all exercises contains zero answer keys."""
    db = SessionLocal()
    try:
        seed_database(db)
        exercises = db.query(Exercise).all()
        assert len(exercises) == 216

        for ex in exercises:
            payload = json.loads(ex.payload_json)
            answer = json.loads(ex.answer_json)

            # payload must not have answer fields
            assert "matches" not in payload
            assert "correct_option" not in payload
            assert "accepted_answers" not in payload
            assert "tokens" not in payload
            assert "accepted_token_sequences" not in payload

            # type-specific checks
            if ex.type == "match_pairs":
                assert "left" in payload
                assert "right" in payload
                assert "matches" in answer
                # Left and right have separate ID namespaces
                left_ids = {item["id"] for item in payload["left"]}
                right_ids = {item["id"] for item in payload["right"]}
                assert len(left_ids.intersection(right_ids)) == 0
            elif ex.type == "translate":
                assert "prompt" in payload
                assert "direction" in payload
                assert "word_bank" in payload
                assert "tokens" in answer
                assert "accepted_token_sequences" in answer
            elif ex.type in ("multiple_choice", "fill_blank"):
                assert "options" in payload
                assert "correct_option" in answer
            elif ex.type == "type_answer":
                assert "placeholder" in payload
                assert "accepted_answers" in answer
    finally:
        db.close()


def test_unique_in_progress_attempt_invariant():
    """Verify at most one in_progress attempt per (user, lesson) is enforced."""
    db = SessionLocal()
    try:
        seed_database(db)
        user_1 = db.query(User).filter(User.id == 1).first()
        lesson_1 = db.query(Lesson).first()

        # Clear any preexisting attempts for clean isolation in this test
        db.query(LessonAttempt).filter(
            LessonAttempt.user_id == user_1.id,
            LessonAttempt.lesson_id == lesson_1.id,
        ).delete()
        db.commit()

        # First in_progress attempt succeeds
        att1 = LessonAttempt(
            user_id=user_1.id,
            lesson_id=lesson_1.id,
            status="in_progress",
        )
        db.add(att1)
        db.commit()

        # Second in_progress attempt for the SAME (user, lesson)
        # must violate the partial unique index
        att2 = LessonAttempt(
            user_id=user_1.id,
            lesson_id=lesson_1.id,
            status="in_progress",
        )
        db.add(att2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # Changing att1 to completed allows a new in_progress attempt
        att1 = db.query(LessonAttempt).filter(LessonAttempt.id == att1.id).first()
        att1.status = "completed"
        db.commit()

        att3 = LessonAttempt(
            user_id=user_1.id,
            lesson_id=lesson_1.id,
            status="in_progress",
        )
        db.add(att3)
        db.commit()
        assert att3.id is not None
    finally:
        db.close()

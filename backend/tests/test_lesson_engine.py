"""Phase 1B tests: Lesson engine, exercise checking, hearts, streaks, and gamification."""

import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models.course import Exercise
from app.models.gamification import DailyActivity, UserAchievement, WeeklyXP
from app.models.progress import AttemptAnswer, LessonAttempt, UserLessonProgress
from app.models.user import User
from app.seed import seed_database
from app.services.exercise_evaluator import evaluate_exercise
from app.services.hearts import calculate_heart_regen, deduct_heart
from app.services.progress_service import clear_debug_unlock_all

client = TestClient(app)


def reset_user_1_state(db: Session) -> User:
    """Helper to set user 1 back to standard starting baseline."""
    clear_debug_unlock_all(1)
    # Clean up attempts and progress
    db.query(AttemptAnswer).delete()
    db.query(LessonAttempt).delete()
    db.query(UserLessonProgress).delete()
    db.query(DailyActivity).delete()
    db.query(WeeklyXP).delete()
    db.query(UserAchievement).delete()

    user = db.query(User).filter(User.id == 1).first()
    if not user:
        seed_database(db)
        user = db.query(User).filter(User.id == 1).first()

    now_utc = datetime.now(timezone.utc)
    user.hearts = 5
    user.hearts_updated_at = now_utc
    user.xp_total = 0
    user.gems = 500
    user.streak_current = 0
    user.date_offset_days = 0
    db.commit()
    db.refresh(user)
    return user


# -----------------------------------------------------------------------------
# 1. Heart loss while full does NOT instantly regenerate
# -----------------------------------------------------------------------------
def test_heart_loss_while_full_does_not_instantly_regenerate():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        assert user.hearts == 5

        # Deduct 1 heart when user has 5 hearts
        hearts_rem, exhausted = deduct_heart(user, db)
        assert hearts_rem == 4
        assert not exhausted

        # Verify hearts_updated_at was set to current time
        # Calling calculate_heart_regen immediately should NOT grant a heart back!
        user = calculate_heart_regen(user, db)
        assert user.hearts == 4, "Heart must not instantly regenerate upon loss!"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 2, 3, 4. Heart regeneration after 5h, 10h, and 25h
# -----------------------------------------------------------------------------
def test_heart_regeneration_after_5h():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        user.hearts = 3
        # Set hearts_updated_at to 5 hours + 10 seconds ago
        user.hearts_updated_at = datetime.now(timezone.utc) - timedelta(hours=5, seconds=10)
        db.commit()

        user = calculate_heart_regen(user, db)
        assert user.hearts == 4, "After 5h, user should regenerate exactly 1 heart"
    finally:
        db.close()


def test_heart_regeneration_after_10h():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        user.hearts = 2
        # Set hearts_updated_at to 10 hours + 10 seconds ago
        user.hearts_updated_at = datetime.now(timezone.utc) - timedelta(hours=10, seconds=10)
        db.commit()

        user = calculate_heart_regen(user, db)
        assert user.hearts == 4, "After 10h, user should regenerate exactly 2 hearts"
    finally:
        db.close()


def test_heart_regeneration_after_25h_caps_at_max():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        user.hearts = 1
        # Set hearts_updated_at to 25 hours ago (5 intervals)
        user.hearts_updated_at = datetime.now(timezone.utc) - timedelta(hours=25)
        db.commit()

        user = calculate_heart_regen(user, db)
        assert user.hearts == 5, "After 25h, hearts must regenerate and cap at 5"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 5. 0 hearts blocks lesson start (HTTP 409)
# -----------------------------------------------------------------------------
def test_zero_hearts_blocks_lesson_start():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        user.hearts = 0
        user.hearts_updated_at = datetime.now(timezone.utc)  # updated just now
        db.commit()

        res = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        assert res.status_code == 409
        assert res.json()["detail"] == "OUT_OF_HEARTS"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 6. Wrong final heart fails lesson
# -----------------------------------------------------------------------------
def test_wrong_final_heart_fails_lesson():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        user.hearts = 1
        db.commit()

        # Start attempt for lesson 1
        res = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        assert res.status_code == 201
        attempt_id = res.json()["attempt_id"]
        exercise_id = res.json()["exercises"][0]["id"]

        # Submit deliberately wrong answer
        check_res = client.post(
            f"/api/attempts/{attempt_id}/check",
            json={"exercise_id": exercise_id, "user_answer": "totally_wrong_answer_xyz"},
            headers={"X-User-Id": "1"},
        )
        assert check_res.status_code == 200
        data = check_res.json()
        assert data["is_correct"] is False
        assert data["hearts_remaining"] == 0
        assert data["attempt_status"] == "failed"
        assert data["lesson_failed"] is True

        # Verify attempt in DB is marked failed
        db.refresh(user)
        assert user.hearts == 0
        att = db.query(LessonAttempt).filter(LessonAttempt.id == attempt_id).first()
        assert att.status == "failed"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 7. Same-day streak activity twice
# -----------------------------------------------------------------------------
def test_same_day_streak_activity_twice():
    db = SessionLocal()
    try:
        reset_user_1_state(db)
        exercises = db.query(Exercise).filter(Exercise.lesson_id == 1).all()

        # Complete lesson 1 first time today
        start_res = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att1_id = start_res.json()["attempt_id"]

        for ex in exercises:
            ans_spec = json.loads(ex.answer_json)
            # Answer correctly
            if ex.type in ("multiple_choice", "fill_blank"):
                ans = ans_spec["correct_option"]
            elif ex.type == "translate":
                ans = ans_spec["tokens"]
            elif ex.type == "match_pairs":
                ans = ans_spec["matches"]
            else:
                ans = ans_spec["accepted_answers"][0]

            client.post(
                f"/api/attempts/{att1_id}/check",
                json={"exercise_id": ex.id, "user_answer": ans},
                headers={"X-User-Id": "1"},
            )

        comp1_res = client.post(f"/api/attempts/{att1_id}/complete", headers={"X-User-Id": "1"})
        assert comp1_res.status_code == 200
        assert comp1_res.json()["streak_current"] == 1
        assert comp1_res.json()["streak_extended"] is True

        # Complete lesson 1 second time today (replay)
        start_res2 = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att2_id = start_res2.json()["attempt_id"]

        for ex in exercises:
            ans_spec = json.loads(ex.answer_json)
            if ex.type in ("multiple_choice", "fill_blank"):
                ans = ans_spec["correct_option"]
            elif ex.type == "translate":
                ans = ans_spec["tokens"]
            elif ex.type == "match_pairs":
                ans = ans_spec["matches"]
            else:
                ans = ans_spec["accepted_answers"][0]

            client.post(
                f"/api/attempts/{att2_id}/check",
                json={"exercise_id": ex.id, "user_answer": ans},
                headers={"X-User-Id": "1"},
            )

        comp2_res = client.post(f"/api/attempts/{att2_id}/complete", headers={"X-User-Id": "1"})
        assert comp2_res.status_code == 200
        # Same-day activity should NOT increment streak again!
        assert comp2_res.json()["streak_current"] == 1
        assert comp2_res.json()["streak_extended"] is False
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 8 & 9. Advance-day and missed day/reset behavior
# -----------------------------------------------------------------------------
def test_advance_day_and_streak_progression():
    db = SessionLocal()
    try:
        reset_user_1_state(db)
        exercises = db.query(Exercise).filter(Exercise.lesson_id == 1).all()

        # Day 0: Complete a lesson -> streak = 1
        res = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att1_id = res.json()["attempt_id"]
        for ex in exercises:
            ans_spec = json.loads(ex.answer_json)
            ans = (
                ans_spec.get("correct_option")
                or ans_spec.get("tokens")
                or ans_spec.get("matches")
                or ans_spec["accepted_answers"][0]
            )
            client.post(
                f"/api/attempts/{att1_id}/check",
                json={"exercise_id": ex.id, "user_answer": ans},
                headers={"X-User-Id": "1"},
            )
        client.post(f"/api/attempts/{att1_id}/complete", headers={"X-User-Id": "1"})

        me_res = client.get("/api/me", headers={"X-User-Id": "1"})
        assert me_res.json()["streak_current"] == 1
        assert me_res.json()["streak_active_today"] is True

        # Advance 1 day (consecutive active day)
        adv_res = client.post(
            "/api/debug/advance-day", json={"days": 1}, headers={"X-User-Id": "1"}
        )
        assert adv_res.status_code == 200

        # On next consecutive day, complete lesson again
        res2 = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att2_id = res2.json()["attempt_id"]
        for ex in exercises:
            ans_spec = json.loads(ex.answer_json)
            ans = (
                ans_spec.get("correct_option")
                or ans_spec.get("tokens")
                or ans_spec.get("matches")
                or ans_spec["accepted_answers"][0]
            )
            client.post(
                f"/api/attempts/{att2_id}/check",
                json={"exercise_id": ex.id, "user_answer": ans},
                headers={"X-User-Id": "1"},
            )
        comp_res2 = client.post(f"/api/attempts/{att2_id}/complete", headers={"X-User-Id": "1"})
        assert comp_res2.json()["streak_current"] == 2
        assert comp_res2.json()["streak_extended"] is True

        # Now skip 2 days (missed day)
        client.post("/api/debug/advance-day", json={"days": 2}, headers={"X-User-Id": "1"})

        # Practice after missing a day -> streak resets to 1
        res3 = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att3_id = res3.json()["attempt_id"]
        for ex in exercises:
            ans_spec = json.loads(ex.answer_json)
            ans = (
                ans_spec.get("correct_option")
                or ans_spec.get("tokens")
                or ans_spec.get("matches")
                or ans_spec["accepted_answers"][0]
            )
            client.post(
                f"/api/attempts/{att3_id}/check",
                json={"exercise_id": ex.id, "user_answer": ans},
                headers={"X-User-Id": "1"},
            )
        comp_res3 = client.post(f"/api/attempts/{att3_id}/complete", headers={"X-User-Id": "1"})
        assert comp_res3.json()["streak_current"] == 1
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 10. Completion idempotency
# -----------------------------------------------------------------------------
def test_completion_idempotency():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        exercises = db.query(Exercise).filter(Exercise.lesson_id == 1).all()

        start_res = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att_id = start_res.json()["attempt_id"]
        for ex in exercises:
            ans_spec = json.loads(ex.answer_json)
            ans = (
                ans_spec.get("correct_option")
                or ans_spec.get("tokens")
                or ans_spec.get("matches")
                or ans_spec["accepted_answers"][0]
            )
            client.post(
                f"/api/attempts/{att_id}/check",
                json={"exercise_id": ex.id, "user_answer": ans},
                headers={"X-User-Id": "1"},
            )

        first_comp = client.post(f"/api/attempts/{att_id}/complete", headers={"X-User-Id": "1"})
        assert first_comp.status_code == 200
        xp1 = first_comp.json()["xp_earned"]

        # Re-calling complete on already completed attempt should return identical result
        second_comp = client.post(f"/api/attempts/{att_id}/complete", headers={"X-User-Id": "1"})
        assert second_comp.status_code == 200
        assert second_comp.json()["attempt_id"] == att_id
        assert second_comp.json()["status"] == "completed"
        assert second_comp.json()["xp_earned"] == xp1

        # User XP in DB should not be awarded twice
        db.refresh(user)
        assert user.xp_total == xp1
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 11. Unanswered completion rejected (HTTP 400 INVALID_COMPLETION)
# -----------------------------------------------------------------------------
def test_unanswered_completion_rejected():
    db = SessionLocal()
    try:
        reset_user_1_state(db)
        start_res = client.post("/api/lessons/1/start", headers={"X-User-Id": "1"})
        att_id = start_res.json()["attempt_id"]

        # Attempt to complete without answering all questions
        res = client.post(f"/api/attempts/{att_id}/complete", headers={"X-User-Id": "1"})
        assert res.status_code == 400
        assert res.json()["detail"] == "INVALID_COMPLETION"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 12. Locked lesson rejected (HTTP 403 LESSON_LOCKED)
# -----------------------------------------------------------------------------
def test_locked_lesson_rejected():
    db = SessionLocal()
    try:
        reset_user_1_state(db)
        # Lesson 2 requires completing Lesson 1 first
        res = client.post("/api/lessons/2/start", headers={"X-User-Id": "1"})
        assert res.status_code == 403
        assert res.json()["detail"] == "LESSON_LOCKED"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 13. Leaderboard nonempty after Monday/week initialization
# -----------------------------------------------------------------------------
def test_leaderboard_nonempty_after_week_initialization():
    db = SessionLocal()
    try:
        reset_user_1_state(db)
        res = client.get("/api/leaderboard", headers={"X-User-Id": "1"})
        assert res.status_code == 200
        data = res.json()
        assert "week_start_date" in data
        assert len(data["rankings"]) >= 16  # User 1 + 15 bots
        # Current user must be highlighted
        current_users = [r for r in data["rankings"] if r["is_current_user"]]
        assert len(current_users) == 1
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 14. Seed twice creates no duplicates
# -----------------------------------------------------------------------------
def test_seed_twice_creates_no_duplicates():
    db = SessionLocal()
    try:
        c1 = seed_database(db)
        c2 = seed_database(db)
        assert c1 == c2
        assert c1["lessons"] == 27
        assert c1["exercises"] == 216
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 15. Representative answer checking for ALL FIVE exercise types
# -----------------------------------------------------------------------------
def test_exercise_type_multiple_choice():
    payload = json.dumps({"options": ["El niño", "La niña", "El agua"]})
    answer = json.dumps({"correct_option": "El niño"})

    # Exact match
    ok, ans, exp = evaluate_exercise("multiple_choice", payload, answer, "El niño")
    assert ok is True
    assert exp is None

    # Case insensitive
    ok, ans, exp = evaluate_exercise("multiple_choice", payload, answer, "el niño")
    assert ok is True

    # Accent difference
    ok, ans, exp = evaluate_exercise("multiple_choice", payload, answer, "El nino")
    assert ok is True
    assert exp == "Pay attention to accents."

    # Wrong
    ok, ans, exp = evaluate_exercise("multiple_choice", payload, answer, "La niña")
    assert ok is False


def test_exercise_type_fill_blank():
    payload = json.dumps({"prompt": "Yo ___ pan.", "options": ["como", "comes", "come"]})
    answer = json.dumps({"correct_option": "como"})

    ok, ans, exp = evaluate_exercise("fill_blank", payload, answer, "como")
    assert ok is True
    assert ans == "como"

    ok, ans, exp = evaluate_exercise("fill_blank", payload, answer, "comes")
    assert ok is False


def test_exercise_type_type_answer():
    payload = json.dumps({"prompt": "Translate 'The girl'"})
    answer = json.dumps({"accepted_answers": ["La niña", "Una niña"]})

    # Exact
    ok, ans, exp = evaluate_exercise("type_answer", payload, answer, "La niña")
    assert ok is True
    assert exp is None

    # Alternative accepted
    ok, ans, exp = evaluate_exercise("type_answer", payload, answer, "una niña")
    assert ok is True

    # Accent difference
    ok, ans, exp = evaluate_exercise("type_answer", payload, answer, "la nina")
    assert ok is True
    assert exp == "Pay attention to accents."

    # Wrong
    ok, ans, exp = evaluate_exercise("type_answer", payload, answer, "el niño")
    assert ok is False


def test_exercise_type_translate():
    payload = json.dumps({"word_bank": ["El", "hombre", "come", "manzanas"]})
    answer = json.dumps(
        {
            "tokens": ["El", "hombre", "come"],
            "accepted_token_sequences": [["El", "hombre", "come"], ["el", "hombre", "come"]],
        }
    )

    # Tokens list
    ok, ans, exp = evaluate_exercise("translate", payload, answer, ["El", "hombre", "come"])
    assert ok is True

    # String input
    ok, ans, exp = evaluate_exercise("translate", payload, answer, "el hombre come")
    assert ok is True

    # Wrong token sequence
    ok, ans, exp = evaluate_exercise("translate", payload, answer, ["El", "come", "hombre"])
    assert ok is False


def test_exercise_type_match_pairs():
    payload = json.dumps(
        {
            "left": [{"id": "l_1", "text": "hola"}, {"id": "l_2", "text": "adiós"}],
            "right": [{"id": "r_1", "text": "hello"}, {"id": "r_2", "text": "goodbye"}],
        }
    )
    answer = json.dumps({"matches": {"l_1": "r_1", "l_2": "r_2"}})

    # Correct matches dict
    ok, ans, exp = evaluate_exercise("match_pairs", payload, answer, {"l_1": "r_1", "l_2": "r_2"})
    assert ok is True

    # Incomplete / wrong matches
    ok, ans, exp = evaluate_exercise("match_pairs", payload, answer, {"l_1": "r_2", "l_2": "r_1"})
    assert ok is False


def test_hearts_refill_gems_and_practice():
    db = SessionLocal()
    try:
        user = reset_user_1_state(db)
        user.hearts = 1
        user.gems = 500
        db.commit()

        # Practice refill (free)
        res = client.post(
            "/api/hearts/refill", json={"method": "practice"}, headers={"X-User-Id": "1"}
        )
        assert res.status_code == 200
        assert res.json()["hearts"] == 5
        assert res.json()["gems"] == 500

        # Reduce hearts and test gems refill (costs 350)
        user.hearts = 2
        db.commit()
        res2 = client.post(
            "/api/hearts/refill", json={"method": "gems"}, headers={"X-User-Id": "1"}
        )
        assert res2.status_code == 200
        assert res2.json()["hearts"] == 5
        assert res2.json()["gems"] == 150

        # Insufficient gems returns 409
        user.hearts = 2
        db.commit()
        res3 = client.post(
            "/api/hearts/refill", json={"method": "gems"}, headers={"X-User-Id": "1"}
        )
        assert res3.status_code == 409
        assert res3.json()["detail"] == "INSUFFICIENT_GEMS"
    finally:
        db.close()

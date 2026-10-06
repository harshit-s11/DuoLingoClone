from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_me():
    res = client.get("/api/me", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["hearts"] == 5
    assert data["gems"] == 500
    # Explicit check: email field must not exist
    assert "email" not in data


def test_get_course_path():
    res = client.get("/api/courses/1/path")
    assert res.status_code == 200
    data = res.json()
    assert data["course_id"] == 1
    assert len(data["units"]) > 0


def test_start_lesson_attempt():
    res = client.post("/api/lessons/1/start")
    assert res.status_code == 201
    data = res.json()
    assert data["attempt_id"] == 10
    assert data["status"] == "in_progress"
    assert len(data["exercises"]) > 0
    # Crucial security check: answer_json must never be exposed
    for ex in data["exercises"]:
        assert "answer_json" not in ex
        assert "answer" not in ex


def test_complete_attempt_empty_body():
    res = client.post("/api/attempts/10/complete")
    assert res.status_code == 200
    data = res.json()
    assert data["attempt_id"] == 10
    assert data["status"] == "completed"
    assert data["xp_earned"] == 15


def test_refill_hearts_validation():
    # Practice refill is free
    res = client.post("/api/hearts/refill", json={"method": "practice"})
    assert res.status_code == 200
    assert res.json()["hearts"] == 5

    # Gems refill succeeds when balance sufficient
    res = client.post("/api/hearts/refill", json={"method": "gems"})
    assert res.status_code == 200
    assert res.json()["hearts"] == 5


def test_debug_advance_day():
    res = client.post("/api/debug/advance-day", json={"days": 1}, headers={"X-User-Id": "1"})
    assert res.status_code == 200
    assert res.json()["date_offset_days"] == 1


def test_debug_advance_day_unauthorized_user():
    # Only user 1 can access debug endpoints
    res = client.post("/api/debug/advance-day", json={"days": 1}, headers={"X-User-Id": "2"})
    assert res.status_code == 403

# REST API Specification

## 1. Global Conventions & Architecture

- **Base URL**: `/api` (rewritten via Next.js proxy to backend FastAPI service; root health also available at `/health`).
- **Authentication**: Simulated identity via `X-User-Id` request header (default `1`). No passwords or JWT tokens.
- **Content Type**: `application/json` for requests and responses.
- **Date & Time**: ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SSZ`).
- **Logical Clock**: Server evaluates current time as `datetime.now(timezone.utc) + timedelta(days=user.date_offset_days)`.
- **Hearts Regeneration**: 1 heart per 5 hours (18,000s) up to 5 max, lazily computed upon read/check.
- **Critical Heart Rule**: When hearts decrement from 5, `hearts_updated_at` MUST be set to current logical timestamp BEFORE decrementing.

---

## 2. Health & Diagnostic Endpoints

### `GET /health` & `GET /api/health`
Checks server and SQLite connectivity.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-06T14:50:00Z",
  "database": "connected",
  "version": "0.1.0"
}
```

---

## 3. User & Session Endpoints

### `GET /api/me`
Retrieves authenticated user profile, heart balance, gems, streak, and logical time offset.

**Headers**: `X-User-Id: 1`

**Response `200 OK`**:
```json
{
  "id": 1,
  "username": "duo_learner",
  "email": "learner@example.com",
  "hearts": 5,
  "max_hearts": 5,
  "hearts_updated_at": "2026-10-06T12:00:00Z",
  "next_heart_in_seconds": null,
  "xp_total": 125,
  "gems": 500,
  "streak_current": 3,
  "date_offset_days": 0,
  "timezone": "UTC"
}
```

### `GET /api/profile`
Detailed profile with streak history, recent activity, and crown stats.

**Response `200 OK`**:
```json
{
  "user": {
    "id": 1,
    "username": "duo_learner",
    "created_at": "2026-10-01T08:00:00Z",
    "xp_total": 125,
    "streak_current": 3,
    "total_crowns": 4
  },
  "recent_activity": [
    {
      "activity_date": "2026-10-06",
      "xp_earned": 30,
      "lessons_completed": 2
    }
  ],
  "unlocked_achievements_count": 2
}
```

### `GET /api/settings` & `PATCH /api/settings`
Fetch and update user preferences.

**PATCH Request**:
```json
{
  "timezone": "America/New_York"
}
```
**Response `200 OK`**:
```json
{
  "timezone": "America/New_York",
  "date_offset_days": 0
}
```

---

## 4. Course & Learning Path Endpoints

### `GET /api/courses`
Lists available languages.

**Response `200 OK`**:
```json
[
  {
    "id": 1,
    "code": "es",
    "title": "Spanish",
    "description": "Learn conversational Spanish from scratch",
    "flag_emoji": "🇪🇸"
  }
]
```

### `GET /api/courses/{course_id}/path`
Returns the learning tree: units -> skills -> lessons, with completion and crown calculations.

**Response `200 OK`**:
```json
{
  "course_id": 1,
  "title": "Spanish",
  "units": [
    {
      "id": 1,
      "unit_order": 1,
      "title": "Unit 1: Introductions",
      "description": "Greet people, order food, and introduce yourself",
      "skills": [
        {
          "id": 1,
          "skill_order": 1,
          "name": "Basics",
          "description": "Learn fundamental words and greetings",
          "icon_name": "cup",
          "total_crowns": 5,
          "crowns_earned": 2,
          "lessons": [
            {
              "id": 1,
              "lesson_order": 1,
              "title": "Lesson 1",
              "is_completed": true,
              "is_locked": false
            },
            {
              "id": 2,
              "lesson_order": 2,
              "title": "Lesson 2",
              "is_completed": false,
              "is_locked": false
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 5. Lesson & Attempt Engine Endpoints

### `GET /api/lessons/{id}`
Returns lesson metadata and exercises. **Answer data (`answer_json`) is never included in `payload_json`.**

**Response `200 OK`**:
```json
{
  "id": 1,
  "skill_id": 1,
  "title": "Lesson 1",
  "exercises": [
    {
      "id": 101,
      "exercise_order": 1,
      "type": "multiple_choice",
      "payload": {
        "prompt": "Select the correct translation for 'The boy'",
        "options": ["El niño", "La niña", "La manzana", "El agua"]
      }
    }
  ]
}
```

### `POST /api/lessons/{id}/start`
Initiates an authoritative server-side lesson attempt.
- Rejects locked lessons (`403 FORBIDDEN`).
- Rejects if user has 0 hearts (`400 OUT_OF_HEARTS`).
- If an `in_progress` attempt exists for `(user, lesson)`, marks it `abandoned` and starts a fresh one.

**Request**: `{}` (Empty)

**Response `201 CREATED`**:
```json
{
  "attempt_id": 10,
  "lesson_id": 1,
  "status": "in_progress",
  "hearts_remaining": 5,
  "exercises": [
    {
      "id": 101,
      "exercise_order": 1,
      "type": "multiple_choice",
      "payload": {
        "prompt": "Select the correct translation for 'The boy'",
        "options": ["El niño", "La niña", "La manzana", "El agua"]
      }
    }
  ]
}
```

### `POST /api/attempts/{attempt_id}/check`
Authoritatively checks a submitted exercise response and executes heart rules.

**Request**:
```json
{
  "exercise_id": 101,
  "user_answer": "El niño"
}
```

**Response `200 OK` (Correct Answer)**:
```json
{
  "is_correct": true,
  "correct_answer": "El niño",
  "hearts_remaining": 5,
  "attempt_status": "in_progress"
}
```

**Response `200 OK` (Wrong Answer)**:
```json
{
  "is_correct": false,
  "correct_answer": "El niño",
  "hearts_remaining": 4,
  "attempt_status": "in_progress"
}
```
*Note: If hearts reach 0, `attempt_status` changes to `"failed"`.*

### `POST /api/attempts/{attempt_id}/complete`
Authoritatively completes an attempt, calculates accuracy, and awards XP.
- Request body MUST be empty `{}`.
- Rejects incomplete attempts where not every exercise has a correct answer logged in `attempt_answers`.
- XP formula: Base = 10, +5 for 100% accuracy, +2 for >= 80% accuracy.
- Replays award XP but do not grant duplicate crowns.
- Idempotent: Calling again on an already completed attempt returns existing completion data.

**Request**: `{}`

**Response `200 OK`**:
```json
{
  "attempt_id": 10,
  "status": "completed",
  "xp_earned": 15,
  "accuracy": 1.0,
  "hearts_lost": 0,
  "is_replay": false,
  "new_crown_earned": true,
  "streak_current": 4
}
```

### `POST /api/attempts/{attempt_id}/abandon`
Abandons an in-progress attempt.

**Request**: `{}`

**Response `200 OK`**:
```json
{
  "attempt_id": 10,
  "status": "abandoned"
}
```

---

## 6. Gamification & Store Endpoints

### `POST /api/hearts/refill`
Refills user hearts back to 5.
- Method `"gems"`: Costs 350 gems. Returns `409 Conflict` (`INSUFFICIENT_GEMS`) if balance < 350.
- Method `"practice"`: Mocked free path that sets hearts to 5.
- Both methods set `hearts = 5` and reset `hearts_updated_at = logical_now`.

**Request**:
```json
{
  "method": "gems"
}
```

**Response `200 OK`**:
```json
{
  "hearts": 5,
  "gems": 150,
  "hearts_updated_at": "2026-10-06T14:50:00Z"
}
```

**Error `409 Conflict`**:
```json
{
  "detail": "INSUFFICIENT_GEMS"
}
```

### `GET /api/leaderboard`
Returns current week's leaderboard standings.

**Response `200 OK`**:
```json
{
  "week_start_date": "2026-10-05",
  "rankings": [
    {
      "rank": 1,
      "username": "duo_learner",
      "xp_earned": 125,
      "is_current_user": true
    },
    {
      "rank": 2,
      "username": "polyglot_99",
      "xp_earned": 85,
      "is_current_user": false
    }
  ]
}
```

### `GET /api/achievements`
Returns achievements and current user unlocking milestones.

**Response `200 OK`**:
```json
[
  {
    "id": 1,
    "code": "wildfire",
    "title": "Wildfire",
    "description": "Reach a 3-day streak",
    "badge_icon": "flame",
    "target_value": 3,
    "current_value": 3,
    "is_unlocked": true,
    "unlocked_at": "2026-10-06T10:00:00Z"
  }
]
```

---

## 7. Debug Endpoints (`ENABLE_DEBUG=true`, Scoped to User 1)

### `POST /api/debug/advance-day`
Advances logical clock by specified days to test streaks and heart regeneration.

**Request**:
```json
{
  "days": 1
}
```
**Response `200 OK`**:
```json
{
  "date_offset_days": 1,
  "logical_now": "2026-10-07T14:50:00Z"
}
```

### `POST /api/debug/unlock-all`
Unlocks all units and skills for rapid navigation testing.

**Response `200 OK`**:
```json
{
  "message": "All lessons unlocked for user 1"
}
```

### `POST /api/debug/reset-demo`
Resets user 1 hearts to 5, gems to 500, streak to 0, xp to 0, and clears progress.

**Response `200 OK`**:
```json
{
  "message": "Demo data reset successfully"
}
```

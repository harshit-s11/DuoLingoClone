# Database Schema Specification

## 1. Overview & Locked Decisions

- **Engine**: SQLite 3 (local development), running in WAL mode with connection pragma `PRAGMA foreign_keys = ON;` strictly enforced on every connection.
- **Database File**: `./data/duolingo_clone.db` (auto-created on startup inside `./data`).
- **Cascade Policy**: All user-owned foreign keys and child relational hierarchies specify `ON DELETE CASCADE`.
- **Authoritative Server**: Server-side attempt tracking is authoritative. Client-side answer payloads are submitted to backend for validation.
- **Excluded Tables**: `lesson_completions` and `user_skill_progress` **DO NOT exist**. All completion progress is tracked via `user_lesson_progress`, and skill crowns are derived from completed lessons.
- **Excluded Columns**: `skills` does **NOT** contain `crown_count` or `xp_reward`. Crowns are computed on-the-fly from distinct completed lessons in that skill.
- **Security / Data Isolation**: `exercises` segregates presentation (`payload_json`) from verification (`answer_json`). `answer_json` MUST NEVER be exposed in client payloads or public endpoints.

---

## 2. Table Definitions

### 2.1 `users`
Represents learners. Default local learner has `id = 1`.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    is_bot BOOLEAN NOT NULL DEFAULT 0,
    hearts INTEGER NOT NULL DEFAULT 5 CHECK(hearts BETWEEN 0 AND 5),
    hearts_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    xp_total INTEGER NOT NULL DEFAULT 0 CHECK(xp_total >= 0),
    gems INTEGER NOT NULL DEFAULT 500 CHECK(gems >= 0),
    streak_current INTEGER NOT NULL DEFAULT 0 CHECK(streak_current >= 0),
    daily_xp_goal INTEGER NOT NULL DEFAULT 20,
    dark_mode BOOLEAN NOT NULL DEFAULT 0,
    sound_enabled BOOLEAN NOT NULL DEFAULT 1,
    date_offset_days INTEGER NOT NULL DEFAULT 0,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 `courses`
Language courses offered (e.g., Spanish, French, German).

```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(16) NOT NULL UNIQUE,
    title VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    flag_emoji VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 `units`
Top-level structural modules within a course.

```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    unit_order INTEGER NOT NULL,
    slug VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE (course_id, unit_order),
    UNIQUE (course_id, slug)
);
```

### 2.4 `skills`
Thematic nodes along the learning path (e.g., Basics, Food, Greetings).

```sql
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    skill_order INTEGER NOT NULL,
    slug VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    icon_name VARCHAR(64) NOT NULL,
    total_crowns INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES units (id) ON DELETE CASCADE,
    UNIQUE (unit_id, skill_order),
    UNIQUE (unit_id, slug)
);
```
*Note: `crown_count` and `xp_reward` are strictly excluded from this table.*

### 2.5 `lessons`
Individual bite-sized lessons contained within a skill.

```sql
CREATE TABLE lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL,
    lesson_order INTEGER NOT NULL,
    slug VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE,
    UNIQUE (skill_id, lesson_order),
    UNIQUE (skill_id, slug)
);
```

### 2.6 `exercises`
Interactive questions within a lesson.

```sql
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    exercise_order INTEGER NOT NULL,
    slug VARCHAR(64) NOT NULL,
    type VARCHAR(32) NOT NULL CHECK(type IN ('multiple_choice', 'translate', 'match_pairs', 'fill_blank', 'type_answer')),
    payload_json TEXT NOT NULL,  -- Public question prompt, options, distractors
    answer_json TEXT NOT NULL,   -- Private authoritative correct solution (NEVER exposed to frontend)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE,
    UNIQUE (lesson_id, exercise_order),
    UNIQUE (lesson_id, slug)
);
```

### 2.7 `user_lesson_progress`
Tracks the historical completion status of a lesson for a user.

```sql
CREATE TABLE user_lesson_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT 0,
    score INTEGER DEFAULT NULL,
    completed_at TIMESTAMP DEFAULT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE,
    UNIQUE (user_id, lesson_id)
);
```
*Note: Replaces legacy `lesson_completions`. Replays update `completed_at` and score as appropriate.*

### 2.8 `lesson_attempts`
Authoritative server-side session for an active or completed lesson attempt.

```sql
CREATE TABLE lesson_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed', 'abandoned', 'failed')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NULL,
    hearts_lost INTEGER NOT NULL DEFAULT 0,
    xp_earned INTEGER NOT NULL DEFAULT 0,
    accuracy REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
);

-- At most one active in-progress attempt per (user, lesson)
CREATE UNIQUE INDEX idx_unique_in_progress_attempt
ON lesson_attempts (user_id, lesson_id)
WHERE status = 'in_progress';
```

### 2.9 `attempt_answers`
Log of every answered exercise during an attempt, powering authoritative correctness & accuracy calculations.

```sql
CREATE TABLE attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    user_answer_json TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    answered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES lesson_attempts (id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
);
```

### 2.10 `daily_activity`
Aggregated day-level activity used to derive learning streaks and calendar heatmaps.

```sql
CREATE TABLE daily_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_date DATE NOT NULL,  -- YYYY-MM-DD
    xp_earned INTEGER NOT NULL DEFAULT 0,
    lessons_completed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (user_id, activity_date)
);
```

### 2.11 `weekly_xp`
Weekly XP aggregation for leaderboard standings.

```sql
CREATE TABLE weekly_xp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    week_start_date DATE NOT NULL,  -- YYYY-MM-DD (typically Monday)
    xp_earned INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (user_id, week_start_date)
);
```

### 2.12 `achievements`
Static achievement definitions.

```sql
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    badge_icon VARCHAR(64) NOT NULL,
    condition_type VARCHAR(64) NOT NULL,
    threshold INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.13 `user_achievements`
Per-user achievement unlocking status and milestone progress.

```sql
CREATE TABLE user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    current_value INTEGER NOT NULL DEFAULT 0,
    is_unlocked BOOLEAN NOT NULL DEFAULT 0,
    unlocked_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements (id) ON DELETE CASCADE,
    UNIQUE (user_id, achievement_id)
);
```

---

## 3. Indexes & Constraints

1. **Foreign Keys**: `PRAGMA foreign_keys = ON;` executed upon opening SQLite connections.
2. **Partial Unique Index**: `idx_unique_in_progress_attempt` on `lesson_attempts(user_id, lesson_id)` where `status = 'in_progress'`.
3. **Lookup Indexes**:
   - `idx_units_course`: `units(course_id, unit_order)`
   - `idx_skills_unit`: `skills(unit_id, skill_order)`
   - `idx_lessons_skill`: `lessons(skill_id, lesson_order)`
   - `idx_exercises_lesson`: `exercises(lesson_id, exercise_order)`
   - `idx_daily_activity_date`: `daily_activity(user_id, activity_date)`
   - `idx_weekly_xp_user_week`: `weekly_xp(week_start_date, xp_earned DESC)`

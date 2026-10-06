from datetime import datetime, timezone

NOW_ISO = datetime.now(timezone.utc).isoformat()

MOCK_USER = {
    "id": 1,
    "username": "duo_learner",
    "hearts": 5,
    "max_hearts": 5,
    "hearts_updated_at": NOW_ISO,
    "next_heart_in_seconds": None,
    "xp_total": 125,
    "gems": 500,
    "streak_current": 3,
    "date_offset_days": 0,
    "timezone": "UTC",
}

MOCK_COURSES = [
    {
        "id": 1,
        "code": "es",
        "title": "Spanish",
        "description": "Learn conversational Spanish from scratch",
        "flag_emoji": "🇪🇸",
    },
    {
        "id": 2,
        "code": "fr",
        "title": "French",
        "description": "Master fundamental French conversation",
        "flag_emoji": "🇫🇷",
    },
]

MOCK_COURSE_PATH = {
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
                            "title": "Lesson 1: Greetings",
                            "is_completed": True,
                            "is_locked": False,
                        },
                        {
                            "id": 2,
                            "lesson_order": 2,
                            "title": "Lesson 2: Common Phrases",
                            "is_completed": False,
                            "is_locked": False,
                        },
                        {
                            "id": 3,
                            "lesson_order": 3,
                            "title": "Lesson 3: Farewells",
                            "is_completed": False,
                            "is_locked": True,
                        },
                    ],
                },
                {
                    "id": 2,
                    "skill_order": 2,
                    "name": "Food & Drink",
                    "description": "Order coffee, bread, and water",
                    "icon_name": "apple",
                    "total_crowns": 5,
                    "crowns_earned": 0,
                    "lessons": [
                        {
                            "id": 4,
                            "lesson_order": 1,
                            "title": "Lesson 1: Beverages",
                            "is_completed": False,
                            "is_locked": True,
                        }
                    ],
                },
            ],
        }
    ],
}

MOCK_EXERCISES = [
    {
        "id": 101,
        "exercise_order": 1,
        "type": "multiple_choice",
        "payload": {
            "prompt": "Select the correct translation for 'The boy'",
            "options": ["El niño", "La niña", "La manzana", "El agua"],
        },
    },
    {
        "id": 102,
        "exercise_order": 2,
        "type": "translate",
        "payload": {
            "prompt": "Translate: The girl drinks water",
            "word_bank": ["La", "niña", "bebe", "agua", "come", "el"],
        },
    },
    {
        "id": 103,
        "exercise_order": 3,
        "type": "match_pairs",
        "payload": {
            "prompt": "Tap the matching pairs",
            "pairs": [
                {"id": "p1", "left": "boy", "right": "niño"},
                {"id": "p2", "left": "girl", "right": "niña"},
                {"id": "p3", "left": "water", "right": "agua"},
            ],
        },
    },
    {
        "id": 104,
        "exercise_order": 4,
        "type": "fill_blank",
        "payload": {
            "prompt": "Yo ___ pan.",
            "options": ["como", "bebo", "eres"],
        },
    },
    {
        "id": 105,
        "exercise_order": 5,
        "type": "type_answer",
        "payload": {
            "prompt": "Write 'Hello' in Spanish",
            "placeholder": "Type in Spanish...",
        },
    },
]

MOCK_LEADERBOARD = {
    "week_start_date": "2026-10-05",
    "rankings": [
        {"rank": 1, "username": "duo_learner", "xp_earned": 125, "is_current_user": True},
        {"rank": 2, "username": "polyglot_99", "xp_earned": 85, "is_current_user": False},
        {"rank": 3, "username": "linguist_sarah", "xp_earned": 70, "is_current_user": False},
    ],
}

MOCK_ACHIEVEMENTS = [
    {
        "id": 1,
        "code": "wildfire",
        "title": "Wildfire",
        "description": "Reach a 3-day streak",
        "badge_icon": "flame",
        "target_value": 3,
        "current_value": 3,
        "is_unlocked": True,
        "unlocked_at": NOW_ISO,
    },
    {
        "id": 2,
        "code": "champion",
        "title": "Champion",
        "description": "Earn 500 total XP",
        "badge_icon": "trophy",
        "target_value": 500,
        "current_value": 125,
        "is_unlocked": False,
        "unlocked_at": None,
    },
]

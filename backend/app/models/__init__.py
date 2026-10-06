"""Centralized model exports for metadata registration."""

from app.models.course import Course, Exercise, Lesson, Skill, Unit
from app.models.gamification import Achievement, DailyActivity, UserAchievement, WeeklyXP
from app.models.progress import AttemptAnswer, LessonAttempt, UserLessonProgress
from app.models.user import User

__all__ = [
    "User",
    "Course",
    "Unit",
    "Skill",
    "Lesson",
    "Exercise",
    "UserLessonProgress",
    "LessonAttempt",
    "AttemptAnswer",
    "DailyActivity",
    "WeeklyXP",
    "Achievement",
    "UserAchievement",
]

"""User SQLAlchemy model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    is_bot = Column(Boolean, default=False, nullable=False)
    hearts = Column(Integer, default=5, nullable=False)
    hearts_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    xp_total = Column(Integer, default=0, nullable=False)
    gems = Column(Integer, default=500, nullable=False)
    streak_current = Column(Integer, default=0, nullable=False)
    daily_xp_goal = Column(Integer, default=20, nullable=False)
    dark_mode = Column(Boolean, default=False, nullable=False)
    sound_enabled = Column(Boolean, default=True, nullable=False)
    date_offset_days = Column(Integer, default=0, nullable=False)
    timezone = Column(String(64), default="UTC", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("hearts BETWEEN 0 AND 5", name="check_hearts_range"),
        CheckConstraint("xp_total >= 0", name="check_xp_positive"),
    )

    # Relationships
    lesson_progress = relationship(
        "UserLessonProgress",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    attempts = relationship(
        "LessonAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    daily_activities = relationship(
        "DailyActivity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    weekly_xps = relationship(
        "WeeklyXP",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    user_achievements = relationship(
        "UserAchievement",
        back_populates="user",
        cascade="all, delete-orphan",
    )

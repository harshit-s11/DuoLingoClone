"""Course, Unit, Skill, Lesson, and Exercise SQLAlchemy models."""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    flag_emoji = Column(String(16), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    units = relationship(
        "Unit",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Unit.unit_order",
    )


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_order = Column(Integer, nullable=False)
    slug = Column(String(64), nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("course_id", "unit_order", name="uq_units_course_order"),
        UniqueConstraint("course_id", "slug", name="uq_units_course_slug"),
        Index("idx_units_course", "course_id", "unit_order"),
    )

    # Relationships
    course = relationship("Course", back_populates="units")
    skills = relationship(
        "Skill",
        back_populates="unit",
        cascade="all, delete-orphan",
        order_by="Skill.skill_order",
    )


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(
        Integer,
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_order = Column(Integer, nullable=False)
    slug = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    icon_name = Column(String(64), nullable=False)
    total_crowns = Column(Integer, default=5, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Note: crown_count and xp_reward are strictly omitted per locked specification.

    __table_args__ = (
        UniqueConstraint("unit_id", "skill_order", name="uq_skills_unit_order"),
        UniqueConstraint("unit_id", "slug", name="uq_skills_unit_slug"),
        Index("idx_skills_unit", "unit_id", "skill_order"),
    )

    # Relationships
    unit = relationship("Unit", back_populates="skills")
    lessons = relationship(
        "Lesson",
        back_populates="skill",
        cascade="all, delete-orphan",
        order_by="Lesson.lesson_order",
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_order = Column(Integer, nullable=False)
    slug = Column(String(64), nullable=False)
    title = Column(String(128), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("skill_id", "lesson_order", name="uq_lessons_skill_order"),
        UniqueConstraint("skill_id", "slug", name="uq_lessons_skill_slug"),
        Index("idx_lessons_skill", "skill_id", "lesson_order"),
    )

    # Relationships
    skill = relationship("Skill", back_populates="lessons")
    exercises = relationship(
        "Exercise",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Exercise.exercise_order",
    )
    user_progress = relationship(
        "UserLessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    attempts = relationship(
        "LessonAttempt",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_order = Column(Integer, nullable=False)
    slug = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    payload_json = Column(Text, nullable=False)
    answer_json = Column(Text, nullable=False)  # Server-only authoritative answer
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('multiple_choice', 'translate', 'match_pairs', 'fill_blank', 'type_answer')",
            name="check_exercise_type",
        ),
        UniqueConstraint("lesson_id", "exercise_order", name="uq_exercises_lesson_order"),
        UniqueConstraint("lesson_id", "slug", name="uq_exercises_lesson_slug"),
        Index("idx_exercises_lesson", "lesson_id", "exercise_order"),
    )

    # Relationships
    lesson = relationship("Lesson", back_populates="exercises")
    attempt_answers = relationship(
        "AttemptAnswer",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )

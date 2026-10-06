from pydantic import BaseModel, ConfigDict


class CourseItem(BaseModel):
    id: int
    code: str
    title: str
    description: str
    flag_emoji: str

    model_config = ConfigDict(extra="forbid")


class LessonSummary(BaseModel):
    id: int
    lesson_order: int
    title: str
    is_completed: bool
    is_locked: bool

    model_config = ConfigDict(extra="forbid")


class SkillSummary(BaseModel):
    id: int
    skill_order: int
    name: str
    description: str
    icon_name: str
    total_crowns: int
    crowns_earned: int
    lessons: list[LessonSummary]

    model_config = ConfigDict(extra="forbid")


class UnitSummary(BaseModel):
    id: int
    unit_order: int
    title: str
    description: str
    skills: list[SkillSummary]

    model_config = ConfigDict(extra="forbid")


class CoursePathResponse(BaseModel):
    course_id: int
    title: str
    units: list[UnitSummary]

    model_config = ConfigDict(extra="forbid")

from pydantic import BaseModel, ConfigDict


class AdvanceDayRequest(BaseModel):
    days: int = 1

    model_config = ConfigDict(extra="forbid")


class AdvanceDayResponse(BaseModel):
    date_offset_days: int
    logical_now: str

    model_config = ConfigDict(extra="forbid")


class SimpleMessageResponse(BaseModel):
    message: str

    model_config = ConfigDict(extra="forbid")

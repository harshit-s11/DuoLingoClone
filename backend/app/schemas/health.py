from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    version: str

    model_config = ConfigDict(extra="forbid")

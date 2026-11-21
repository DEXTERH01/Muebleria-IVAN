from typing import Literal

from pydantic import BaseModel

from app.core.config import Environment


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: Environment

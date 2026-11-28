"""Contracts for the public Mía assistant endpoint."""

from pydantic import Field

from app.schemas.common import ApiModel


class AssistantChatRequest(ApiModel):
    message: str = Field(min_length=2, max_length=500)


class AssistantChatData(ApiModel):
    message: str
    provider: str
    model: str


class AssistantChatResponse(ApiModel):
    data: AssistantChatData

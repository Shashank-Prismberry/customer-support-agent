from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ChatResponse(BaseModel):
    response: str
    conversation_id: str | None = None


class ErrorResponse(BaseModel):
    code: Literal[
        "UNAUTHORIZED",
        "FORBIDDEN",
        "NOT_FOUND",
        "VALIDATION_ERROR",
        "CONFLICT",
        "SERVICE_UNAVAILABLE",
        "INTERNAL_ERROR",
    ]
    message: str
    details: list[dict[str, str]] = Field(default_factory=list)

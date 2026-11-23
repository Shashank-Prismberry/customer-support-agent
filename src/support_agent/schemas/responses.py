from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ChatResponse(BaseModel):
    response: str
    conversation_id: str | None = None

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RequestIntent(str, Enum):
    TICKET = "ticket"
    KNOWLEDGE = "knowledge"
    BILLING = "billing"
    GENERAL = "general"


class ExecutionMode(str, Enum):
    QUICK = "quick"
    CONTEXT = "context"
    DEEP = "deep"


class RequestAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_mode: ExecutionMode
    intent: RequestIntent
    requires_conversation_history: bool
    requires_rag: bool
    requires_mcp: bool
    requires_approval: bool
    reasoning: str = Field(min_length=1)

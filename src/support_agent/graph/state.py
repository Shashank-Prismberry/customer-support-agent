from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

from support_agent.schemas.context import AuthenticatedUser


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    user_context: AuthenticatedUser
    conversation_context: str
    active_agent: str

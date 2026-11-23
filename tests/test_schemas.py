from pydantic import ValidationError
import pytest

from support_agent.schemas.requests import ChatRequest
from support_agent.schemas.responses import ChatResponse, HealthResponse


def test_chat_request_validates_message_and_optional_conversation():
    request = ChatRequest(message="  Hello  ", conversation_id="conversation-123")

    assert request.message == "Hello"
    assert request.conversation_id == "conversation-123"


def test_chat_request_rejects_empty_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")


def test_chat_request_rejects_oversized_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="x" * 4001)


def test_initial_response_models():
    health = HealthResponse(status="ok")
    chat = ChatResponse(response="How can I help?", conversation_id="conversation-123")

    assert health.status == "ok"
    assert chat.response == "How can I help?"
    assert chat.conversation_id == "conversation-123"

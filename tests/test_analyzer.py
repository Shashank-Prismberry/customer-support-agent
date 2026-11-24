import pytest
from pydantic import ValidationError

from support_agent.analyzer.request_analyzer import (
    ExecutionMode,
    RequestAnalysis,
    RequestIntent,
)


def test_request_analysis_accepts_supported_values():
    analysis = RequestAnalysis(
        execution_mode=ExecutionMode.DEEP,
        intent=RequestIntent.BILLING,
        requires_conversation_history=True,
        requires_rag=True,
        requires_mcp=True,
        requires_approval=True,
        reasoning="The request may require policy review and refund approval.",
    )

    assert analysis.execution_mode == ExecutionMode.DEEP
    assert analysis.intent == RequestIntent.BILLING
    assert analysis.requires_conversation_history is True
    assert analysis.requires_rag is True
    assert analysis.requires_mcp is True
    assert analysis.requires_approval is True


def test_request_analysis_rejects_unknown_intent():
    with pytest.raises(ValidationError):
        RequestAnalysis(
            execution_mode="quick",
            intent="unknown",
            requires_conversation_history=False,
            requires_rag=False,
            requires_mcp=False,
            requires_approval=False,
            reasoning="Unknown request type.",
        )


def test_request_analysis_rejects_unknown_execution_mode():
    with pytest.raises(ValidationError):
        RequestAnalysis(
            execution_mode="instant",
            intent="general",
            requires_conversation_history=False,
            requires_rag=False,
            requires_mcp=False,
            requires_approval=False,
            reasoning="Unsupported execution mode.",
        )


def test_request_analysis_rejects_extra_fields():
    with pytest.raises(ValidationError):
        RequestAnalysis(
            execution_mode="quick",
            intent="general",
            requires_conversation_history=False,
            requires_rag=False,
            requires_mcp=False,
            requires_approval=False,
            reasoning="A general question.",
            organization_id="not-authorized-here",
        )

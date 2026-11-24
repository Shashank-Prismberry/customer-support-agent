from langchain_core.messages import HumanMessage

from support_agent.schemas.context import AuthenticatedUser, UserRole
from support_agent.graph.state import AgentState


def test_agent_state_accepts_initial_request_and_context():
    user = AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        customer_id="10000000-0000-0000-0000-000000000001",
        org_id="20000000-0000-0000-0000-000000000001",
        role=UserRole.END_CUSTOMER,
        email="charlie@example.com",
    )
    state: AgentState = {
        "messages": [HumanMessage(content="What is your refund policy?")],
        "user_context": user,
        "conversation_context": "Previous policy question",
        "active_agent": "knowledge",
    }

    assert state["messages"][0].content == "What is your refund policy?"
    assert state["user_context"].role == UserRole.END_CUSTOMER
    assert state["conversation_context"] == "Previous policy question"
    assert state["active_agent"] == "knowledge"


def test_agent_state_contains_no_raw_token_field():
    state: AgentState = {"messages": []}

    assert "bearer_token" not in state
    assert "raw_token" not in state

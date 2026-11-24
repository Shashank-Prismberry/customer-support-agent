from langchain_core.messages import HumanMessage

from support_agent.schemas.context import AuthenticatedUser, UserRole
from support_agent.graph.state import AgentState
from support_agent.graph.workflow import create_workflow, workflow
from support_agent.graph.nodes import process_request_node


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


def test_minimal_graph_compiles():
    workflow = create_workflow()

    assert workflow is not None


def test_module_exposes_compiled_workflow():
    assert workflow is not None


def test_minimal_graph_accepts_and_returns_state():
    workflow = create_workflow()
    initial_state: AgentState = {
        "messages": [HumanMessage(content="Hello")],
    }

    result = workflow.invoke(initial_state)

    assert result["messages"][-1].content == "Hello"


def test_process_request_node_sets_supervisor_as_active_agent():
    state: AgentState = {
        "messages": [HumanMessage(content="Hello")],
    }

    result = process_request_node(state)

    assert result["active_agent"] == "supervisor"
    assert result["messages"] == state["messages"]


def test_process_request_node_preserves_existing_active_agent():
    state: AgentState = {
        "messages": [HumanMessage(content="Hello")],
        "active_agent": "knowledge",
    }

    result = process_request_node(state)

    assert result["active_agent"] == "knowledge"


def test_workflow_runs_request_node():
    workflow = create_workflow()

    result = workflow.invoke({"messages": [HumanMessage(content="Hello")]})

    assert result["active_agent"] == "supervisor"


def test_module_workflow_executes_with_authenticated_context():
    user = AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        customer_id="10000000-0000-0000-0000-000000000001",
        org_id="20000000-0000-0000-0000-000000000001",
        role=UserRole.ORG_ADMIN,
        email="alice@example.com",
    )

    result = workflow.invoke(
        {
            "messages": [HumanMessage(content="Show my tickets")],
            "user_context": user,
        }
    )

    assert result["active_agent"] == "supervisor"
    assert result["user_context"] == user
    assert result["messages"][-1].content == "Show my tickets"
    assert "bearer_token" not in result


def test_module_workflow_preserves_existing_active_agent():
    result = workflow.invoke(
        {
            "messages": [HumanMessage(content="Continue")],
            "active_agent": "knowledge",
        }
    )

    assert result["active_agent"] == "knowledge"


def test_module_workflow_returns_full_state_after_execution():
    result = workflow.invoke(
        {
            "messages": [HumanMessage(content="Hello")],
            "conversation_context": "Prior support conversation",
        }
    )

    assert set(result) >= {
        "messages",
        "conversation_context",
        "active_agent",
    }
    assert result["conversation_context"] == "Prior support conversation"

from support_agent.graph.state import AgentState


def process_request_node(state: AgentState) -> AgentState:
    if state.get("active_agent"):
        return state

    return {**state, "active_agent": "supervisor"}

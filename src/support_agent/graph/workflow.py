from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from support_agent.graph.nodes import process_request_node
from support_agent.graph.state import AgentState


def create_workflow() -> CompiledStateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("process_request", process_request_node)
    builder.add_edge(START, "process_request")
    builder.add_edge("process_request", END)
    return builder.compile()


workflow = create_workflow()

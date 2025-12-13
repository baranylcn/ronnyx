from typing import Dict

from langchain_core.messages import HumanMessage

from app.core.agent import AgentState, build_graph

graph_app = build_graph()

SESSIONS: Dict[str, AgentState] = {}


def get_state(session_id: str) -> AgentState:
    return SESSIONS.get(session_id, {"messages": []})


def set_state(session_id: str, state: AgentState) -> None:
    SESSIONS[session_id] = state


def apply_user_message(state: AgentState, user_message: str) -> AgentState:
    state["messages"] = list(state["messages"]) + [HumanMessage(content=user_message)]
    return state

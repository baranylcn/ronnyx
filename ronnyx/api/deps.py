from langchain_core.messages import HumanMessage

from ronnyx.core.agent import AgentState


def get_state(session_id: str, sessions: dict) -> AgentState:
    return sessions.get(session_id, {"messages": []})


def set_state(session_id: str, state: AgentState, sessions: dict) -> None:
    sessions[session_id] = state


def apply_user_message(state: AgentState, user_message: str) -> AgentState:
    state["messages"] = list(state["messages"]) + [HumanMessage(content=user_message)]
    return state

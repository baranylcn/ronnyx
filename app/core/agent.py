from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

from app.core.prompts import ASSISTANT_SYSTEM_PROMPT
from app.core.notion_tools import notion_tools
from app.core.github_tools import github_tools

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


tools = notion_tools + github_tools
llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools=tools)


def call_llm(state: AgentState) -> AgentState:
    system_message = SystemMessage(content=ASSISTANT_SYSTEM_PROMPT)
    response = llm.invoke([system_message] + list(state["messages"]))
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    if not messages:
        return "end"
    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    return "continue" if tool_calls else "end"


def build_graph():
    graph = StateGraph(state_schema=AgentState)
    tool_node = ToolNode(tools=tools)

    graph.add_node("agent", call_llm)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")
    return graph.compile()

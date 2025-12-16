from typing import Annotated, Sequence, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

#from app.core.tools.github_tools import github_tools
#from app.core.tools.notion_tools import notion_tools
from app.core.tools.registry import TOOLS
from app.core.prompts import ASSISTANT_SYSTEM_PROMPT

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools=TOOLS)


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
    tool_node = ToolNode(tools=TOOLS)

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

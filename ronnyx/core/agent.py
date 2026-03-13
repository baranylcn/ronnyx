import logging
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from ronnyx.core.prompts import SYSTEM_PROMPT

logger = logging.getLogger("ronnyx")


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def build_graph(tools: list, config):
    tool_map = {t.name: t for t in tools}
    llm = ChatOpenAI(
        model=config.llm_model, temperature=0, api_key=config.llm_api_key
    ).bind_tools(tools)

    context_parts = config.build_context()
    system_prompt = SYSTEM_PROMPT + context_parts if context_parts else SYSTEM_PROMPT

    async def call_llm(state: AgentState) -> AgentState:
        system = SystemMessage(content=system_prompt)
        response = await llm.ainvoke([system] + list(state["messages"]))
        return {"messages": [response]}

    async def execute_tools(state: AgentState) -> AgentState:
        last = state["messages"][-1]
        results = []
        for tc in last.tool_calls:
            tool = tool_map.get(tc["name"])
            if tool is None:
                content = f"Tool '{tc['name']}' not found."
            else:
                try:
                    content = await tool.ainvoke(tc["args"])
                except Exception as e:
                    logger.warning("Tool %s failed: %s", tc["name"], e)
                    content = f"Tool error: {e}"
            results.append(ToolMessage(content=str(content), tool_call_id=tc["id"]))
        return {"messages": results}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        return "continue" if getattr(last, "tool_calls", None) else "end"

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_llm)
    graph.add_node("tools", execute_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")
    return graph.compile()

from fastapi import APIRouter, Request
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from ronnyx.api.deps import apply_user_message, get_state, set_state
from ronnyx.core.agent import AgentState

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@router.get("/tools")
async def list_tools(request: Request):
    return {"tools": request.app.state.tool_names}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    graph = request.app.state.graph
    sessions = request.app.state.sessions

    state: AgentState = get_state(req.session_id, sessions)
    state = apply_user_message(state, req.message)
    new_state = await graph.ainvoke(state)
    set_state(req.session_id, new_state, sessions)

    reply = next(
        m.content
        for m in reversed(new_state["messages"])
        if isinstance(m, AIMessage) and m.content
    )

    return ChatResponse(session_id=req.session_id, reply=reply)

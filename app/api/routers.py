from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import graph_app, get_state, set_state, apply_user_message
from app.core.agent import AgentState


router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    state: AgentState = get_state(req.session_id)
    state = apply_user_message(state, req.message)
    new_state = graph_app.invoke(state)
    set_state(req.session_id, new_state)

    last_message = new_state["messages"][-1]
    return ChatResponse(session_id=req.session_id, reply=last_message.content)

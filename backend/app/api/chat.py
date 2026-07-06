from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from app.agents.cost_agent import chat

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Send a message to the CloudSense AI agent."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    # Validate roles
    for msg in request.messages:
        if msg.role not in ("user", "assistant"):
            raise HTTPException(status_code=400, detail=f"Invalid role: {msg.role}")

    session_id = request.session_id or str(uuid.uuid4())

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        reply = chat(messages=messages, use_live_data=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(reply=reply, session_id=session_id)


@router.get("/starters")
async def conversation_starters():
    """Return suggested questions to help users get started."""
    return {
        "starters": [
            "Why did my AWS costs increase this week?",
            "Which service is costing me the most?",
            "Are there any idle resources wasting money?",
            "What will my bill look like at the end of the month?",
            "Give me a summary of my cloud spend",
            "How can I reduce my EC2 costs?",
        ]
    }

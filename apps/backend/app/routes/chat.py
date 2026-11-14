import json
import logging
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.agent import get_agent
from app.lib.auth import get_current_user
from app.lib.db import SessionLocal, get_session
from app.models import Message, User
from app.routes.project import get_own_project

router = APIRouter(prefix="/projects/{project_id}", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatBody(BaseModel):
    message: str = Field(min_length=1)


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str


@router.get("/messages")
async def list_messages(
    project_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)
) -> list[MessageOut]:
    await get_own_project(project_id, user, db)
    rows = await db.scalars(
        select(Message).where(Message.project_id == project_id).order_by(Message.created_at)
    )
    return [MessageOut(id=m.id, role=m.role, content=m.content) for m in rows]


@router.post("/chat")
async def chat(
    project_id: uuid.UUID,
    body: ChatBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    await get_own_project(project_id, user, db)

    # Past messages = the agent's memory of this conversation
    rows = await db.scalars(
        select(Message).where(Message.project_id == project_id).order_by(Message.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in rows]

    # Save the user's message before the agent starts
    db.add(Message(project_id=project_id, role="user", content=body.message))
    await db.commit()
    history.append({"role": "user", "content": body.message})

    return StreamingResponse(stream_reply(project_id, history), media_type="text/event-stream")


# --- Streaming helpers ---

def sse(data: dict) -> str:
    """One Server-Sent Event: 'data: {...}' followed by a blank line."""
    return f"data: {json.dumps(data)}\n\n"


def text_of(chunk: AIMessageChunk) -> str:
    """Claude sends either a plain string or a list of blocks; keep only the text."""
    if isinstance(chunk.content, str):
        return chunk.content
    return "".join(
        b.get("text", "") for b in chunk.content if isinstance(b, dict) and b.get("type") == "text"
    )


async def stream_reply(project_id: uuid.UUID, history: list[dict]):
    reply = ""
    try:
        async for chunk, _meta in get_agent().astream({"messages": history}, stream_mode="messages"):
            if isinstance(chunk, AIMessageChunk):
                text = text_of(chunk)
                if text:
                    reply += text
                    yield sse({"type": "token", "text": text})
    except Exception:
        logger.exception("Agent failed")
        yield sse({"type": "error", "message": "Agent failed"})

    # The request's DB session may already be closed while streaming, so open a fresh one
    async with SessionLocal() as db:
        db.add(Message(project_id=project_id, role="assistant", content=reply or "(no reply)"))
        await db.commit()

    yield sse({"type": "done"})
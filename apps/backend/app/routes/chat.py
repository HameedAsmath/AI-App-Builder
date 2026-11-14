import json
import logging
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.agent import build_agent
from app.lib.auth import get_current_user
from app.lib.db import SessionLocal, get_session
from app.lib.sandbox import get_sandbox, preview_url
from app.models import Message, Project, User
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
    project = await get_own_project(project_id, user, db)

    rows = await db.scalars(
        select(Message).where(Message.project_id == project_id).order_by(Message.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in rows]

    db.add(Message(project_id=project_id, role="user", content=body.message))
    await db.commit()
    history.append({"role": "user", "content": body.message})

    return StreamingResponse(
        stream_reply(project.id, project.sandbox_id, history), media_type="text/event-stream"
    )


def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def text_of(chunk: AIMessageChunk) -> str:
    if isinstance(chunk.content, str):
        return chunk.content
    return "".join(
        b.get("text", "") for b in chunk.content if isinstance(b, dict) and b.get("type") == "text"
    )


async def stream_reply(project_id: uuid.UUID, sandbox_id: str | None, history: list[dict]):
    reply = ""
    try:
        # 1. Get the project's sandbox (new ones take ~1–2 minutes to set up)
        yield sse({"type": "status", "text": "Starting sandbox…"})
        sandbox = await get_sandbox(sandbox_id)
        url = preview_url(sandbox)

        if sandbox.sandbox_id != sandbox_id:  # new sandbox → remember it
            async with SessionLocal() as db:
                await db.execute(
                    update(Project)
                    .where(Project.id == project_id)
                    .values(sandbox_id=sandbox.sandbox_id, preview_url=url)
                )
                await db.commit()

        yield sse({"type": "preview", "url": url})
        yield sse({"type": "status", "text": "Thinking…"})

        # 2. Run the agent and stream its text and tool activity
        async for chunk, _meta in build_agent(sandbox).astream({"messages": history}, stream_mode="messages"):
            if not isinstance(chunk, AIMessageChunk):
                continue
            for call in chunk.tool_call_chunks:
                if call.get("name"):
                    yield sse({"type": "status", "text": f"Running {call['name']}…"})
            text = text_of(chunk)
            if text:
                reply += text
                yield sse({"type": "token", "text": text})
    except Exception:
        logger.exception("Agent failed")
        yield sse({"type": "error", "message": "Agent failed"})

    async with SessionLocal() as db:
        db.add(Message(project_id=project_id, role="assistant", content=reply or "(no reply)"))
        await db.commit()

    yield sse({"type": "status", "text": ""})
    yield sse({"type": "done"})
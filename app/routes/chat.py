import json
from collections.abc import AsyncGenerator
from typing import Literal

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.embeddings import generate_embedding
from app.limiter import limiter
from app.models import PortfolioKnowledge
from app.prompts import CHAT_PROMPT
from app.schemas import ChatRequest
from app.tools import TOOLS

load_dotenv()

router = APIRouter()

LLM = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(TOOLS)
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

HISTORY_LIMIT = 20


async def search_similar(
    session: AsyncSession, query_embedding: list[float], limit: int = 5
):
    results = await session.execute(
        select(PortfolioKnowledge)
        .order_by(PortfolioKnowledge.embedding.op("<=>")(query_embedding))
        .limit(limit)
    )
    return results.scalars().all()


def build_context(chunks: list[PortfolioKnowledge]) -> str:
    return "\n\n".join(f"[{chunk.category}] {chunk.content}" for chunk in chunks)


def build_history(messages: list) -> list[BaseMessage]:
    history: list[BaseMessage] = []
    for msg in messages[-HISTORY_LIMIT:]:
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            history.append(AIMessage(content=msg.content))
    return history


def _extract_text(content) -> str:
    """Safely extract a plain string from a LangChain message content.

    langchain-google-genai can return content as:
      - a plain str
      - a list of dicts like [{"type": "text", "text": "..."}]
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


async def _call_tool(tool_call: dict) -> ToolMessage:
    name = tool_call["name"]
    tool_impl = TOOLS_BY_NAME.get(name)
    if tool_impl:
        content = await tool_impl.ainvoke(tool_call["args"])
    else:
        content = json.dumps({"error": "unknown function"})
    return ToolMessage(tool_call_id=tool_call["id"], name=name, content=content)


async def run_agent(messages: list[BaseMessage]) -> AsyncGenerator[dict, None]:
    """Run the turn, yielding typed events as they happen.

    Emits {"type": "text", "delta": ...} for answer tokens and
    {"type": "tool", "status": "start"|"end", "name": ...} around each tool
    call. Tool execution is the long silence in a turn — analyze_job_description
    alone is a second full model call — so clients need to know it is happening.

    Both model passes stream token by token. The first pass is accumulated as it
    goes so the tool calls are available once it finishes — Gemini emits either
    text or function calls in a turn, so nothing is streamed twice.
    """
    gathered: AIMessageChunk | None = None

    async for chunk in LLM.astream(messages):
        gathered = chunk if gathered is None else gathered + chunk
        text = _extract_text(chunk.content)
        if text:
            yield {"type": "text", "delta": text}

    if gathered is None or not gathered.tool_calls:
        return

    messages.append(AIMessage(content=gathered.content, tool_calls=gathered.tool_calls))

    for tool_call in gathered.tool_calls:
        yield {"type": "tool", "status": "start", "name": tool_call["name"]}
        messages.append(await _call_tool(tool_call))
        yield {"type": "tool", "status": "end", "name": tool_call["name"]}

    async for chunk in LLM.astream(messages):
        text = _extract_text(chunk.content)
        if text:
            yield {"type": "text", "delta": text}


async def stream_text(messages: list[BaseMessage]):
    """Legacy format: the answer as a bare token stream, tool events dropped."""
    async for event in run_agent(messages):
        if event["type"] == "text":
            yield event["delta"]


async def stream_events(messages: list[BaseMessage]):
    """NDJSON: one JSON object per line, so clients can react to tool events."""
    async for event in run_agent(messages):
        yield json.dumps(event, ensure_ascii=False) + "\n"


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008
    stream: Literal["text", "events"] = "text",
):
    """Answer a question about Nacho.

    `?stream=events` returns NDJSON with tool-progress events; the default
    stays a bare text stream so existing clients keep working unchanged.
    """
    query_embedding = await generate_embedding(body.message)
    chunks = await search_similar(session, query_embedding)

    messages = CHAT_PROMPT.format_messages(
        context=build_context(chunks),
        history=build_history(body.history),
        user_message=body.message,
        locale=body.locale,
    )

    headers = {
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    if stream == "events":
        return StreamingResponse(
            stream_events(messages),
            media_type="application/x-ndjson",
            headers=headers,
        )

    # Plain text, not SSE: the body is a raw token stream with no `data:` frames,
    # so labelling it text/event-stream misleads proxies and clients.
    return StreamingResponse(
        stream_text(messages),
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )

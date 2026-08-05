import json

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


async def _run_tool_calls(tool_calls: list[dict]) -> list[ToolMessage]:
    results = []
    for tool_call in tool_calls:
        name = tool_call["name"]
        tool_impl = TOOLS_BY_NAME.get(name)
        if tool_impl:
            content = await tool_impl.ainvoke(tool_call["args"])
        else:
            content = json.dumps({"error": "unknown function"})
        results.append(
            ToolMessage(tool_call_id=tool_call["id"], name=name, content=content)
        )
    return results


async def stream_agent(messages: list[BaseMessage]):
    """Stream the model's answer, running a tool round-trip if it asks for one.

    Both passes stream token by token. The first pass is accumulated as it goes
    so the tool calls are available once it finishes — Gemini emits either text
    or function calls in a turn, so nothing is streamed twice.
    """
    gathered: AIMessageChunk | None = None

    async for chunk in LLM.astream(messages):
        gathered = chunk if gathered is None else gathered + chunk
        text = _extract_text(chunk.content)
        if text:
            yield text

    if gathered is None or not gathered.tool_calls:
        return

    messages.append(AIMessage(content=gathered.content, tool_calls=gathered.tool_calls))
    messages.extend(await _run_tool_calls(gathered.tool_calls))

    async for chunk in LLM.astream(messages):
        text = _extract_text(chunk.content)
        if text:
            yield text


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
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

    return StreamingResponse(
        stream_agent(messages),
        media_type="text/event-stream",
        headers=headers,
    )

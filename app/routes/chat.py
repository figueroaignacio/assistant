import asyncio
import json

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_groq import ChatGroq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.embeddings import generate_embedding
from app.limiter import limiter
from app.models import PortfolioKnowledge
from app.prompts import CHAT_PROMPT
from app.tools import TOOLS

load_dotenv()

router = APIRouter()


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


async def stream_groq(messages: list[BaseMessage]):
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)

    response = await llm_with_tools.ainvoke(messages)

    if response.tool_calls:
        messages.append(response)

        tools_by_name = {t.name: t for t in TOOLS}

        for tool_call in response.tool_calls:
            func_name = tool_call["name"]
            args = tool_call["args"]

            tool_impl = tools_by_name.get(func_name)
            if tool_impl:
                result_str = await tool_impl.ainvoke(args)
            else:
                result_str = json.dumps({"error": "unknown function"})

            messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=func_name,
                    content=result_str,
                )
            )

        async for chunk in llm_with_tools.astream(messages):
            if chunk.content:
                yield chunk.content
    else:
        if response.content:
            chunk_size = 15
            for i in range(0, len(response.content), chunk_size):
                yield response.content[i : i + chunk_size]
                await asyncio.sleep(0.01)


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(
    request: Request, body: dict, session: AsyncSession = Depends(get_session)
):
    user_message = body.get("message", "")

    query_embedding = await generate_embedding(user_message)
    chunks = await search_similar(session, query_embedding)
    context = build_context(chunks)

    messages = CHAT_PROMPT.format_messages(context=context, user_message=user_message)

    headers = {
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    return StreamingResponse(
        stream_groq(messages),
        media_type="text/event-stream",
        headers=headers,
    )

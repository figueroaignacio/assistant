import asyncio
import json
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.embeddings import generate_embedding
from app.limiter import limiter
from app.models import PortfolioKnowledge
from app.prompts import SYSTEM_PROMPT
from app.routes.portfolio import get_experience, get_projects
from app.tools import TOOLS

load_dotenv()

router = APIRouter()
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


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


async def stream_groq(messages: list[dict]):
    response = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=False,
        tools=TOOLS,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            }
        )

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except Exception:
                args = {}

            locale = args.get("locale", "en")

            if func_name == "get_projects":
                result = await get_projects(locale)
            elif func_name == "get_experience":
                result = await get_experience(locale)
            else:
                result = {"error": "unknown function"}

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": json.dumps(result),
                }
            )

        stream = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            stream=True,
            max_tokens=1024,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    else:
        if message.content:
            chunk_size = 15
            for i in range(0, len(message.content), chunk_size):
                yield message.content[i : i + chunk_size]
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

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + f"Context:\n{context}",
        },
        {"role": "user", "content": user_message},
    ]

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

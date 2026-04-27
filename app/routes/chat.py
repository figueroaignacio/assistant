import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.embeddings import generate_embedding
from app.models import PortfolioKnowledge
from app.prompts import SYSTEM_PROMPT

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


@router.post("/chat")
async def chat(body: dict, session: AsyncSession = Depends(get_session)):
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
        stream_groq(messages), media_type="text/plain", headers=headers
    )

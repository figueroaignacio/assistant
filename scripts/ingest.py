import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import delete

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal, init_db
from app.embeddings import generate_embedding
from app.http import close_client, get_client
from app.models import PortfolioKnowledge

load_dotenv()

PAYLOAD_CMS_URL = os.getenv("PAYLOAD_CMS_URL")
ENDPOINTS = ["projects", "experience", "education"]


def build_content(item: dict, endpoint: str) -> str:
    if endpoint == "experience":
        tasks = " ".join(t["item"] for t in item.get("tasks", []))
        techs = ", ".join(t["name"] for t in item.get("technologies", []))
        return (
            f"{item.get('title', '')} at {item.get('company', '')}. "
            f"Location: {item.get('location', '')}. "
            f"Tasks: {tasks}. "
            f"Technologies: {techs}."
        )
    return item.get("description", "") or item.get("content", "")


async def fetch_collection(endpoint: str) -> list[dict]:
    response = await get_client().get(f"{PAYLOAD_CMS_URL}/{endpoint}")
    response.raise_for_status()
    return response.json()["docs"]


async def ingest():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Ingestion is a full rebuild, not an append. Without this the table
        # grows a duplicate copy of every chunk on each run, which degrades the
        # similarity search. Delete and inserts share one transaction, so a
        # failure mid-run leaves the existing knowledge base untouched.
        deleted = await session.execute(delete(PortfolioKnowledge))
        print(f"Clearing {deleted.rowcount} existing rows...")

        total = 0
        for endpoint in ENDPOINTS:
            print(f"Fetching /{endpoint}...")
            items = await fetch_collection(endpoint)
            print(f"Found {len(items)} items in {endpoint}")

            for item in items:
                content = build_content(item, endpoint)

                if not content.strip():
                    print(f"  Skipping empty item {item.get('id')}")
                    continue

                print(f"  Embedding: {content[:80]}...")
                embedding = await generate_embedding(content)

                session.add(
                    PortfolioKnowledge(
                        content=content, category=endpoint, embedding=embedding
                    )
                )
                total += 1

        await session.commit()
        print(f"Ingestion complete. {total} chunks stored.")


async def main():
    try:
        await ingest()
    finally:
        await close_client()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal, init_db
from app.embeddings import generate_embedding
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


async def fetch_collection(client: httpx.AsyncClient, endpoint: str) -> list[dict]:
    response = await client.get(f"{PAYLOAD_CMS_URL}/{endpoint}")
    response.raise_for_status()
    return response.json()["docs"]


async def ingest():
    await init_db()

    async with httpx.AsyncClient() as client:
        async with AsyncSessionLocal() as session:
            for endpoint in ENDPOINTS:
                print(f"Fetching /{endpoint}...")
                items = await fetch_collection(client, endpoint)
                print(f"Found {len(items)} items in {endpoint}")

                for item in items:
                    content = build_content(item, endpoint)

                    if not content.strip():
                        print(f"  Skipping empty item {item.get('id')}")
                        continue

                    print(f"  Embedding: {content[:80]}...")
                    embedding = await generate_embedding(content)

                    record = PortfolioKnowledge(
                        content=content, category=endpoint, embedding=embedding
                    )
                    session.add(record)

            await session.commit()
            print("Ingestion complete.")


if __name__ == "__main__":
    asyncio.run(ingest())

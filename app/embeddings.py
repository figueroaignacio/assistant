import os

import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"


async def generate_embedding(text: str) -> list[float]:
    import asyncio

    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            try:
                response = await client.post(
                    MODEL_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json={"inputs": text},
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()

                if isinstance(result[0], list):
                    return result[0]
                return result
            except (
                httpx.ReadTimeout,
                httpx.HTTPStatusError,
                httpx.ConnectTimeout,
            ) as e:
                if attempt == 4:
                    raise e
                print(
                    f"Embedding request failed, retrying in {2**attempt} seconds... ({e})"
                )
                await asyncio.sleep(2**attempt)

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"


async def generate_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MODEL_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": text},
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

        if isinstance(result[0], list):
            return result[0]
        return result

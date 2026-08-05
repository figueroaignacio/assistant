import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

MAX_ATTEMPTS = 5

# Only transient failures are worth retrying. 503 in particular is how the HF
# inference API reports "model is still loading". Anything else (401 bad token,
# 400 bad input) will fail identically on every retry, so it is raised at once
# instead of burning ~31s of exponential backoff.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


async def generate_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        for attempt in range(MAX_ATTEMPTS):
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
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in RETRYABLE_STATUS:
                    raise
                last_error: Exception = e
            except httpx.TransportError as e:
                # Covers connect/read timeouts and connection errors.
                last_error = e

            if attempt == MAX_ATTEMPTS - 1:
                raise last_error

            delay = 2**attempt
            print(
                f"Embedding request failed, retrying in {delay} seconds... ({last_error})"
            )
            await asyncio.sleep(delay)

    raise RuntimeError("unreachable")

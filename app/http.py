"""Shared httpx client.

One client for the whole process means connection pooling and keep-alive
across requests instead of a fresh TLS handshake per outbound call. The app
closes it on shutdown via `close_client`; standalone scripts should do the same
before exiting.
"""

import httpx

_client: httpx.AsyncClient | None = None

DEFAULT_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None

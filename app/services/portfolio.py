"""Access layer for the Payload CMS portfolio data.

This module owns everything that talks to Payload: fetching collections,
shaping documents into the payload the API exposes, and pulling plain text out
of Lexical rich-text nodes. Routes and LLM tools both depend on this module —
never on each other.
"""

import os
import re

from dotenv import load_dotenv

from app.http import get_client

load_dotenv()


def _base_url() -> str:
    url = os.getenv("PAYLOAD_CMS_URL")
    if not url:
        raise RuntimeError("PAYLOAD_CMS_URL is not set")
    return url.rstrip("/")


def build_experience_item(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "company": item.get("company"),
        "location": item.get("location"),
        "startDate": item.get("startDate"),
        "endDate": item.get("endDate"),
        "isCurrent": item.get("isCurrent", False),
        "link": item.get("link"),
        "tasks": item.get("tasks", []),
        "technologies": item.get("technologies", []),
    }


def build_project_item(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "subtitle": item.get("subtitle"),
        "description": item.get("description"),
        "slug": item.get("slug"),
        "demo": item.get("demo"),
        "repository": item.get("repository"),
        "technologies": item.get("technologies", []),
    }


async def _fetch_published(collection: str, locale: str) -> list[dict]:
    response = await get_client().get(
        f"{_base_url()}/{collection}",
        params={
            "locale": locale,
            "where[_status][equals]": "published",
            "where[locale][equals]": locale,
        },
    )
    response.raise_for_status()
    return response.json().get("docs", [])


async def fetch_projects(locale: str = "en") -> list[dict]:
    docs = await _fetch_published("projects", locale)
    return [build_project_item(doc) for doc in docs]


async def fetch_experience(locale: str = "en") -> list[dict]:
    docs = await _fetch_published("experience", locale)
    return [build_experience_item(doc) for doc in docs]


def extract_text_from_lexical(node: dict) -> str:
    """Recursively extract plain text from a Payload CMS Lexical rich-text node."""
    if not isinstance(node, dict):
        return ""
    text = node.get("text", "")
    children = node.get("children", [])
    child_text = " ".join(extract_text_from_lexical(child) for child in children)
    return f"{text} {child_text}".strip()


def clean_text(raw: str) -> str:
    """Collapse whitespace and remove excessive blank lines."""
    return re.sub(r"\s+", " ", raw).strip()

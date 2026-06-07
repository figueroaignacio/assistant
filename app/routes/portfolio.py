import os
import re

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PAYLOAD_CMS_URL = os.getenv("PAYLOAD_CMS_URL")


def _extract_text_from_lexical(node: dict) -> str:
    """Recursively extract plain text from a Payload CMS Lexical rich-text node."""
    if not isinstance(node, dict):
        return ""
    text = node.get("text", "")
    children = node.get("children", [])
    child_text = " ".join(_extract_text_from_lexical(child) for child in children)
    combined = f"{text} {child_text}".strip()
    return combined


def _clean_text(raw: str) -> str:
    """Collapse whitespace and remove excessive blank lines."""
    return re.sub(r"\s+", " ", raw).strip()


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


@router.get("/projects")
async def get_projects(locale: str = "en"):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYLOAD_CMS_URL}/projects",
            params={
                "locale": locale,
                "where[_status][equals]": "published",
                "where[locale][equals]": locale,
            },
        )
        response.raise_for_status()
        docs = response.json().get("docs", [])
        return [build_project_item(p) for p in docs]


@router.get("/experience")
async def get_experience(locale: str = "en"):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYLOAD_CMS_URL}/experience",
            params={
                "locale": locale,
                "where[_status][equals]": "published",
                "where[locale][equals]": locale,
            },
        )
        response.raise_for_status()
        docs = response.json().get("docs", [])
        return [build_experience_item(e) for e in docs]


_SUMMARIZE_SYSTEM_PROMPT = """\
You are a concise technical writer. Given the full body of a software project description, \
write a clear, engaging 2-3 sentence summary that captures what the project does, \
the main technology or approach used, and the key outcome or problem it solves. \
Write in the same language as the content (locale hint: {locale}). \
Return only the summary text — no headings, no bullet points, no extra commentary.\
"""


@router.post("/summarize")
async def summarize_project(request: Request):
    """
    Summarize a project's Lexical rich-text body using Gemini Flash.

    Expects JSON body:
        {
            "body": <Payload Lexical root node>,
            "locale": "en" | "es"   (optional, defaults to "en")
        }
    """
    payload = await request.json()
    lexical_body = payload.get("body")
    locale = payload.get("locale", "en")

    if not lexical_body or not isinstance(lexical_body, dict):
        raise HTTPException(
            status_code=422,
            detail="Missing or invalid 'body' field. Expected a Payload Lexical root node.",
        )

    # Payload CMS Lexical format: { root: { children: [...], ... } }
    # Unwrap the outer wrapper so _extract_text_from_lexical sees the actual root node.
    root_node = lexical_body.get("root", lexical_body)

    plain_text = _clean_text(_extract_text_from_lexical(root_node))

    if not plain_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the provided body.",
        )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

    prompt = [
        ("system", _SUMMARIZE_SYSTEM_PROMPT.format(locale=locale)),
        ("human", plain_text),
    ]

    response = await llm.ainvoke(prompt)

    summary = response.content if isinstance(response.content, str) else ""
    return {"summary": summary.strip()}

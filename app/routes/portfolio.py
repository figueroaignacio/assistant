from fastapi import APIRouter, HTTPException, Request
from langchain_google_genai import ChatGoogleGenerativeAI

from app.prompts import SUMMARIZE_SYSTEM_PROMPT
from app.services.portfolio import (
    clean_text,
    extract_text_from_lexical,
    fetch_experience,
    fetch_projects,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/projects")
async def get_projects(locale: str = "en"):
    return await fetch_projects(locale)


@router.get("/experience")
async def get_experience(locale: str = "en"):
    return await fetch_experience(locale)


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
    # Unwrap the outer wrapper so extract_text_from_lexical sees the actual root node.
    root_node = lexical_body.get("root", lexical_body)

    plain_text = clean_text(extract_text_from_lexical(root_node))

    if not plain_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the provided body.",
        )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

    prompt = [
        ("system", SUMMARIZE_SYSTEM_PROMPT.format(locale=locale)),
        ("human", plain_text),
    ]

    response = await llm.ainvoke(prompt)

    summary = response.content if isinstance(response.content, str) else ""
    return {"summary": summary.strip()}

import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv()

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PAYLOAD_CMS_URL = os.getenv("PAYLOAD_CMS_URL")


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

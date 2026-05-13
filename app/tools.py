import json

from langchain_core.tools import tool

from app.routes.portfolio import get_experience, get_projects


@tool("get_projects")
async def get_projects_tool(locale: str = "en") -> str:
    """Fetch a list of my projects, including links, descriptions, and technologies used. Use this to provide information about the projects I've built.

    Args:
        locale: The language locale, e.g., 'en' for English or 'es' for Spanish.
    """
    result = await get_projects(locale)
    return json.dumps(result)


@tool("get_experience")
async def get_experience_tool(locale: str = "en") -> str:
    """Fetch a list of my work experiences, including companies, roles, tasks, and technologies. Use this to provide information about my work history.

    Args:
        locale: The language locale, e.g., 'en' for English or 'es' for Spanish.
    """
    result = await get_experience(locale)
    return json.dumps(result)


TOOLS = [get_projects_tool, get_experience_tool]

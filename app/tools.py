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


@tool("send_contact_email")
async def send_contact_email_tool(name: str, email: str, message: str) -> str:
    """Trigger the sending of a contact email with the name, email, and message body.
    Call this tool when you have collected all three pieces of information from the user
    and they want to send the message.

    Args:
        name: The name of the sender.
        email: The email address of the sender.
        message: The content of the message.
    """
    payload = {"name": name, "email": email, "message": message}
    return f"[SEND_EMAIL_TRIGGER]{json.dumps(payload)}"


TOOLS = [get_projects_tool, get_experience_tool, send_contact_email_tool]

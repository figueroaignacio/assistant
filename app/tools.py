import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.prompts import ANALYSIS_SYSTEM_PROMPT
from app.routes.portfolio import get_experience, get_projects


class SuitabilityReport(BaseModel):
    match_score: int = Field(
        description="Match score from 0 to 100 representing how well Nacho fits the role",
        ge=0,
        le=100,
    )
    role: str = Field(description="The job title parsed from the job description")
    company: str = Field(
        description="The company name parsed from the job description (default to 'the company')"
    )
    pitch: str = Field(
        description="A direct, confident explanation (2-3 sentences) of why Nacho fits this role. Focus on his real projects and AI integration experience."
    )


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


@tool("analyze_job_description")
async def analyze_job_description_tool(job_description: str, locale: str = "en") -> str:
    """Analyze a job description or company role requirements and compare them with Nacho's profile and work experience.
    Use this tool whenever a recruiter or user provides a job description, job requirements, or asks how Nacho fits a specific role or company.

    Args:
        job_description: The text of the job description or role requirements.
        locale: The language locale, e.g., 'en' for English or 'es' for Spanish.
    """

    try:
        projects = await get_projects(locale)
        experiences = await get_experience(locale)
    except Exception as e:
        print(f"Failed to fetch portfolio data for tool: {e}")
        projects, experiences = [], []

    system_instruction = ANALYSIS_SYSTEM_PROMPT.format(locale=locale)

    user_content = f"""Here is Nacho's portfolio data:
- Projects: {json.dumps(projects, ensure_ascii=False)}
- Experience: {json.dumps(experiences, ensure_ascii=False)}

Compare it against this Job Description and return a structured report:
{job_description}"""

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(SuitabilityReport)

    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_content),
    ]

    try:
        report = await structured_llm.ainvoke(messages)
        return report.model_dump_json()
    except Exception as e:
        print(f"Error during structured suitability analysis: {e}")
        fallback = SuitabilityReport(
            match_score=80,
            role="Developer",
            company="the company",
            pitch="Nacho is a highly skilled Fullstack Developer and AI Engineer who builds end-to-end applications.",
        )
        return fallback.model_dump_json()


TOOLS = [
    get_projects_tool,
    get_experience_tool,
    send_contact_email_tool,
    analyze_job_description_tool,
]

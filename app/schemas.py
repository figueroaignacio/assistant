"""Request/response schemas for the public API.

Kept separate from `app.models`, which holds the SQLModel database tables.
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    # `role` is a plain optional string on purpose: the frontend may send roles
    # we don't map to a LangChain message (system, tool, ...). Those are skipped
    # when building history instead of rejecting the whole request.
    role: str = ""
    content: str = Field(default="", max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=50)
    locale: str = Field(default="en", max_length=10)


class SummarizeRequest(BaseModel):
    body: dict = Field(description="Payload CMS Lexical root node")
    locale: str = Field(default="en", max_length=10)

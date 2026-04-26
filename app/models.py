from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Text
from sqlmodel import Column, Field, SQLModel


class PortfolioKnowledge(SQLModel, table=True):
    __tablename__ = "portfolio_knowledge"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(Text, nullable=False))
    category: str = Field(nullable=False)
    embedding: Optional[List[float]] = Field(
        default=None, sa_column=Column(Vector(384))
    )

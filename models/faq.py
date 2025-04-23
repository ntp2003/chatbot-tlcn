from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import VECTOR


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str] = mapped_column(Text(), nullable=False)
    question: Mapped[str] = mapped_column(Text(), nullable=False)
    answer: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreateFAQModel(BaseModel):
    id: int
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]


class UpdateFAQModel(BaseModel):
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]


class FAQModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]
    created_at: datetime
    updated_at: datetime

from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Boolean, Text, DateTime, JSON, Integer, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import Vector
from env import env
from typing import Optional, TYPE_CHECKING
import sqlalchemy as sa


class Comment(Base):
    __tablename__: str = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    product_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    creation_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    creation_time_display: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    full_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_administrator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.text("now()"),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )


class CreateCommentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    product_id: str
    product_type: str
    creation_time: datetime
    creation_time_display: Optional[str] = None
    content: Optional[str] = None
    score: Optional[int] = None
    like_count: int = 0
    full_name: Optional[str] = None
    is_administrator: bool = False
    parent_id: Optional[int] = None
    tags: list[str] = []


class CommentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: str
    product_type: str
    creation_time: datetime
    creation_time_display: Optional[str] = None
    content: Optional[str] = None
    score: Optional[int] = None
    like_count: int = 0
    full_name: Optional[str] = None
    is_administrator: bool = False
    parent_id: Optional[int] = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

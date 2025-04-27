from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa
from uuid import UUID, uuid4


class MessageType(str, Enum):
    user = "user"
    bot = "bot"
    page_admin = "page_admin"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    thread_id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)

    content: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    type: Mapped[MessageType] = mapped_column(sa.Enum(MessageType), nullable=False)
    fb_message_id: Mapped[Optional[str]] = mapped_column(sa.String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=(lambda: datetime.now(tz=timezone.utc))
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=(lambda: datetime.now(tz=timezone.utc)),
        onupdate=(lambda: datetime.now(tz=timezone.utc)),
    )


class MessageModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    content: str
    type: MessageType
    fb_message_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreateMessageModel(BaseModel):
    id: UUID | None = None
    thread_id: UUID
    content: str
    type: MessageType
    fb_message_id: Optional[str] = None


class UpdateMessageModel(BaseModel):
    content: str | None = None

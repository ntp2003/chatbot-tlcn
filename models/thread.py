from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa
from uuid import UUID, uuid4


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=(lambda: datetime.now(tz=timezone.utc))
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=(lambda: datetime.now(tz=timezone.utc)),
        onupdate=(lambda: datetime.now(tz=timezone.utc)),
    )


class ThreadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str | None = None
    is_active: bool

    created_at: datetime
    updated_at: datetime


class CreateThreadModel(BaseModel):
    id: UUID | None = None
    user_id: UUID
    name: str | None = None

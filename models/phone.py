from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from .base import Base


class Phone(Base):
    __tablename__: str = "phones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)

    data: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreatePhoneModel(BaseModel):
    id: str
    data: dict


class PhoneModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    data: dict

    created_at: datetime
    updated_at: datetime

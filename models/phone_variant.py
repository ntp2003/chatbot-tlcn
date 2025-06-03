import uuid
from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import UUID, DateTime, ForeignKey, Text, Integer, ARRAY
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import VECTOR
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from models.phone import Phone, PhoneModel


class Variant(BaseModel):
    propertyName: str
    displayValue: str
    value: Union[str, int, float]
    displayOrder: int
    code: Optional[str] = None


class PhoneVariant(Base):
    __tablename__ = "phone_variants"

    id: Mapped[int] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    phone_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("phones.id", ondelete="CASCADE"),
        nullable=False,
    )
    phone: Mapped["Phone"] = relationship(
        "Phone",
        foreign_keys=[phone_id],
        back_populates="phone_variants",
        lazy="noload",
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    attributes: Mapped[list[dict]] = mapped_column(
        ARRAY(JSONB), nullable=False, default=[]
    )
    slug: Mapped[str] = mapped_column(Text(), nullable=False)
    sku: Mapped[str] = mapped_column(Text(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    variants: Mapped[list[Variant]] = mapped_column(
        ARRAY(JSONB), nullable=False, default=[]
    )
    color_tsv: Mapped[str] = mapped_column(TSVECTOR, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class PhoneVariantModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone_id: str
    data: dict = {}
    attributes: list[dict] = []
    slug: str
    sku: str
    name: str
    variants: list[Variant] = []
    created_at: datetime
    updated_at: datetime


class CreatePhoneVariantModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phone_id: str
    data: dict = {}
    attributes: list[dict] = []
    slug: str
    sku: str
    name: str
    variants: list[Variant] = []

from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
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

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    phone_id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("phones.id", ondelete="CASCADE"),
        nullable=False,
    )
    phone: Mapped["Phone"] = relationship(
        "Phone",
        back_populates="phone_variants",
        lazy="selectin",
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    attributes: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=[])
    slug: Mapped[str] = mapped_column(Text(), nullable=False)
    sku: Mapped[str] = mapped_column(Text(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    variants: Mapped[list[Variant]] = mapped_column(JSONB, nullable=False, default=[])
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

    id: int
    phone_id: int
    phone: "PhoneModel"
    data: dict = {}
    attributes: list[dict] = []
    slug: str
    sku: str
    name: str
    variants: list[Variant] = []
    created_at: datetime
    updated_at: datetime


class CreatePhoneVariantModel(BaseModel):
    phone_id: int
    data: dict = {}
    attributes: list[dict] = []
    slug: str
    sku: str
    name: str
    variants: list[Variant] = []

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

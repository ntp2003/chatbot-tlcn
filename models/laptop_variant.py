from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import DateTime, Text, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TSVECTOR
from pydantic import BaseModel, ConfigDict
from .base import Base
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from models.laptop import Laptop


class Variant(BaseModel):
    propertyName: str
    displayValue: str
    value: Union[str, int, float]
    displayOrder: int
    code: Optional[str] = None


class LaptopVariant(Base):
    __tablename__: str = "laptop_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    laptop_id: Mapped[str] = mapped_column(
        Text, ForeignKey("laptops.id", ondelete="CASCADE"), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    attributes: Mapped[list[dict]] = mapped_column(
        ARRAY(JSONB), nullable=False, default=[]
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    variants: Mapped[list[Variant]] = mapped_column(
        ARRAY(JSONB), nullable=False, default=[]
    )
    color_tsv: Mapped[str] = mapped_column(TSVECTOR, nullable=False)

    laptop: Mapped["Laptop"] = relationship(
        "Laptop",
        foreign_keys=[laptop_id],
        back_populates="laptop_variants",
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreateLaptopVariantModel(BaseModel):
    laptop_id: str
    data: dict = {}
    attributes: list[dict] = []
    slug: str
    sku: str
    name: str
    variants: list[Variant] = []


class LaptopVariantModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    laptop_id: str
    data: dict = {}
    attributes: list[dict] = []
    slug: str
    sku: str
    name: str
    variants: list[Variant] = []
    created_at: datetime
    updated_at: datetime

from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict
from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Float, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID


class UserDemand(str, Enum):
    MOBILE_PHONE = "mobile phone"
    ANOTHER_PRODUCT = "another product"


class PriceRequirement(BaseModel):
    min_price: int | None = None
    max_price: int | None = None

    def __init__(
        self,
        approximate_price: int | None,
        min_price: int | None,
        max_price: int | None,
        diff: int = 500000,
    ):
        BaseModel.__init__(self)
        if approximate_price:
            self.min_price = approximate_price - diff
            self.max_price = approximate_price + diff
        else:
            self.min_price = min_price
            self.max_price = max_price


class UserMemory(Base):
    __tablename__ = "user_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_demand: Mapped[UserDemand | None] = mapped_column(Text, nullable=True)
    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreateUserMemoryModel(BaseModel):
    user_id: uuid.UUID
    thread_id: uuid.UUID


class UserMemoryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    thread_id: uuid.UUID
    user_demand: UserDemand | None
    product_name: str | None
    brand: str | None
    min_price: int | None
    max_price: float | None
    phone_number: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime

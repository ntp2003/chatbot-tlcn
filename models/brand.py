from .base import Base, TimestampMixin, TableNameMixin
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import DateTime, String
from typing import List
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import Vector

#SQLAlchemy model mapping to database
class Brand(Base, TimestampMixin, TableNameMixin):
    #__tablename__ = "brands"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector, nullable=False)
    #parent_id: Mapped[str] = mapped_column(String, nullable=True)
    '''
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    '''
    # Add relationship
    '''
    phones: Mapped[List["Phone"]] = relationship("Phone", back_populates="brand", cascade="all, delete-orphan")
    accessories: Mapped[List["Accessory"]] = relationship("Accessory", back_populates="brand", cascade="all, delete-orphan")
    laptops: Mapped[List["Laptop"]] = relationship("Laptop", back_populates="brand", cascade="all, delete-orphan")
    ''' 
## Pydantic model for creating new entity
class CreateBrandModel(BaseModel):
    id: str
    name: str
    embedding: list[float]
    #parent_id: str

# pydantic model for validate/serialize
class BrandModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    embedding: list[float]
    #parent_id: str
    created_at: datetime
    updated_at: datetime

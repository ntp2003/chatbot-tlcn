from datetime import datetime, timezone
from typing import Optional
from .base import Base
from sqlalchemy import String, UUID, DateTime
import uuid
from sqlalchemy.orm import mapped_column, Mapped
from pydantic import BaseModel, ConfigDict


# Define ORM model cho entity User
class User(Base):
    __tablename__ = "users"  # table name in db

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )  # primary key table users, UUID type, default value is uuid.uuid4
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


# Pydantic model để tạo mới user
class CreateUserModel(BaseModel):
    user_name: str
    password: str


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    password: str

    created_at: datetime
    updated_at: datetime

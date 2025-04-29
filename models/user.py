from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from .base import Base
from sqlalchemy import String, UUID, DateTime,Text
import uuid
from sqlalchemy.orm import mapped_column, Mapped,relationship
from pydantic import BaseModel, ConfigDict
import sqlalchemy as sa


class UserRole(str, Enum):
    admin = "admin"
    chainlit_user = "chainlit_user"
    fb_user = "fb_user"


# Define ORM model cho entity User
class User(Base):
    __tablename__ = "users"  # table name in db

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )  # primary key table users, UUID type, default value is uuid.uuid4
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, name="userrole"),
        nullable=False,
        server_default=UserRole.chainlit_user,
    )
    fb_user_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
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
    password: Optional[str] = None
    role: UserRole = UserRole.chainlit_user
    fb_user_id: Optional[str] = None
    gender: Optional[str] = None


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    password: Optional[str] = None
    role: UserRole
    fb_user_id: Optional[str] = None
    gender: Optional[str] = None

    created_at: datetime
    updated_at: datetime

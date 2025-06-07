from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from .base import Base
from sqlalchemy import Boolean, String, UUID, DateTime
import uuid
from sqlalchemy.orm import mapped_column, Mapped
from pydantic import BaseModel, ConfigDict, EmailStr, Field
import sqlalchemy as sa


class OAuthProvider(str, Enum):
    google = "google"  # Thêm provider cho Google OAuth


class UserRole(str, Enum):
    admin = "admin"
    chainlit_user = "chainlit_user"
    fb_user = "fb_user"
    google_user = "google_user"  # Thêm role cho Google user


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

    # Existing OAuth fields
    fb_user_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Google OAuth fields
    google_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    email_verified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    last_oauth_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    oauth_provider: Mapped[Optional[OAuthProvider]] = mapped_column(
        String(50), nullable=True
    )

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
    google_id: Optional[str] = None
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    oauth_provider: Optional[OAuthProvider] = None
    last_oauth_login: Optional[datetime] = None


# Pydantic model để update user
class UpdateUserModel(BaseModel):
    user_name: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    role: Optional[UserRole] = None
    fb_user_id: Optional[str] = Field(None, max_length=50)
    google_id: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = None
    full_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    oauth_provider: Optional[str] = Field(None, max_length=50)
    last_oauth_login: Optional[datetime] = None


# Pydantic model cho response
class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    password: Optional[str] = None
    role: UserRole

    # OAuth provider IDs
    fb_user_id: Optional[str] = None
    google_id: Optional[str] = None

    # Profile information
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None

    # OAuth tracking
    last_oauth_login: Optional[datetime] = None
    oauth_provider: Optional[OAuthProvider] = None

    created_at: datetime
    updated_at: datetime

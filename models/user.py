from datetime import datetime, timezone
from typing import Optional, List
from .base import Base
from sqlalchemy import String, UUID, DateTime,Text
import uuid
from sqlalchemy.orm import mapped_column, Mapped,relationship
from pydantic import BaseModel, ConfigDict


# Define ORM model cho entity User
class User(Base):
    __tablename__ = "users"  # table name in db

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )  # primary key table users, UUID type, default value is uuid.uuid4
    #user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_name: Mapped[str] = mapped_column(Text, nullable=False)

    #password: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    #fb_id : Mapped[Optional[str]] = mapped_column(Text)
    fb_id : Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True) # them fb_id de tich hop chatbot tren messenger
    
    gender: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")

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
    password: str = None
    fb_id: str = None   

    gender: str = None


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    password: str | None
    fb_id: str | None
    
    gender: str | None

    created_at: datetime
    updated_at: datetime

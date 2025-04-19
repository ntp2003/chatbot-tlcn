from datetime import datetime, timezone
from typing import Optional, List
from .base import Base
from sqlalchemy import String, UUID, DateTime,Text
import uuid
from sqlalchemy.orm import mapped_column, Mapped,relationship
from pydantic import BaseModel, ConfigDict
from models.user_memory import UserMemory
#Define ORM model cho entity User 
class User(Base):
    __tablename__ = "users" #table name in db

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    ) # primary key table users, UUID type, default value is uuid.uuid4
    #user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    #password: Mapped[str] = mapped_column(String(50), nullable=False)
    user_name: Mapped[str] = mapped_column(Text, nullable=False)

    password : Mapped[Optional[str]] = mapped_column(String(50))
    fb_id : Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True) ## them fb_id để tích hợp chatbot trên messenger
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    
    memories : Mapped[List["UserMemory"]] = relationship(
        "UserMemory",
        back_populates="user",
        cascade="all, delete-orphan",
    ) # relationship với bảng user_memory, 1 user có thể có nhiều user_memory, nếu xóa user thì cũng xóa luôn user_memory của nó

'''
INSERT INTO public.users (id,user_name,"password",updated_at,created_at) VALUES
  ('f6f200d4-e309-47fc-8cc2-ffac77cdb8ad'::uuid,'admin','admin','2024-10-13 08:26:12.58468+07','2024-10-13 08:26:12.584536+07');
'''

#Pydantic model để tạo mới user
class CreateUserModel(BaseModel):
    id: Optional[uuid.UUID] = None #không cần cung cấp id khi tạo new user , ORM tự động tạo UUID mới nhờ default = uuid.uuid4
    user_name: str
    password: str = None
    fb_id: str = None


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    password: str | None
    fb_id: str | None

    created_at: datetime
    updated_at: datetime

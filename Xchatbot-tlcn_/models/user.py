from datetime import datetime, timezone
from typing import Optional
from .base import Base
from sqlalchemy import String , UUID, DateTime, Text
import uuid
from sqlalchemy.orm import mapped_column , Mapped
from pydantic import BaseModel , ConfigDict

#define ORM model for entity User
class User(Base):
    __tablename__ = "users" #table name in db

    id: Mapped[
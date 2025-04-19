from .base import Base, TimestampMixin, TableNameMixin
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import VECTOR

# directly interact with the database (SQLAlchemy orm interact with db)
class FAQ(Base, TimestampMixin, TableNameMixin):
    #_tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str] = mapped_column(Text(), nullable=False)
    question: Mapped[str] = mapped_column(Text(), nullable=False)
    answer: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(), nullable=False)
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
# Pydantic model for create new FAQ entity
class CreateFAQModel(BaseModel):
    id: int
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]

# validate n serialize the data
class FAQModel(BaseModel):

    # pydantic map the fields of model to the attribiutes of source object, even if the source object isnt a dictionary (SQLAlchemy ORM instance)
    # Nêú không có config thì FAQModel.model_validate(faq_orm)  # Lỗi vì pydantic không đọc được ORM object
    model_config = ConfigDict(from_attributes=True) ## allow converting sqlalchemy model to pydantic model (allow pydantic model to populate its fields from SQLAlchemy ORM model)

    id: int
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]
    created_at: datetime
    updated_at: datetime

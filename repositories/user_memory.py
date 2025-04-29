from models.user_memory import (
    UpdateUserMemoryModel,
    UserMemory,
    CreateUserMemoryModel,
    UserMemoryModel,
)
from db import Session
from sqlalchemy import select, update as sql_update
import uuid
from uuid import UUID
from database import get_db
from schemas.user_memory import UserMemory


def create(data: CreateUserMemoryModel) -> UserMemoryModel:
    with get_db() as db:
        user_memory = UserMemory(
            user_id=data.user_id,
            thread_id=data.thread_id,
            gender=data.gender,
            intent=data.intent,
            context=data.context
        )
        db.add(user_memory)
        db.commit()
        db.refresh(user_memory)
        return UserMemoryModel.model_validate(user_memory)


def get_by_thread_id(thread_id: UUID) -> UserMemoryModel | None:
    with get_db() as db:
        stmt = select(UserMemory).where(UserMemory.thread_id == thread_id)
        result = db.execute(stmt)
        user_memory = result.scalar_one_or_none()
        if user_memory is None:
            return None
        return UserMemoryModel.model_validate(user_memory)

'''
def get_by_messenger_id(messenger_id: str) -> UserMemoryModel | None:
    """
    Get user memory by Facebook Messenger ID
    """
    with get_db() as db:
        stmt = select(UserMemory).where(UserMemory.messenger_id == messenger_id)
        result = db.execute(stmt)
        user_memory = result.scalar_one_or_none()
        if user_memory is None:
            return None
        return UserMemoryModel.model_validate(user_memory)
'''

def update(id: UUID, data: UpdateUserMemoryModel) -> UserMemoryModel:
    with get_db() as db:
        update_data = data.model_dump(exclude_unset=True)
        stmt = (
            update(UserMemory)
            .where(UserMemory.id == id)
            .values(**update_data)
            .returning(UserMemory)
        )
        result = db.execute(stmt)
        db.commit()
        user_memory = result.scalar_one()
        return UserMemoryModel.model_validate(user_memory)

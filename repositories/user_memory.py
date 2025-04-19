from models.user_memory import UserMemory, CreateUserMemoryModel, UserMemoryModel
from db import Session
from sqlalchemy import select, update
import uuid


def create_user_memory(data: CreateUserMemoryModel) -> UserMemoryModel:
    with Session() as session:
        user_memory = UserMemory(**data.model_dump())

        session.add(user_memory)
        session.commit()

        return UserMemoryModel.model_validate(user_memory)


def get_user_memory_by_thread_id(thread_id: uuid.UUID) -> UserMemoryModel | None:
    with Session() as session:
        user_memory = session.execute(
            select(UserMemory).where(UserMemory.thread_id == thread_id)
        ).scalar_one_or_none()

        return UserMemoryModel.model_validate(user_memory) if user_memory else None


def update_user_memory(user_memory: UserMemoryModel) -> UserMemoryModel:
    with Session() as session:
        session.execute(
            update(UserMemory)
            .where(UserMemory.thread_id == user_memory.thread_id)
            .values(**user_memory.model_dump())
        )
        session.commit()

        return user_memory

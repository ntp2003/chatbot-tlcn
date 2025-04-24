from models.user_memory import (
    UpdateUserMemoryModel,
    UserMemory,
    CreateUserMemoryModel,
    UserMemoryModel,
)
from db import Session
from sqlalchemy import select, update as sql_update
import uuid


def create(data: CreateUserMemoryModel) -> UserMemoryModel:
    with Session() as session:
        user_memory = UserMemory(**data.model_dump())

        session.add(user_memory)
        session.commit()

        return UserMemoryModel.model_validate(user_memory)


def get_by_thread_id(thread_id: uuid.UUID) -> UserMemoryModel | None:
    with Session() as session:
        user_memory = session.execute(
            select(UserMemory).where(UserMemory.thread_id == thread_id)
        ).scalar_one_or_none()

        return UserMemoryModel.model_validate(user_memory) if user_memory else None


def update(id: uuid.UUID, data: UpdateUserMemoryModel) -> UserMemoryModel:
    with Session() as session:
        print(
            "Updating user memory with id:",
            id,
            "and data:",
            data.model_dump(),
        )

        stmt = (
            sql_update(UserMemory)
            .where(UserMemory.id == id)
            .values(**data.model_dump())
            .returning(UserMemory)
        )
        updated_user_memory = session.execute(stmt).scalar_one()
        session.commit()
        return UserMemoryModel.model_validate(updated_user_memory)

from uuid import UUID
from models.thread import (
    CreateThreadModel,
    Thread,
    ThreadModel,
)
from db import Session


def create(data: CreateThreadModel) -> ThreadModel:
    with Session() as session:
        thread = Thread(**data.model_dump())

        session.add(thread)
        session.commit()

        return ThreadModel.model_validate(thread)


def get(id: UUID) -> ThreadModel | None:
    with Session() as session:
        thread = session.get(Thread, id)
        if thread is None:
            return None

        return ThreadModel.model_validate(thread)


def get_all(user_id: UUID) -> list[ThreadModel]:
    with Session() as session:
        threads = (
            session.query(Thread)
            .filter(Thread.user_id == user_id)
            .order_by(Thread.created_at.desc())
            .all()
        )
        return [ThreadModel.model_validate(thread) for thread in threads]


def delete(id: UUID) -> bool:
    with Session() as session:
        thread = session.get(Thread, id)
        if thread is None:
            return False

        session.delete(thread)
        session.commit()

        return True

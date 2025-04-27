from uuid import UUID
from db import Session
from models.message import CreateMessageModel, Message, MessageModel, UpdateMessageModel
from sqlalchemy import select, update as sql_update


def create(data: CreateMessageModel) -> MessageModel:
    with Session() as session:
        message = Message(**data.model_dump())

        session.add(message)
        session.commit()

        return MessageModel.model_validate(message)


def update(id: UUID, data: UpdateMessageModel) -> MessageModel:
    with Session() as session:
        stmt = (
            sql_update(Message)
            .where(Message.id == id)
            .values(**data.model_dump(exclude_unset=True))
            .returning(Message)
        )

        updated_message = session.execute(stmt).scalar_one()
        session.commit()
        return MessageModel.model_validate(updated_message)


def get(id: UUID) -> MessageModel | None:
    with Session() as session:
        message = session.get(Message, id)
        if message is None:
            return None

        return MessageModel.model_validate(message)


def get_by_fb_message_id(fb_message_id: str) -> MessageModel | None:
    with Session() as session:
        stmt = (
            select(Message)
            .select_from(Message)
            .where(Message.fb_message_id == fb_message_id)
        )

        message = session.execute(stmt).scalar()

        if message is None:
            return None

        return MessageModel.model_validate(message)


def get_all(thread_id: UUID, limit: int | None = 10) -> list[MessageModel]:
    with Session() as session:
        messages = (
            session.query(Message)
            .filter(Message.thread_id == thread_id)
            .order_by(Message.created_at.desc())
        )

        if limit is not None:
            messages = messages.limit(limit)
        messages = messages.all()

        messages.reverse()

        return [MessageModel.model_validate(message) for message in messages]


def delete(id: UUID) -> bool:
    with Session() as session:
        message = session.get(Message, id)
        if message is None:
            return False

        session.delete(message)
        session.commit()

        return True

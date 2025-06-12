from uuid import UUID
from db import Session
from typing import Optional, List
from models.user import CreateUserModel, User, UserModel, UserRole, UpdateUserModel
from sqlalchemy import select, case
from models.thread import Thread
from models.message import Message
from models.user_memory import UserMemory


def create(data: CreateUserModel) -> UserModel:
    with Session() as session:
        if data.role == UserRole.chainlit_user and get_by_user_name_and_role(
            data.user_name, data.role
        ):
            raise ValueError("User name already exists")
        if data.role == UserRole.fb_user and get_by_fb_user_id(data.fb_user_id):  # type: ignore
            raise ValueError("Facebook user ID already exists")
        if data.role == UserRole.google_user and get_by_email_and_role(
            data.email, data.role  # type: ignore
        ):
            raise ValueError("Email already exists for Google user")
        user = User(
            **data.model_dump(),
        )
        session.add(user)
        session.commit()

        return UserModel.model_validate(user)


def password_auth_user(
    user_name: str, password: str, role: UserRole
) -> Optional[UserModel]:
    with Session() as session:
        stmt = (
            select(User)
            .select_from(User)
            .where(
                (User.user_name == user_name)
                & (User.password == password)
                & (User.role == role)
            )
        )

        user = session.execute(stmt).scalar()

        if user is None:
            return None
        return UserModel.model_validate(user)


def get(id: UUID) -> Optional[UserModel]:
    with Session() as session:
        user = session.get(User, id)
        if user is None:
            return None

        return UserModel.model_validate(user)


def get_by_fb_user_id(fb_user_id: str) -> Optional[UserModel]:
    with Session() as session:
        stmt = (
            select(User)
            .select_from(User)
            .where((User.fb_user_id == fb_user_id) & (User.role == UserRole.fb_user))
        )

        user = session.execute(stmt).scalar()

        if user is None:
            return None

        return UserModel.model_validate(user)


def get_by_user_name_and_role(user_name: str, role: UserRole) -> Optional[UserModel]:
    with Session() as session:
        stmt = (
            select(User)
            .select_from(User)
            .where((User.user_name == user_name) & (User.role == role))
        )

        user = session.execute(stmt).scalar()

        if user is None:
            return None
        return UserModel.model_validate(user)


def get_by_email_and_role(email: str, role: UserRole) -> Optional[UserModel]:
    with Session() as session:
        stmt = (
            select(User)
            .select_from(User)
            .where((User.email == email) & (User.role == role))
        )

        user = session.execute(stmt).scalar()

        if user is None:
            return None
        return UserModel.model_validate(user)


def update(id: UUID, data: UpdateUserModel) -> int:
    with Session() as session:
        user = session.get(User, id)
        if user is None:
            return 0

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)

        session.add(user)
        session.commit()
        return 1


def delete_by_user_name(user_name: str) -> int:
    with Session() as session:
        users = session.query(User).filter(User.user_name == user_name)
        if not users:
            return 0
        for user in users:
            threads = session.query(Thread).filter(Thread.user_id == user.id).all()
            for thread in threads:
                messages = (
                    session.query(Message).filter(Message.thread_id == thread.id).all()
                )
                for message in messages:
                    session.delete(message)

                memories = (
                    session.query(UserMemory)
                    .filter(UserMemory.thread_id == thread.id)
                    .all()
                )
                for memory in memories:
                    session.delete(memory)

                session.delete(thread)

        delete_count = session.query(User).filter(User.user_name == user_name).delete()
        session.commit()
        return delete_count

from uuid import UUID
from db import Session
from typing import Optional, List
from models.user import CreateUserModel, User, UserModel
from sqlalchemy import select, case


def create_user(data: CreateUserModel) -> UserModel:
    with Session() as session:
        user = User(
            user_name=data.user_name,
            password=data.password,
            fb_id=data.fb_id
        )

        session.add(user)
        session.commit()

        return UserModel.model_validate(user)


def auth_user(user_name: str, password: str) -> Optional[UserModel]:
    with Session() as session:
        stmt = (
            select(User)
            .select_from(User)
            .where((User.user_name == user_name) & (User.password == password))
        )

        user = session.execute(stmt).scalar()

        if user is None:
            return None
        return UserModel.model_validate(user)


def get_user(user_id: UUID) -> Optional[UserModel]:
    with Session() as session:
        user = session.get(User, user_id)
        if user is None:
            return None

        return UserModel.model_validate(user)


def update_user(data: UserModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(User)
            .filter(User.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count

def get_user_by_fb_id(fb_id: str) -> Optional[UserModel]:
    with Session() as session:

        stmt = select(User).where(User.fb_id == fb_id)
        '''
        stmt = (
            select(User)
            .select_from(User)
            .where(User.fb_id == fb_id)
        )
        '''
        #user = session.execute(stmt).scalar()
        user = session.execute(stmt).scalar_one_or_none()
        if user is None:
            return None
        return UserModel.model_validate(user)

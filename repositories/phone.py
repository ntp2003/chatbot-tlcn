from ast import stmt
from db import Session
from typing import Optional, List
from models.phone import CreatePhoneModel, Phone, PhoneModel
from sqlalchemy import Select, select, case
from sqlalchemy.orm import contains_eager
from tools.utils.search import PhoneFilter
from sqlalchemy.sql.elements import ColumnElement
from service.embedding import get_embedding
import numpy as np


def create_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        phone = Phone(**data.model_dump())
        session.add(phone)
        session.commit()

        return PhoneModel.model_validate(phone)


def get_phone(phone_id: str) -> Optional[PhoneModel]:
    with Session() as session:
        phone = session.get(Phone, phone_id)
        if phone is None:
            return None

        return PhoneModel.model_validate(phone)


def update_phone(data: CreatePhoneModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(Phone)
            .filter(Phone.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count


def upsert_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:

        if update_phone(data) == 0:
            return create_phone(data)

        id = data.id

        updated_phone = (
            session.execute(select(Phone).where(Phone.id == id)).unique().scalar_one()
        )
        return PhoneModel.model_validate(updated_phone)


def search_phone_by_filter(
    filter: PhoneFilter,
    order_by: ColumnElement,
    is_desc: bool = True,
    limit: int = 4,
    page: int = 0,
) -> List[PhoneModel]:
    with Session() as session:
        condition = filter.condition_expression()

        stmt = (
            select(Phone).filter(condition) if condition is not None else select(Phone)
        )

        stmt = (
            stmt.order_by(order_by.desc() if is_desc else order_by)
            .limit(limit)
            .offset(page * limit)
        )

        phones = session.execute(stmt).scalars().all()
        return [PhoneModel.model_validate(phone) for phone in phones]


def search_phone_by_phone_name(
    phone_name: str, top_k: int = 4, threshold: Optional[float] = None
) -> List[PhoneModel]:
    with Session() as session:
        embedding = get_embedding(phone_name)
        phones = (
            session.execute(
                select(Phone)
                .order_by(Phone.name_embedding.cosine_distance(embedding))
                .limit(top_k)
                .where(
                    (1 - Phone.name_embedding.cosine_distance(embedding)) < threshold
                )
            )
            .scalars()
            .all()
        )

        return [PhoneModel.model_validate(phone) for phone in phones]


def search(stmt: Select) -> List[PhoneModel]:
    with Session() as session:
        phones = session.execute(stmt).scalars().unique().all()
        return [PhoneModel.model_validate(phone) for phone in phones]


def get_all() -> list[PhoneModel]:
    with Session() as session:
        phones = (
            session.execute(
                select(Phone)
                .join(
                    Phone.phone_variants,
                )
                .options(contains_eager(Phone.phone_variants))
            )
            .scalars()
            .unique()
            .all()
        )
        return [PhoneModel.model_validate(phone) for phone in phones]


def delete_all():
    with Session() as session:
        session.query(Phone).delete()
        session.commit()

from ast import stmt
from db import Session
from typing import Optional, List
from models.phone import CreatePhoneModel, Phone, PhoneModel
from sqlalchemy import Select, select, case
from tools.utils.search import PhoneFilter
from sqlalchemy.sql.elements import ColumnElement
from service.embedding import get_embedding
import numpy as np


# Tạo phone entity
def create_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        phone = Phone(**data.model_dump())
        session.add(phone)
        session.commit()

        # Xác thực phone entity
        return PhoneModel.model_validate(phone)


# Truy xuất phone entity từ database dựa trên id
def get_phone(phone_id: int) -> Optional[PhoneModel]:
    with Session() as session:
        phone = session.get(
            Phone, phone_id
        )  # dùng get của sqlalchemy để truy xuất phone entity từ database
        if phone is None:
            return None

        return PhoneModel.model_validate(phone)


# Cập nhật phone entity trong database
def update_phone(data: CreatePhoneModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)  # loại bỏ id từ thông tin cập nhật
        # Truy vấn lấy ra phone entity dựa trên id và cập nhật thông tin mới (update_info được truyền vào từ CreatePhoneModel)
        update_count = (
            session.query(Phone)
            .filter(Phone.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count  # trả về số lượng phone entity (record) đã được cập nhật


# cập nhật hoặc chèn 1 entity phone mới vào database
def upsert_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        # Không có bản ghi nào được cập nhật => id chưa tồn tại trong db => tạo mới phone entity
        if update_phone(data) == 0:
            return create_phone(data)

        # Nếu có ít nhất 1 bản ghi được cập nhật => id đã tồn tại trong db => cập nhật thông tin phone entity
        id = data.id
        # Truy vấn lấy ra phone entity dã cập nhật từ db dựa trên id
        updated_phone = session.execute(
            select(Phone).where(Phone.id == id)
        ).scalar_one()
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
        phones = session.execute(stmt).scalars().all()
        return [PhoneModel.model_validate(phone) for phone in phones]


def get_all() -> list[PhoneModel]:
    with Session() as session:
        phones = session.execute(select(Phone)).scalars().all()
        return [PhoneModel.model_validate(phone) for phone in phones]

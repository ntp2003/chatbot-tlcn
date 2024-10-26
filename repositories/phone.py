from db import Session
from typing import Optional, List
from models.phone import CreatePhoneModel, Phone, PhoneModel
from sqlalchemy import select, case


def create_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        phone = Phone(
            id=data.id,
            data=data.data,
        )

        session.add(phone)
        session.commit()

        return PhoneModel.model_validate(phone)


def get_phone(phone_id: int) -> Optional[PhoneModel]:
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

        updated_phone = session.execute(
            select(Phone).where(Phone.id == id)
        ).scalar_one()

        return PhoneModel.model_validate(updated_phone)

from uuid import UUID
from db import Session
from typing import Optional, List
from models.phone_variant import (
    CreatePhoneVariantModel,
    PhoneVariant,
    PhoneVariantModel,
)
from sqlalchemy import Select, select, case, update as sql_update


def get(id: UUID) -> Optional[PhoneVariantModel]:
    with Session() as session:
        stmt: Select = select(PhoneVariant).where(PhoneVariant.id == id)
        result = session.execute(stmt).scalar_one_or_none()
        return PhoneVariantModel.model_validate(result) if result else None


def get_by_phone_id(phone_id: str) -> list[PhoneVariantModel]:
    with Session() as session:
        stmt: Select = select(PhoneVariant).where(PhoneVariant.phone_id == phone_id)
        result = session.execute(stmt).scalars().all()
        return [PhoneVariantModel.model_validate(item) for item in result]


def create(phone_variant: CreatePhoneVariantModel) -> PhoneVariantModel:
    with Session() as session:
        new_variant = PhoneVariant(**phone_variant.model_dump())
        session.add(new_variant)
        session.commit()
        session.refresh(new_variant)
        return PhoneVariantModel.model_validate(new_variant)


def delete(id: UUID) -> bool:
    with Session() as session:
        stmt = select(PhoneVariant).where(PhoneVariant.id == id)
        result = session.execute(stmt).scalar_one_or_none()
        if result:
            session.delete(result)
            session.commit()
            return True
        return False


def delete_by_phone_id(phone_id: str) -> bool:
    with Session() as session:
        stmt = select(PhoneVariant).where(PhoneVariant.phone_id == phone_id)
        result = session.execute(stmt).scalars().all()
        if result:
            for item in result:
                session.delete(item)
            session.commit()
            print(f"Deleted {len(result)} phone variants for phone_id: {phone_id}")
            return True
        return False

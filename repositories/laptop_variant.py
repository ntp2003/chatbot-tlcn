from db import Session
from typing import Optional, List
from models.laptop_variant import (
    CreateLaptopVariantModel,
    LaptopVariant,
    LaptopVariantModel,
)
from sqlalchemy import Select, select


def create_laptop_variant(data: CreateLaptopVariantModel) -> LaptopVariantModel:
    with Session() as session:
        laptop_variant = LaptopVariant(**data.model_dump())
        session.add(laptop_variant)
        session.commit()
        return LaptopVariantModel.model_validate(laptop_variant)


def get_laptop_variant(laptop_variant_id: str) -> Optional[LaptopVariantModel]:
    with Session() as session:
        laptop_variant = session.get(LaptopVariant, laptop_variant_id)
        return (
            LaptopVariantModel.model_validate(laptop_variant)
            if laptop_variant
            else None
        )


def update_laptop_variant(data: CreateLaptopVariantModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(LaptopVariant)
            .filter(LaptopVariant.id == data.id)
            .update(update_info)
        )
        session.commit()
        return update_count


def upsert_laptop_variant(data: CreateLaptopVariantModel) -> LaptopVariantModel:
    with Session() as session:
        if update_laptop_variant(data) == 0:
            return create_laptop_variant(data)
        id = data.id
        updated_laptop_variant = session.execute(
            select(LaptopVariant).where(LaptopVariant.id == id)
        ).scalar_one()
        return LaptopVariantModel.model_validate(updated_laptop_variant)


def search(stmt: Select) -> List[LaptopVariantModel]:
    with Session() as session:
        laptop_variants = session.execute(stmt).scalars().all()
        return [
            LaptopVariantModel.model_validate(laptop_variant)
            for laptop_variant in laptop_variants
        ]


def get_laptop_variants_by_laptop_id(laptop_id: str) -> List[LaptopVariantModel]:
    with Session() as session:
        stmt = select(LaptopVariant).where(LaptopVariant.laptop_id == laptop_id)
        laptop_variants = session.execute(stmt).scalars().all()
        return [
            LaptopVariantModel.model_validate(laptop_variant)
            for laptop_variant in laptop_variants
        ]


def delete_laptop_variants_by_laptop_id(laptop_id: str):
    with Session() as session:
        session.query(LaptopVariant).filter(
            LaptopVariant.laptop_id == laptop_id
        ).delete()
        session.commit()


def delete_all():
    with Session() as session:
        session.query(LaptopVariant).delete()
        session.commit()

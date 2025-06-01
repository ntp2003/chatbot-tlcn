from db import Session
from typing import Optional, List
from models.laptop import CreateLaptopModel, Laptop, LaptopModel
from sqlalchemy import Select, select, case, update as sql_update

# from tools.utils.search import LaptopFilter

from sqlalchemy.sql.elements import ColumnElement
from service.embedding import get_embedding
import numpy as np


def create_laptop(data: CreateLaptopModel) -> LaptopModel:
    with Session() as session:
        laptop = Laptop(**data.model_dump())
        session.add(laptop)
        session.commit()
        return LaptopModel.model_validate(laptop)


def get_laptop(laptop_id: str) -> Optional[LaptopModel]:
    with Session() as session:
        laptop = session.get(Laptop, laptop_id)
        return LaptopModel.model_validate(laptop) if laptop else None


def update_laptop(data: CreateLaptopModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(Laptop).filter(Laptop.id == data.id).update(**update_info)
        )
        session.commit()
        return update_count


def upsert_laptop(data: CreateLaptopModel) -> LaptopModel:
    with Session() as session:
        if update_laptop(data) == 0:
            return create_laptop(data)
        id = data.id
        updated_laptop = session.execute(
            select(Laptop).where(Laptop.id == id)
        ).scalar_one()
        return LaptopModel.model_validate(updated_laptop)


def search(stmt: Select) -> List[LaptopModel]:
    with Session() as session:
        laptops = session.execute(stmt).scalars().all()
        return [LaptopModel.model_validate(laptop) for laptop in laptops]


def get_all() -> List[LaptopModel]:
    with Session() as session:
        stmt = select(Laptop)
        laptops = session.execute(stmt).scalars().all()
        return [LaptopModel.model_validate(laptop) for laptop in laptops]

from ast import stmt
from db import Session
from typing import Optional, List
from models.laptop import CreateLaptopModel, Laptop, LaptopModel
from sqlalchemy import Select, select, case, update as sql_update

#from tools.utils.search import LaptopFilter

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
            session.query(Laptop)
            .filter(Laptop.id == data.id)
            .update(update_info)
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
    
'''
def search_laptop_by_filter(
    filter: LaptopFilter,
    order_by: ColumnElement,
    is_desc: bool = True,
    limit: int = 4,
    page: int = 0,
) -> List[LaptopModel]:
    with Session() as session:
        condition = filter.condition_expression()
        stmt = (
            select(Laptop).filter(condition) if condition is not None else select(Laptop)
        )
        stmt = (
            stmt.order_by(order_by.desc() if is_desc else order_by)
            .limit(limit)
            .offset(page * limit)
        )
        laptops = session.execute(stmt).scalars().all()
        return [LaptopModel.model_validate(laptop) for laptop in laptops]

def search_laptop_by_name(
    laptop_name: str,
    top_k: int = 4,
    threshold: Optional[float] = None
) -> List[LaptopModel]:
    with Session() as session:
        embedding = get_embedding(laptop_name)
        laptops = (
            session.execute(
                select(Laptop)
                .order_by(Laptop.name_embedding.cosine_distance(embedding))
                .limit(top_k)
                .where(
                    (1 - Laptop.name_embedding.cosine_distance(embedding)) < threshold
                ) if threshold else None
            )
            .scalars()
            .all()
        )
        return [LaptopModel.model_validate(laptop) for laptop in laptops]
'''


'''
# Tìm laptop Dell từ 15-30 triệu
filter = LaptopFilter(
    brand_code="DELL",
    min_price=15000000,
    max_price=30000000
)

# Tìm theo filter
laptops = search_laptop_by_filter(
    filter=filter,
    order_by=Laptop.price,
    is_desc=True,
    limit=4,
    page=0
)
'''
'''
similar_laptops = search_laptop_by_name(
    laptop_name="Macbook Pro M2",
    top_k=4,
    threshold=0.8
)
'''
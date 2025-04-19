
from db import Session
from typing import Optional, List
from models.accessories import CreateAccessoryModel, Accessory, AccessoryModel
from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement
from tools.utils.search import AccessoryFilter
from service.embedding import get_embedding
import numpy as np
import chainlit as cl


def create_accessory(data: CreateAccessoryModel) -> AccessoryModel:
    with Session() as session:
        accessory = Accessory(
            id=data.id,
            name=data.name,
            slug=data.slug,
            brand_code=data.brand_code,
            product_type=data.product_type,
            description=data.description,
            promotions=data.promotions,
            skus=data.skus,
            key_selling_points=data.key_selling_points,
            price=data.price,
            score=data.score,
            data=data.data,
            name_embedding=data.name_embedding,
        )
        session.add(accessory)
        session.commit()
        return AccessoryModel.model_validate(accessory)


def get_accessory(accessory_id: str) -> Optional[AccessoryModel]:
    with Session() as session:
        accessory = session.get(Accessory, accessory_id)
        if accessory is None:
            return None
        return AccessoryModel.model_validate(accessory)


def update_accessory(data: CreateAccessoryModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(Accessory)
            .filter(Accessory.id == data.id)
            .update(update_info)
        )
        session.commit()
        return update_count


def upsert_accessory(data: CreateAccessoryModel) -> AccessoryModel:
    with Session() as session:
        if update_accessory(data) == 0:
            return create_accessory(data)
        id = data.id
        updated_accessory = session.execute(
            select(Accessory).where(Accessory.id == id)
        ).scalar_one()
        return AccessoryModel.model_validate(updated_accessory)


def search_accessory_by_filter(
    filter: AccessoryFilter,
    order_by: ColumnElement,
    is_desc: bool = True,
    limit: int = 4,
    page: int = 0,
) -> List[AccessoryModel]:
    with Session() as session:
        condition = filter.condition_expression()

        stmt = (
            select(Accessory).filter(condition) if condition is not None else select(Accessory)
        )

        stmt = (
            stmt.order_by(order_by.desc() if is_desc else order_by)
            .limit(limit)
            .offset(page * limit)
        )

        accessories = session.execute(stmt).scalars().all()
        return [AccessoryModel.model_validate(accessory) for accessory in accessories]


def search_accessory_by_name(
    accessory_name: str,
    top_k: int = 4,
    threshold: Optional[float] = None
) -> List[AccessoryModel]:
    with Session() as session:
        embedding = get_embedding(accessory_name)
        accessories = (
            session.execute(
                select(Accessory)
                .order_by(Accessory.name_embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            .scalars()
            .all()
        )

        if threshold:
            results = []
            for accessory in accessories:
                similarity = np.dot(embedding, accessory.name_embedding)
                print(accessory.name, similarity)
                if similarity > threshold:
                    results.append(AccessoryModel.model_validate(accessory))
            return results

        return [AccessoryModel.model_validate(accessory) for accessory in accessories]


'''
Example usage:

# Search for accessories by filter
filter = AccessoryFilter(
    brand_code="APPLE",
    min_price=1000000,
    max_price=5000000
)

accessories = search_accessory_by_filter(
    filter=filter,
    order_by=Accessory.price,
    is_desc=True,
    limit=4,
    page=0
)

# Search for accessories by name
similar_accessories = search_accessory_by_name(
    accessory_name="Apple AirPods Pro",
    top_k=4,
    threshold=0.8
)
'''


from typing import Optional

import numpy as np
from db import Session
from models.brand import CreateBrandModel, Brand, BrandModel
from sqlalchemy import select
from service.embedding import get_embedding
import chainlit as cl


def create_brand(data: CreateBrandModel) -> BrandModel:
    with Session() as session:
        brand = Brand(
            id=data.id,
            name=data.name,
            embedding=data.embedding,
        )

        session.add(brand)
        session.commit()

        return BrandModel.model_validate(brand)


def update_brand(data: CreateBrandModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(Brand)
            .filter(Brand.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count


def upsert_brand(data: CreateBrandModel) -> BrandModel:
    with Session() as session:
        if update_brand(data) == 0:
            return create_brand(data)
        id = data.id

        updated_Brand = session.execute(
            select(Brand).where(Brand.id == id)
        ).scalar_one()

        return BrandModel.model_validate(updated_Brand)


def query_by_semantic(
    brand_name: str, top_k: int = 4, threshold: Optional[float] = None
) -> list[BrandModel]:
    with Session() as session:
        embedding = get_embedding(brand_name)
        brands = (
            session.execute(
                select(Brand)
                .order_by(Brand.embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            .scalars()
            .all()
        )

        if threshold:
            results = []
            for brand in brands:
                c = np.dot(embedding, brand.embedding)
                print(brand.name, c)
                if c > threshold:
                    results.append(BrandModel.model_validate(brand))
            return results

        return [BrandModel.model_validate(brand) for brand in brands]

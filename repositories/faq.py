from typing import Optional
from db import Session
from models.faq import CreateFAQModel, FAQ, FAQModel, UpdateFAQModel
from sqlalchemy import select, update as sql_update
from pgvector.sqlalchemy import Vector


def create(data: CreateFAQModel) -> FAQModel:
    with Session() as session:
        faq = FAQ(**data.model_dump())

        session.add(faq)
        session.commit()

        return FAQModel.model_validate(faq)


def update(id: int, data: UpdateFAQModel) -> FAQModel | None:
    with Session() as session:
        stmt = (
            sql_update(FAQ)
            .where(FAQ.id == id)
            .values(**data.model_dump())
            .returning(FAQ)
        )

        updated_faq = session.execute(stmt).scalar_one_or_none()
        session.commit()
        return FAQModel.model_validate(updated_faq) if updated_faq else None


def upsert(data: CreateFAQModel) -> FAQModel:
    with Session() as session:
        updated_faq = update(
            data.id,
            UpdateFAQModel.model_validate(data.model_dump(exclude={"id"})),
        )

        if updated_faq:
            return updated_faq

        return create(data)


def search_by_semantic(
    question_embedding: list[float], top_k: int = 4, threshold: Optional[float] = None
) -> list[FAQModel]:
    with Session() as session:
        stmt = (
            select(FAQ)
            .order_by(
                FAQ.embedding.cast(Vector).cosine_distance(question_embedding).asc()
            )
            .limit(top_k)
        )
        if threshold:
            stmt = stmt.where(
                FAQ.embedding.cast(Vector).cosine_distance(question_embedding)
                < 1 - threshold
            )

        faqs = session.execute(stmt).scalars().all()

        return [FAQModel.model_validate(faq) for faq in faqs]


def get_all() -> list[FAQModel]:
    with Session() as session:
        stmt = select(FAQ)
        faqs = session.execute(stmt).scalars().all()

        return [FAQModel.model_validate(faq) for faq in faqs]

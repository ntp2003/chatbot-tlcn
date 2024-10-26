from typing import Optional

import numpy as np
from db import Session
from models.faq import CreateFAQModel, FAQ, FAQModel
from sqlalchemy import select
from service.embedding import get_embedding


def create_faq(data: CreateFAQModel) -> FAQModel:
    with Session() as session:
        faq = FAQ(
            id=data.id,
            title=data.title,
            category=data.category,
            question=data.question,
            answer=data.answer,
            embedding=data.embedding,
        )

        session.add(faq)
        session.commit()

        return FAQModel.model_validate(faq)


def update_faq(data: CreateFAQModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(FAQ)
            .filter(FAQ.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count


def upsert_faq(data: CreateFAQModel) -> FAQModel:
    with Session() as session:
        if update_faq(data) == 0:
            return create_faq(data)
        id = data.id

        updated_faq = session.execute(select(FAQ).where(FAQ.id == id)).scalar_one()

        return FAQModel.model_validate(updated_faq)


def query_by_semantic(
    question: str, top_k: int = 4, threshold: Optional[float] = None
) -> list[FAQModel]:
    with Session() as session:
        embedding = get_embedding(question)
        faqs = (
            session.execute(
                select(FAQ).order_by(FAQ.embedding.op("<=>")(embedding)).limit(top_k)
            )
            .scalars()
            .all()
        )

        if threshold:
            results = []
            for faq in faqs:
                c = np.dot(embedding, faq.embedding)
                print(faq.question, c)
                if c > threshold:
                    results.append(FAQModel.model_validate(faq))
            return results

        return [FAQModel.model_validate(faq) for faq in faqs]

from repositories.faq import search_by_semantic, search_by_semantic_with_id
from models.faq import FAQModel
from service.embedding import get_embedding


def search(
    question: str,
    top_k: int = 4,
    threshold: float = 0.55,
) -> list[FAQModel]:
    question_embedding = get_embedding(question)

    faqs = search_by_semantic(
        question_embedding=question_embedding, top_k=top_k, threshold=threshold
    )

    return faqs

def search_with_id(
    question: str,
    top_k: int = 4,
    threshold: float = 0.4,
) -> tuple[list[FAQModel], list[int]]:
    question_embedding = get_embedding(question)

    faqs, ids = search_by_semantic_with_id(
        question_embedding=question_embedding, top_k=top_k, threshold=threshold
    )

    return faqs, ids

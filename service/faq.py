from repositories.faq import search_by_semantic
from models.faq import FAQModel
from service.embedding import get_embedding


def search(
    question: str,
    top_k: int = 4,
    threshold: float = 0.4,
) -> list[FAQModel]:
    question_embedding = get_embedding(question)

    faqs = search_by_semantic(
        question_embedding=question_embedding, top_k=top_k, threshold=threshold
    )

    for faq in faqs:
        print(f"FAQ: {faq.question}")

    return faqs

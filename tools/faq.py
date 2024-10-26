from models.faq import FAQModel
from repositories.faq import query_by_semantic
from openai.types.chat import ChatCompletionToolParam


tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "search_faqs_tool",
        "description": (
            "Search for information regarding answers to frequently asked questions (FAQ) about the store's policies available in the database, "
            "including privacy policy, return and refund policy, warranty policy, and shipping policy.\n"
            "Return:\n"
            "- The related set of questions and answers\n"
            "- Instructions on how to give response to the user based on the information provided"
        ),
        "parameters": {
            "type": "object",
            "required": ["question"],
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user's general question about TripHunter and its services",
                }
            },
        },
    },
}


def _to_text(faq: FAQModel) -> str:
    return (
        f"- Title: {faq.title}\n"
        f"  - Câu hỏi: {faq.question}\n"
        f"  - Câu trả lời: {faq.answer}\n"
    )


def invoke(question: str) -> str:
    print(f"Câu hỏi: {question}")
    faqs = query_by_semantic(question, threshold=0.3)
    faq_texts = [_to_text(faq) for faq in faqs]
    if faq_texts:
        return (
            "\n".join(faq_texts)
            + "## The above contains information about frequently asked questions and corresponding answers. "
            "Based on this information, please filter and provide responses to the user.\n"
            "## NOTE: If this information cannot answer the user's question, please respond that you do not know."
        )
    return "you have to tell the user that you don't know the answer."

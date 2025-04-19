from models.faq import FAQModel
from repositories.faq import query_by_semantic
from openai.types.chat import ChatCompletionToolParam

# "Search the faq database for information regarding answers to frequently asked questions (FAQ) about the store's policies available in the database, "
#             "including privacy policy, return and refund policy, warranty policy, and shipping policy.\n"
tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "search_faq_database_tool",
        "description": """
# ROLE
Search the FAQ database.

## RULES
- Frequently asked questions (FAQs) are the questions that are commonly asked by users about the store's policies, including privacy policy, return and refund policy, warranty policy, and shipping policy.

## RETURNS
- The related set of questions and answers.
- Instructions on how to give response to the user based on the information provided.
""",
        "parameters": {
            "type": "object",
            "required": ["faq_question"],
            "properties": {
                "faq_question": {
                    "type": "string",
                    "description": "The frequently asked question (FAQ) about the store's policies that the user is asking for.",
                }
            },
        },
    },
}

# format FAQModel thành structured string theo template
def _to_text(faq: FAQModel) -> str:
    return (
        f"- Title: {faq.title}\n"
        f"  - Câu hỏi: {faq.question}\n"
        f"  - Câu trả lời: {faq.answer}\n"
    )


def invoke(question: str) -> str:
    print(f"Câu hỏi: {question}")
    #semantic search with threshold 0.3
    faqs = query_by_semantic(question, threshold=0.3)

    #convert các faqs tìm được thành structured string theo template
    faq_texts = [_to_text(faq) for faq in faqs]
    if faq_texts: # nếu có faqs tìm được
        return (
            "\n".join(faq_texts)
            + "## The above contains information about frequently asked questions and corresponding answers. " # add instruction
            "Based on this information, please filter and provide responses to the user.\n"
            "## NOTE: If this information cannot answer the user's question, please respond that you do not know." # thêm lưu ý
        )
    # Nếu không tìm thấy faqs phù hợp, trả về lời khuyên để hỏi lại
    return "you have to tell the user that you don't know the answer."

'''
# 1. User hỏi về chính sách đổi trả
question = "Làm thế nào để đổi trả sản phẩm?"

# 2. Invoke FAQ tool
result = invoke(question)

# 3. Kết quả có thể như sau:
"""
- Title: Chính sách đổi trả
  - Câu hỏi: Làm thế nào để đổi trả sản phẩm?
  - Câu trả lời: Bạn có thể đổi trả sản phẩm trong vòng 7 ngày...

## The above contains information about frequently asked questions...
## NOTE: If this information cannot answer...
"""
'''
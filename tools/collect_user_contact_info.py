from openai.types.chat import ChatCompletionToolParam
from service.converter import (
    convert_to_standard_email,
    convert_to_standard_phone_number,
)
from models.user_memory import UpdateUserMemoryModel, UserMemoryModel
from repositories.user_memory import update as update_user_memory
from rq import Queue
from db import redis
from service.email import send_message, create_message
from env import env

tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "collect_user_contact_info_tool",
        "description": """
# ROLE
Collect user's contact information such as phone number, email.

## RULES
- You need to collect the user's contact information when the user provides it.

## RETURNS
- Ask the user again if the user provides the invalid contact information.
- Thank the user for providing the contact information.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "The phone number that the user provides.",
                },
                "email": {
                    "type": "string",
                    "description": "The user's email that the user provides.",
                },
            },
        },
    },
}


def invoke(
    user_memory: UserMemoryModel, phone_number: str | None, email: str | None
) -> str:
    invalid_infos = []
    standard_phone_number = convert_to_standard_phone_number(phone_number)
    standard_email = convert_to_standard_email(email)

    if phone_number and not standard_phone_number:
        invalid_infos.append("phone number")
    else:
        user_memory.phone_number = standard_phone_number or user_memory.phone_number

    if email and not standard_email:
        invalid_infos.append("email")
    else:
        user_memory.email = standard_email or user_memory.email

    update_user_memory(
        user_memory.id, UpdateUserMemoryModel(**user_memory.model_dump())
    )
    phone_number_is_missing = not user_memory.phone_number

    if len(invalid_infos) > 0:
        return f"The information about the {'' and ''.join(invalid_infos)} provided by the user might be invalid. You should politely ask them to provide this information again."

    if phone_number_is_missing:
        return "You must ask the user for their phone number to consult or purchase the product better."

    _send_email_cs(user_memory)
    return (
        "## Next, you should naturally thank the user for providing their contact information. The consulting and sales department will get in touch with them as soon as possible.\n"
        "For example: 'Cảm ơn bạn đã cung cấp thông tin liên hệ. Bộ phận tư vấn và bán hàng sẽ liên hệ với bạn sớm nhất có thể. Trong thời gian chờ đợi bạn có thể xem các sản phẩm khác hoặc liên hệ {hotline} để được hỗ trợ nhanh nhất.'"
    )


def _send_email_cs(user_memory: UserMemoryModel):
    email = create_message(
        sender=env.SENDER_EMAIL,
        to=env.RECEIVER_EMAIL,
        subject=f"{user_memory.phone_number} - Người dùng cần hỗ trợ",
        message_text=(
            "Người dùng cần hỗ trợ với.\n"
            f"Số điện thoại: {user_memory.phone_number}\n"
            f"Email: {user_memory.email}\n"
            f"Reference: {env.CHAINLIT_HOST}:{env.CHAINLIT_PORT}/thread/{user_memory.thread_id}\n"
        ),
    )
    queue = Queue(connection=redis)
    queue.enqueue(send_message, email)

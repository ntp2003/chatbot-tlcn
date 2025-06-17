import datetime
from uuid import UUID
import uuid
import chainlit as cl
from models.message import MessageModel
from service.store_chatbot_v2 import gen_answer
from repositories.thread import (
    get as get_thread,
    create as create_thread,
    CreateThreadModel,
)
from repositories.message import create as create_message, CreateMessageModel
from models.message import MessageType
from chainlit.types import ThreadDict


@cl.on_message
async def main(message: cl.Message):
    if not cl.context.session.user:
        raise ValueError("User is not logged in")

    user_id = UUID(cl.context.session.user.metadata["user_id"])
    thread_id = UUID(cl.context.session.thread_id)

    conversation = cl.chat_context.to_openai()
    message.author = "user_message"
    print("User ID:", user_id)
    print("Thread ID:", thread_id)

    thread = get_thread(thread_id)
    if not thread:
        thread = create_thread(
            CreateThreadModel(
                id=thread_id,
                user_id=user_id,
                name=f"THREAD_{thread_id}",
            )
        )

    # Create a new message
    message_data = CreateMessageModel(
        id=UUID(message.id),
        thread_id=thread.id,
        type=MessageType.user,
        content=message.content,
    )

    new_message = create_message(message_data)

    try:
        response_text = gen_answer(user_id, thread_id, conversation)

    except Exception as e:
        print("Error:", e)
        response_text = str(e)

    # Create a new message for the assistant
    new_assistant_message_data = CreateMessageModel(
        thread_id=thread.id,
        type=MessageType.bot,
        content=response_text,
    )
    new_assistant_message = create_message(new_assistant_message_data)
    return await cl.Message(
        content=response_text,
        author="assistant_message",
        metadata={"user_id": str(user_id)},
        parent_id=message.id,
        id=str(new_assistant_message.id),
        created_at=new_assistant_message.created_at.isoformat(),
    ).send()


@cl.set_starters
async def set_starters(user):
    return [
        cl.Starter(
            label="Tư vấn điện thoại",
            message="Mình cần tư vấn điện thoại",
            icon='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-smartphone-icon lucide-smartphone"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>',
        ),
        cl.Starter(
            label="Tư vấn laptop",
            message="Mình cần tư vấn laptop",
            icon='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-laptop-icon lucide-laptop"><path d="M18 5a2 2 0 0 1 2 2v8.526a2 2 0 0 0 .212.897l1.068 2.127a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45l1.068-2.127A2 2 0 0 0 4 15.526V7a2 2 0 0 1 2-2z"/><path d="M20.054 15.987H3.946"/></svg>',
        ),
        cl.Starter(
            label="Chính sách giao hàng",
            message="Chính sách giao hàng của FPT Shop là gì?",
            icon='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-truck-icon lucide-truck"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/></svg>',
        ),
        cl.Starter(
            label="Chính sách bảo hành",
            message="Chính sách bảo hành của FPT Shop là gì?",
            icon='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-check-icon lucide-shield-check"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>',
        ),
    ]


async def on_chat_resume(thread: ThreadDict):
    print("Chat resumed")
    print("Thread ID:", thread["id"])
    for i, step in enumerate(thread["steps"]):
        print(f"Step {i}:", step)

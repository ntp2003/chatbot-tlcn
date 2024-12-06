from uuid import UUID
import chainlit as cl
from models.message import Message
from service.store_chatbot import gen_answer_with_chainlit


@cl.on_message
async def main(message: cl.Message):
    conversation = cl.chat_context.get()
    message.author = "user"
    user_id = UUID(cl.context.session.user.metadata["user_id"])  # type: ignore
    thread_id = UUID(cl.context.session.thread_id)
    conversation = [
        Message(content=msg.content, author=msg.author) for msg in conversation
    ]
    print("User ID:", user_id)
    print("Thread ID:", thread_id)
    return await gen_answer_with_chainlit(user_id, thread_id, conversation).send()


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    pass

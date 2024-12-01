from uuid import UUID
import chainlit as cl
from service.store_chatbot import gen_answer


@cl.on_message
async def main(message: cl.Message):
    conversation = cl.chat_context.get()
    message.author = "user"
    user_id = UUID(cl.context.session.user.metadata["user_id"])  # type: ignore
    thread_id = UUID(cl.context.session.thread_id)
    print("User ID:", user_id)
    print("Thread ID:", thread_id)
    await gen_answer(user_id, thread_id, conversation).send()


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    pass

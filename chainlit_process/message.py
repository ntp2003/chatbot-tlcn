from uuid import UUID
import chainlit as cl
from service.store_chatbot import gen_answer


@cl.on_message
async def main(message: cl.Message):
    conversation = cl.chat_context.get()
    message.author = "user"
    user_id = UUID(cl.context.session.user.metadata["user_id"])  # type: ignore
    await gen_answer(user_id, conversation).send()


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    pass

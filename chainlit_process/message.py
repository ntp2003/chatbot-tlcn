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

# handle user message
@cl.on_message
async def main(message: cl.Message):
    if not cl.context.session.user: # check if user is logged in
        raise ValueError("User is not logged in")

    user_id = UUID(cl.context.session.user.metadata["user_id"]) # get user id from session
    thread_id = UUID(cl.context.session.thread_id) # get thread id from session

    conversation = cl.chat_context.to_openai() # get conversation from chat context and convert to openai format
    message.author = "user_message"
    print("User ID:", user_id)
    print("Thread ID:", thread_id)

    thread = get_thread(thread_id) # get thread from database by thread id
    if not thread: # if thread does not exist, create a new thread in db
        thread = create_thread(
            CreateThreadModel(
                id=thread_id,
                user_id=user_id,
                name=f"THREAD_{thread_id}",
            )
        )

    # Create new user message
    message_data = CreateMessageModel(
        id=UUID(message.id),
        thread_id=thread.id,
        type=MessageType.user,
        content=message.content,
    )

    new_message = create_message(message_data) # create new user message in db

    try:
        response_text = gen_answer(user_id, thread_id, conversation) # generate answer from assistant

    except Exception as e:
        print("Error:", e)
        response_text = str(e)

    # Create new assistant message with response text
    new_assistant_message_data = CreateMessageModel(
        thread_id=thread.id,
        type=MessageType.bot,
        content=response_text,
    )
    
    new_assistant_message = create_message(new_assistant_message_data) # create new assistant message in db
    return await cl.Message(
        content=response_text,
        author="assistant_message",
        metadata={"user_id": str(user_id)},
        parent_id=message.id,
        id=str(new_assistant_message.id),
        created_at=new_assistant_message.created_at.isoformat(),
    ).send() # send new assistant message to user in chainlit UI

# handle khôi phục chat
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("Chat resumed")
    print("Thread ID:", thread["id"])
    for i, step in enumerate(thread["steps"]):
        print(f"Step {i}:", step)

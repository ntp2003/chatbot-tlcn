from typing import Optional
import fbmessenger as fb
from env import env
from repositories.message import (
    create as create_message,
    get_by_fb_message_id as get_message_by_fb_message_id,
    get_all as get_all_messages,
)
from models.message import CreateMessageModel, MessageModel, MessageType
from repositories.thread import (
    create as create_thread,
    get_all_by_user_id as get_all_threads,
)
from repositories.user import (
    get_by_fb_user_id as get_user_by_fb_user_id,
    create as create_user,
)
from models.user import UserModel, CreateUserModel, UserRole
from models.thread import ThreadModel, CreateThreadModel
from service.store_chatbot_v2 import gen_answer

fb.DEFAULT_API_VERSION = env.FB_API_VERSION

from pydantic import BaseModel, HttpUrl
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam,
)


class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_pic: Optional[HttpUrl] = None
    locale: Optional[str] = None
    timezone: Optional[int] = None
    gender: Optional[str] = None
    id: str


class Messenger(fb.BaseMessenger):
    def __init__(self):
        super().__init__(page_access_token=env.FB_PAGE_ACCESS_TOKEN)

    def message(self, message):
        if self.message_is_exists(message):
            return

        sender_id = self.get_user_id()
        recipient_id = self.get_recipient_id()
        is_echo = message.get("message", {}).get("is_echo", False)
        app_id = message.get("message", {}).get("app_id", None)
        user = None
        page_admin_is_sender = None

        if sender_id == env.FB_PAGE_ID:
            page_admin_is_sender = True
        elif recipient_id == env.FB_PAGE_ID:
            page_admin_is_sender = False

        if page_admin_is_sender is None:
            raise ValueError("Page ID not found")

        fb_user_id = recipient_id if page_admin_is_sender else sender_id
        user = self.get_user_in_db(fb_user_id)
        thread = self.get_thread_in_db(user)

        if page_admin_is_sender and not is_echo and not app_id:
            self.create_page_admin_message(message, thread)

        if page_admin_is_sender:
            return

        message = self.create_user_message(message, thread)

        if not thread.is_active:
            return

        history = self.get_openai_message(thread)
        answer = gen_answer(thread_id=thread.id, user_id=user.id, history=history)
        chatbot_message = self.create_chatbot_message(answer, thread)
        self.send(
            {
                "text": chatbot_message.content,
            }
        )

    def get_recipient_id(self):
        return self.last_message["recipient"]["id"]

    def create_page_admin_message(
        self, message: dict, thread: ThreadModel
    ) -> MessageModel:
        text = message.get("message", {}).get("text")
        mid = message.get("message", {}).get("mid")

        new_message = CreateMessageModel(
            thread_id=thread.id,
            content=text,
            type=MessageType.page_admin,
            fb_message_id=mid,
        )

        return create_message(new_message)

    def create_user_message(self, message: dict, thread: ThreadModel) -> MessageModel:
        text = message.get("message", {}).get("text")
        mid = message.get("message", {}).get("mid")

        new_message = CreateMessageModel(
            thread_id=thread.id,
            content=text,
            type=MessageType.user,
            fb_message_id=mid,
        )

        return create_message(new_message)

    def create_chatbot_message(self, message: str, thread: ThreadModel) -> MessageModel:
        new_message = CreateMessageModel(
            thread_id=thread.id,
            content=message,
            type=MessageType.bot,
        )

        return create_message(new_message)

    def get_fb_user_profile(
        self, fb_user_id: str, fields=None, timeout=None
    ) -> UserProfile:
        user_profile = self.client.get_user_data(
            recipient_id=fb_user_id,
            fields=fields,
            timeout=timeout,
        )

        if not user_profile:
            return UserProfile(
                id=self.get_user_id(),
            )
        print(user_profile)

        return UserProfile.model_validate(user_profile)

    def get_user_in_db(self, fb_user_id: str) -> UserModel:
        user = get_user_by_fb_user_id(fb_user_id)

        if user is not None:
            return user

        fb_user_profile = self.get_fb_user_profile(fb_user_id)
        new_user_data = CreateUserModel(
            user_name=f"{fb_user_profile.first_name} {fb_user_profile.last_name}",
            password=None,
            fb_user_id=fb_user_id,
            gender=fb_user_profile.gender,
            role=UserRole.fb_user,
        )
        user = create_user(new_user_data)
        return user

    def get_thread_in_db(self, user: UserModel) -> ThreadModel:
        threads = get_all_threads(user.id)
        if threads:
            return threads[0]

        new_thread_data = CreateThreadModel(
            user_id=user.id,
            name=user.user_name,
        )

        thread = create_thread(new_thread_data)
        return thread

    def message_is_exists(self, message: dict) -> bool:
        mid = message.get("message", {}).get("mid")
        return get_message_by_fb_message_id(mid) is not None

    def get_openai_message(
        self, thread: ThreadModel, limit: int = 10
    ) -> list[ChatCompletionMessageParam]:
        messages = get_all_messages(thread.id)
        return [
            (
                ChatCompletionUserMessageParam(
                    role="user",
                    content=message.content,
                )
                if message.type == MessageType.user
                else ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=message.content,
                )
            )
            for message in messages
        ]


messenger = Messenger()

from typing import Dict, List, Optional
from uuid import UUID
import chainlit as cl
from chainlit.data.base import BaseDataLayer
from models.thread import ThreadModel
from repositories.user import get as get_user
from repositories.message import (
    get_all as get_all_messages,
    update as update_message,
    delete as delete_message,
)
from repositories.thread import (
    get as get_thread,
    delete as delete_thread,
    get_all as get_all_threads,
)
from models.message import (
    MessageType,
    UpdateMessageModel,
)
from chainlit.data.utils import queue_until_user_message
from chainlit.types import (
    Feedback,
    ThreadDict,
    ThreadFilter,
    PaginatedResponse,
    Pagination,
    PageInfo,
)
from chainlit.element import ElementDict, Element
from chainlit.step import StepDict
import chainlit.data as cl_data


class DataLayer(BaseDataLayer):
    """Custom data layer for Chainlit."""

    async def get_user(self, identifier: str) -> Optional[cl.PersistedUser]:
        user = get_user(UUID(identifier))
        if not user:
            return None

        return cl.PersistedUser(
            id=str(user.id),
            identifier=str(user.id),
            createdAt=user.created_at.isoformat(),
            metadata={"user_id": str(user.id), "role": user.role.value},
        )

    async def create_user(self, user: cl.User) -> Optional[cl.PersistedUser]:
        pass

    async def delete_feedback(
        self,
        feedback_id: str,
    ) -> bool:
        return False

    async def upsert_feedback(
        self,
        feedback: Feedback,
    ) -> str:
        return ""

    @queue_until_user_message()
    async def create_element(self, element: Element) -> None:
        # Implement the method logic or leave it as a coroutine with a proper return
        return None

    async def get_element(
        self, thread_id: str, element_id: str
    ) -> Optional[ElementDict]:
        return None

    @queue_until_user_message()
    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        pass

    @queue_until_user_message()
    async def create_step(self, step_dict: StepDict):
        pass

    @queue_until_user_message()
    async def update_step(self, step_dict: StepDict):
        print(f"update_step: {step_dict}")

        if step_dict.get("type") not in ["user_message", "assistant_message"]:
            return

        update_message(
            UUID(step_dict.get("id")),
            UpdateMessageModel(
                content=step_dict.get("output", ""),
            ),
        )

    @queue_until_user_message()
    async def delete_step(self, step_id: str):
        delete_message(UUID(step_id))

    async def get_thread_author(self, thread_id: str) -> str:
        print(f"get_thread_author: {thread_id}")

        thread = get_thread(UUID(thread_id))

        if not thread:
            return ""

        return str(thread.user_id)

    async def delete_thread(self, thread_id: str):
        delete_thread(UUID(thread_id))

    def _convert_to_chainlit_thread(self, thread: ThreadModel) -> ThreadDict:
        messages = get_all_messages(thread.id, limit=None)

        chainlit_steps = []
        for i, message in enumerate(messages):
            chainlit_steps.append(
                StepDict(
                    name=message.type,
                    id=str(message.id),
                    threadId=str(message.thread_id),
                    parentId=str(messages[i - 1].id) if i > 0 else None,
                    output=message.content,
                    createdAt=message.created_at.isoformat(),
                    streaming=False,
                    type=(
                        "user_message"
                        if message.type == MessageType.user
                        else "assistant_message"
                    ),
                )
            )

        return ThreadDict(
            id=str(thread.id),
            name=thread.name,
            userIdentifier=str(thread.user_id),
            createdAt=thread.created_at.isoformat(),
            metadata={},
            tags=[],
            userId=str(thread.user_id),
            elements=[],
            steps=chainlit_steps,
        )

    async def list_threads(
        self, pagination: Pagination, filters: ThreadFilter
    ) -> PaginatedResponse[ThreadDict]:
        if not filters.userId:
            raise ValueError("userId is required")

        threads = get_all_threads(UUID(filters.userId))

        return PaginatedResponse(
            data=[self._convert_to_chainlit_thread(thread) for thread in threads],
            pageInfo=PageInfo(
                hasNextPage=False,
                startCursor=None,
                endCursor=None,
            ),
        )

    async def get_thread(self, thread_id: str) -> "Optional[ThreadDict]":
        print(f"get_thread: {thread_id}")

        thread = get_thread(UUID(thread_id))
        if not thread:
            return None

        return self._convert_to_chainlit_thread(thread)

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        pass

    async def build_debug_url(self) -> str:
        return ""


def set_data_layer():
    if not cl_data._data_layer:
        cl_data._data_layer = DataLayer()


set_data_layer()

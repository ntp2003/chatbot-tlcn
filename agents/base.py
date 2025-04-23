from typing import Any, Literal, Optional

from models.user_memory import UserMemoryModel
from service.openai import _chat_model
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from openai.types.chat_model import ChatModel


class Instruction(BaseModel):
    content: str
    examples: list[str] = []


class SystemPromptConfig(BaseModel):
    pass

    def get_openai_messages(
        self,
        conversation_messages: list[ChatCompletionMessageParam],
    ) -> list[ChatCompletionMessageParam]:
        raise NotImplementedError(
            "get_openai_messages method must be implemented in subclasses"
        )


class AgentResponseBase(BaseModel):
    type: Literal["finished", "navigate", "error", "message"]
    content: Optional[str] = None


class AgentTemporaryMemory(BaseModel):
    chat_completions_messages: list[ChatCompletionMessageParam] = []
    user_memory: UserMemoryModel | None = None


class Agent:
    def __init__(
        self,
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        model: ChatModel = _chat_model,
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
    ):
        self.system_prompt_config = system_prompt_config
        self.model: ChatModel = model
        self.temporary_memory = temporary_memory

    def run(self, *args: Any, **kwargs: Any) -> AgentResponseBase:
        raise NotImplementedError("run method must be implemented in subclasses")

from typing import Literal, Optional
from overrides import override
from pydantic import BaseModel, Field
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from service.openai import _client, _chat_model
from openai.types.chat_model import ChatModel
from agents.base import (
    Agent as AgentBase,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)
from models.user_memory import UserMemory, UserMemoryModel


class ConsultantDemand(BaseModel):
    """
    The information about the demand of the user for searching or consulting.
    """

    user_demands: list[Literal["phone", "undetermined"]] = Field(
        default=["undetermined"],
        description="The type of demand the user is making.",
    )


class SystemPromptConfig(SystemPromptConfigBase):
    pass

    @override
    def get_openai_messages(
        self,
        conversation_messages: list[ChatCompletionMessageParam],
    ) -> list[ChatCompletionMessageParam]:
        return []


class AgentTemporaryMemory(AgentTemporaryMemoryBase):
    pass


class AgentResponse(AgentResponseBase):
    pass


class Agent(AgentBase):
    def __init__(
        self,
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        model: ChatModel = _chat_model,
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
    ):
        super().__init__(
            system_prompt_config=system_prompt_config,
            model=model,
            temporary_memory=temporary_memory,
        )

    def run(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> AgentResponse:
        self.temporary_memory.chat_completions_messages = (
            self.system_prompt_config.get_openai_messages(messages)
        )

        response = _client.beta.chat.completions.parse(
            model=self.model,
            messages=self.temporary_memory.chat_completions_messages,
            temperature=0,
            timeout=30,
            response_format=ConsultantDemand,
        )

        consultant_demand = response.choices[0].message.parsed

        return AgentResponse(type="finished", content="")

from typing import List, Optional
from agents.base import (
    Agent as AgentBase,
    Instruction,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)
from models.user_memory import UserMemoryModel
from agents.utils import generate_response_by_instructions
from openai.types.chat import ChatCompletionMessageParam

class SystemPromptConfig(SystemPromptConfigBase):
    role: str = "Laptop Sales Assistant"
    task: str = "Generate natural and helpful responses about laptop products"
    skills: list[str] = [
        "Clear communication about technical specifications",
        "Personalized product recommendations",
        "Professional and friendly tone",
    ]
    rules: list[str] = [
        "Use simple language to explain technical terms",
        "Maintain a helpful and professional tone",
        "Provide relevant information based on user context",
    ]

class AgentTemporaryMemory(AgentTemporaryMemoryBase):
    user_memory: Optional[UserMemoryModel] = None

class AgentResponse(AgentResponseBase):
    pass

class Agent(AgentBase):
    def __init__(
        self,
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
    ):
        self.system_prompt_config = system_prompt_config
        self.temporary_memory = temporary_memory

    def run(
        self,
        conversation_messages: list[ChatCompletionMessageParam],
        instructions: List[Instruction],
        laptop_knowledge: List[str],
    ) -> AgentResponse:
        if not self.temporary_memory.user_memory:
            return AgentResponse(
                type="error",
                content="User memory not found",
            )

        response = generate_response_by_instructions(
            instructions=instructions,
            knowledge=laptop_knowledge,
            conversation_history=conversation_messages,
        )

        return AgentResponse(
            type="success",
            content=response,
        ) 
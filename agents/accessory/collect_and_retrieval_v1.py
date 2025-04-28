from typing import List, Optional
from pydantic import BaseModel, Field
from agents.base import (
    Agent as AgentBase,
    Instruction,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)
from models.user_memory import UserMemoryModel
from openai.types.chat import ChatCompletionMessageParam
from tools.accessories.search import search_accessories
from tools.accessories.filter import filter_accessories

class SystemPromptConfig(SystemPromptConfigBase):
    role: str = "Accessories Product Consultant"
    task: str = "Analyze user requirements and find suitable accessories"
    skills: list[str] = [
        "Understanding accessory compatibility",
        "Product matching based on user needs",
        "Price and quality analysis",
    ]
    rules: list[str] = [
        "Verify compatibility with user's devices",
        "Consider both budget and quality requirements",
        "Explain features and benefits clearly",
    ]

class AgentTemporaryMemory(AgentTemporaryMemoryBase):
    user_memory: Optional[UserMemoryModel] = None
    offset: int = 0

class AgentResponse(AgentResponseBase):
    instructions: List[Instruction] = []
    knowledge: List[str] = []

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
        messages: list[ChatCompletionMessageParam],
    ) -> AgentResponse:
        if not self.temporary_memory.user_memory:
            return AgentResponse(
                type="error",
                content="User memory not found",
            )

        # Search for accessories based on user requirements
        accessories = search_accessories(
            price_range=self.temporary_memory.user_memory.price_range,
            category=self.temporary_memory.user_memory.accessory_category,
            offset=self.temporary_memory.offset,
        )

        # Filter accessories based on specific requirements
        filtered_accessories = filter_accessories(
            accessories,
            user_requirements=self.temporary_memory.user_memory.requirements,
        )

        # Prepare knowledge about found accessories
        knowledge = []
        for accessory in filtered_accessories:
            knowledge.append(
                f"- {accessory.name}: {accessory.description}, Price: {accessory.price}"
            )

        # Prepare response instructions
        instructions = [
            Instruction(
                content="Generate a response introducing the found accessories",
                examples=[
                    "Dạ, em đã tìm được một số phụ kiện phù hợp với yêu cầu của anh/chị:",
                    "Với nhu cầu của anh/chị, em xin giới thiệu các phụ kiện sau:",
                ]
            ),
        ]

        return AgentResponse(
            type="success",
            content="Found matching accessories",
            instructions=instructions,
            knowledge=knowledge,
        ) 
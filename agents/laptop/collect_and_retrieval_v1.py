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
from tools.laptop.search import search_laptops
from tools.laptop.filter import filter_laptops

class SystemPromptConfig(SystemPromptConfigBase):
    role: str = "Laptop Product Consultant"
    task: str = "Analyze user requirements and find suitable laptop products"
    skills: list[str] = [
        "Understanding laptop specifications and requirements",
        "Product matching based on user needs",
        "Price range analysis",
    ]
    rules: list[str] = [
        "Always confirm user requirements before making suggestions",
        "Consider both budget and technical requirements",
        "Explain technical terms in simple language",
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

        # Search for laptops based on user requirements
        laptops = search_laptops(
            price_range=self.temporary_memory.user_memory.price_range,
            brand=self.temporary_memory.user_memory.brand_name,
            offset=self.temporary_memory.offset,
        )

        # Filter laptops based on specific requirements
        filtered_laptops = filter_laptops(
            laptops,
            user_requirements=self.temporary_memory.user_memory.requirements,
        )

        # Prepare knowledge about found laptops
        knowledge = []
        for laptop in filtered_laptops:
            knowledge.append(
                f"- {laptop.name}: {laptop.specs_summary}, Price: {laptop.price}"
            )

        # Prepare response instructions
        instructions = [
            Instruction(
                content="Generate a response introducing the found laptops",
                examples=[
                    "Dạ, em đã tìm được một số laptop phù hợp với yêu cầu của anh/chị:",
                    "Với nhu cầu của anh/chị, em xin giới thiệu các mẫu laptop sau:",
                ]
            ),
        ]

        return AgentResponse(
            type="success",
            content="Found matching laptops",
            instructions=instructions,
            knowledge=knowledge,
        ) 
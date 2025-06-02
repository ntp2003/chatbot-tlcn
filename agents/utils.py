from typing import Literal, Optional
from overrides import override
from pydantic import BaseModel, Field
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from rq import Queue
from env import env
from db import redis
from service.converter import (
    convert_to_standard_email,
    convert_to_standard_phone_number,
)
from service.email import create_message, send_message
from service.openai import OpenAIChatCompletionsRequest, _client, _chat_model
from openai.types.chat_model import ChatModel
from agents.base import (
    Agent as AgentBase,
    Instruction,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)
from models.user_memory import UserMemory, UserMemoryModel, ProductType
from datetime import datetime


def instructions_to_string(instructions: list[Instruction]) -> str:
    if len(instructions) == 0:
        return ""

    text = ""
    for i, instruction in enumerate(instructions):
        text += f"{i}. {instruction.content}:\n"
        if not instruction.examples:
            continue
        if len(instruction.examples) == 1:
            text += f"Example: {instruction.examples[0]}\n"
        else:
            text += "Examples:\n"
            text += "\n".join([f"   - {example}" for example in instruction.examples])

    return text


def generate_response_by_instructions(
    instructions: list[Instruction],
    knowledge: list[str],
    conversation_history: list[ChatCompletionMessageParam],
    model: str = "gpt-4o-mini",
    user_fine_tune_tone: bool = False,
) -> str:
    if not instructions:
        raise ValueError("Instructions cannot be empty.")

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "## KNOWLEDGE\n"
                + ("\n".join([f"- {knowledge}" for knowledge in knowledge]))
                + "- Information about your phone store:\n"
                "   - Name: FPTShop\n"
                "   - Location: https://fptshop.com.vn/cua-hang\n"
                "   - Hotline: 1800.6601\n"
                "   - Website: [FPTShop](https://fptshop.com.vn)\n"
                "   - Customer service email: cskh@fptshop.com\n"
                f"- Current date: {datetime.now().strftime('%A, %B %d, %Y')} ({datetime.now().strftime('%Y-%m-%d')})\n"
            ),
        },
        {
            "role": "system",
            "content": ("## INSTRUCTIONS\n" + instructions_to_string(instructions)),
        },
        {
            "role": "system",
            "content": (
                "# You are a helpful assistant. Your task is generate a response for the user by <INSTRUCTIONS>.\n"
                "## NOTE\n"
                "- Use only the Vietnamese language in your responses."
                "- The response should be in the form of a conversation."
                "- The response must be follow the <INSTRUCTIONS> and don't say anything else."
            ),
        },
    ]

    if user_fine_tune_tone:
        messages.append(
            {
                "role": "system",
                "content": (
                    "## RULES\n"
                    "- Use only the Vietnamese language in your response. Always refer to yourself using 'em' pronoun. Address the user based on how they refer to themselves . If their preferred address term cannot be determined from their self-reference, then base it on their provided <User gender>: use 'anh' for male, 'chị' for female. If the gender is unknown or not provided, use the polite neutral term 'anh/chị'."
                ),
            }
        )

    messages.extend(conversation_history)

    openai_request = OpenAIChatCompletionsRequest(
        messages=messages,
        model=model,
        temperature=0,
        timeout=60,
    )

    response = openai_request.create()
    return response.choices[0].message.content or ""

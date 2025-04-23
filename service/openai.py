from typing import Iterable, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from env import env
from openai import NotGiven, OpenAI
from openai._types import NOT_GIVEN
import json
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
)
from tools.invoke_tool import invoke
import chainlit as cl

_chat_model = "gpt-4o-mini"
_client = OpenAI(
    api_key=env.OPENAI_API_KEY,
)

_embedding_model = "text-embedding-3-small"


def get_embedding(text, model=_embedding_model):
    text = text.replace("\n", " ")
    return _client.embeddings.create(input=[text], model=model).data[0].embedding


def get_list_embedding(texts, model=_embedding_model):
    texts = [text.replace("\n", " ") for text in texts]
    return [
        item.embedding
        for item in _client.embeddings.create(input=texts, model=model).data
    ]


class OpenAIChatCompletionsRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: list[ChatCompletionMessageParam]
    model: str
    tools: list[ChatCompletionToolParam] | NotGiven = NOT_GIVEN
    temperature: float
    timeout: int

    def create(self):
        if not self.tools or self.tools == NOT_GIVEN:
            return _client.chat.completions.create(
                messages=self.messages,
                model=self.model,
                temperature=self.temperature,
                timeout=self.timeout,
            )
        return _client.chat.completions.create(
            messages=self.messages,
            model=self.model,
            tools=self.tools,
            temperature=self.temperature,
            timeout=self.timeout,
        )


def gen_answer(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
    tools: Iterable[ChatCompletionToolParam],
    max_iterator: int = 5,
    model: str = _chat_model,
    temporary_memory: dict = {},
) -> tuple[str, dict[str, str]]:
    counter = 0
    response = (
        _client.chat.completions.create(
            messages=messages,
            model=model,
            user=str(user_id),
            tools=tools,
            temperature=0,
            timeout=30,
        )
        .choices[0]
        .message
    )

    tool_choices = response.tool_calls

    if not tool_choices:
        if not response.content:
            raise Exception("No response content from the model")
        print("Final response:", response.content)
        return response.content, temporary_memory

    while tool_choices and counter < max_iterator:
        counter += 1
        print("counter:", counter)
        messages.append(response.model_copy())  # type: ignore
        print("\n\n==== tool_calls ====\n\n")
        for tool in tool_choices:
            print(tool.function.name)
            call_id = tool.id
            tool_name = tool.function.name
            args = json.loads(tool.function.arguments)
            tool_response: ChatCompletionToolMessageParam = {
                "role": "tool",
                "tool_call_id": call_id,
                "content": invoke(user_id, thread_id, tool_name, args),
            }
            messages.append(tool_response)  # type: ignore
            temporary_memory[tool_name] = tool_response["content"]
            print("Tool response:", tool_response["content"])
        response = (
            _client.chat.completions.create(
                messages=messages,
                model=model,
                user=str(user_id),
                tools=tools,
                temperature=0,
                timeout=30,
            )
            .choices[0]
            .message
        )
        tool_choices = response.tool_calls

    if counter == max_iterator:
        raise Exception(
            f"Maximum iteration reached ({max_iterator}). Please try again."
        )
    if not response.content:
        raise Exception("No response content from the model")

    print("Final response:", response.content)
    return response.content, temporary_memory

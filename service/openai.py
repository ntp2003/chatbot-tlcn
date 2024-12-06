from typing import Iterable, Optional
from uuid import UUID
from env import env
from openai import NotGiven, OpenAI
import json
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
)
from tools.invoke_tool import invoke
import chainlit as cl

_model = "gpt-4o-mini"
_client = OpenAI(
    api_key=env.OPENAI_API_KEY,
)


def gen_answer(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
    tools: Iterable[ChatCompletionToolParam],
    max_iterator: int = 5,
    model: str = _model,
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

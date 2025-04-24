from typing import Iterable, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from env import env
from openai import NotGiven, OpenAI, NOT_GIVEN
import json
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
)

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

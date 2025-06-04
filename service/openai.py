from time import sleep
from typing import Iterable, Optional
from uuid import UUID

import openai
from pydantic import BaseModel, ConfigDict
from env import env
from openai import NotGiven, OpenAI, NOT_GIVEN, RateLimitError, APITimeoutError
import json
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
)


# _chat_model = "gpt-4o-mini"
_chat_model = "gpt-4o-mini-2024-07-18"

_fine_tuning_model = "ft:gpt-4o-mini-2024-07-18:personal::BePMJcc3"
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

    def create(self, max_retries=5, backoff_factor=3):
        retries = 0
        while retries < max_retries:
            try:
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
            except (RateLimitError, APITimeoutError) as e:
                retries += 1
                wait_time = backoff_factor**retries
                print(f"Rate limit hit. Retry {retries}/{max_retries} in {wait_time}s.")
                sleep(wait_time)
            except openai.OpenAIError as e:
                print(f"OpenAI API error: {e}")
                raise
        raise Exception(f"Failed after {max_retries} retries due to rate limit.")


class OpenAIChatCompletionsParse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: str
    messages: list[ChatCompletionMessageParam]
    temperature: int = 0
    timeout: int = 60
    response_format: type

    def parse(self, max_retries=5, backoff_factor=3):
        retries = 0
        while retries < max_retries:
            try:
                return _client.beta.chat.completions.parse(
                    messages=self.messages,
                    model=self.model,
                    response_format=self.response_format,
                    temperature=self.temperature,
                    timeout=self.timeout,
                )
            except (RateLimitError, APITimeoutError) as e:
                retries += 1
                wait_time = backoff_factor**retries
                print(f"Rate limit hit. Retry {retries}/{max_retries} in {wait_time}s.")
                sleep(wait_time)
            except openai.OpenAIError as e:
                print(f"OpenAI API error: {e}")
                raise
        raise Exception(f"Failed after {max_retries} retries due to rate limit.")

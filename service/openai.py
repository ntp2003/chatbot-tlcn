from env import env
from openai import NotGiven, OpenAI
import json

_model = "gpt-4o-mini"
_client = OpenAI(api_key=env.OPENAI_API_KEY)


def gen_answer(user_message: str, history: list = []):
    formatted_history = []
    for user, assistant in history:
        formatted_history.append({"role": "user", "content": user})
        formatted_history.append({"role": "assistant", "content": assistant})

    formatted_history.append({"role": "user", "content": user_message})

    response = _client.chat.completions.create(
        model=_model, messages=formatted_history, temperature=1.0
    )

    return response.choices[0].message.content

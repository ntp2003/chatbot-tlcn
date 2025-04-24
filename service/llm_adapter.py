# service/llm_adapter.py
from typing import List, Dict, Any, Optional
from env import env

class LLMAdapter:
    def __init__(self, provider="openai"):
        self.provider = provider
        if provider == "openai":
            from service.openai_1 import openai_chat_completion
            self.chat_completion = openai_chat_completion
        elif provider == "gemini":
            from service.gemini import GeminiService
            gemini = GeminiService(api_key=env.GEMINI_KEY)
            self.chat_completion = gemini.chat_completion
        else:
            raise ValueError(f"Provider {provider} not supported")
    
    def invoke(self, messages, tools=None, temperature=0.7):
        return self.chat_completion(messages, tools, temperature)

'''

# Lấy provider từ config hoặc env
llm_provider = env.LLM_PROVIDER  # "openai" hoặc "gemini"
llm = LLMAdapter(provider=llm_provider)

def invoke_tool(messages, tools, temperature=0.7):
    response = llm.invoke(messages, tools, temperature)
    return response
'''

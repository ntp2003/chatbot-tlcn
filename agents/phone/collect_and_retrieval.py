from datetime import datetime
import json
from typing import Any, Callable, Literal, Optional

from openai import NOT_GIVEN, InternalServerError, NotGiven
from overrides import override
from models.user_memory import UserMemoryModel
from service.openai import _client, _chat_model, OpenAIChatCompletionsRequest
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from pydantic import BaseModel
from tools.base import ToolBase, ToolResponse
from openai.types.chat_model import ChatModel
from agents.base import (
    Agent as AgentBase,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)


class SystemPromptConfig(SystemPromptConfigBase):
    role: str = "You are an information collector."
    task: str = (
        "Your task is to collect and update the user's requirements about the service or product based on the user's latest message."
    )
    skills: list[str] = [
        "Demonstrates robust natural language processing skills that are clear and easy to understand, especially in the tourism sector.",
        "Carefully read and accurately understand the user's requirements in the conversation.",
        "Collect and update a diverse array of information simultaneously with precision and thoroughness.",
    ]
    base_knowledge: list[str] = [
        f"Current date: {datetime.now().strftime('%A, %B %d, %Y')} ({datetime.now().strftime('%Y-%m-%d')})",
    ]
    rules: list[str] = [
        "Your primary responsibility is to diligently collect, verify, and analyze all relevant information. Please ensure your full attention is dedicated exclusively to this task.",
        "You must collect and update the user's requirements by calling appropriate functions concurrently, ensuring that all parameters are correctly assigned.",
        "When a user refers to a service or product without including any price details, do not attempt to collect or update the price information.",
        "If a user asks about the price of a service or product but does not specify a particular price value, there is no need to collect or update any price information.",
        "Extract and standardize all mentioned dates to the format YYYY-MM-DD.",
        "Do not procedure invalid content.",
    ]
    working_steps: list[str] = [
        (
            "**Step 1:** Read the user's latest message carefully (self-processing without providing any response).\n"
            "   - Understand the acronyms, slang, and abbreviations used in the message if any.\n"
            "   - Identify the user's requirements about the service or product.\n"
        ),
        (
            "**Step 2:** Based on Step 1, execute all relevant functions concurrently using asynchronous calls.\n"
            "   - Ensure that all appropriate functions are called concurrently.\n"
            "   - Identify and assign the correct parameters to the functions.\n"
        ),
    ]
    initialization: str = (
        "As a/an <ROLE>, you are required to adhere to the <WORKFLOW> and follow the <RULES> strictly, using your expertise in <SKILLS> to do your task effectively."
    )

    def skills_to_string(self) -> str:
        return "\n".join([f"- {skill}" for skill in self.skills])

    def base_knowledge_to_string(self) -> str:
        return "\n".join([f"- {knowledge}" for knowledge in self.base_knowledge])

    def rules_to_string(self) -> str:
        return "\n".join([f"- {rule}" for rule in self.rules])

    def working_steps_to_string(self) -> str:
        return "\n".join([f"{step}" for step in self.working_steps])

    @override
    def get_openai_messages(
        self,
        conversation_messages: list[ChatCompletionMessageParam],
    ) -> list[ChatCompletionMessageParam]:

        role_task_skill_message: ChatCompletionMessageParam = {
            "role": "system",
            "content": f"""# ROLE
{self.role}

## PROFILE:
- Languages: Vietnamese and English.
- Description: {self.task}

## SKILLS:
{self.skills_to_string()}""",
        }
        base_knowledge_message: ChatCompletionMessageParam = {
            "role": "system",
            "content": f"""## BASE KNOWLEDGE:\n{self.base_knowledge_to_string()}""",
        }
        rules_message: ChatCompletionMessageParam = {
            "role": "system",
            "content": f"""## RULES:\n{self.rules_to_string()}""",
        }
        workflow_message: ChatCompletionMessageParam = {
            "role": "system",
            "content": f"""## WORKFLOW:\n{self.working_steps_to_string()}""",
        }
        initialization_message: ChatCompletionMessageParam = {
            "role": "system",
            "content": f"""## INITIALIZATION:\n{self.initialization}""",
        }

        latest_user_message = next(
            (msg for msg in conversation_messages[-1::-1] if msg["role"] == "user"),
            None,
        )

        latest_user_message_description: ChatCompletionMessageParam = {
            "role": "system",
            "content": f"This is the latest user's message: {(latest_user_message or {}).get('content', 'No content available')}",
        }

        messages = [
            role_task_skill_message,
            base_knowledge_message,
            *conversation_messages,
            latest_user_message_description,
            rules_message,
            workflow_message,
            initialization_message,
        ]

        return messages


class AgentTemporaryMemory(AgentTemporaryMemoryBase):
    pass


class Instruction(BaseModel):
    content: str
    examples: list[str] = []


class AgentResponse(AgentResponseBase):
    instructions: list[Instruction] = []


class Agent(AgentBase):
    def __init__(
        self,
        tools: list[ToolBase],
        invoke_tool: Callable,
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        model: ChatModel = _chat_model,
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
    ):
        self.tools = tools
        self.invoke_tool = invoke_tool
        self.system_prompt_config = system_prompt_config
        self.model = model
        self.temporary_memory = temporary_memory

    def run(
        self,
        messages: list[ChatCompletionMessageParam],
        max_iterator: int = 5,
    ) -> AgentResponse:
        if self.temporary_memory.user_memory is None:
            return AgentResponse(
                type="error",
                content="User memory is not available.",
            )

        self.temporary_memory.chat_completions_messages = (
            self.system_prompt_config.get_openai_messages(messages)
        )
        counter = 0
        agent_response = None

        while counter < max_iterator:
            counter += 1
            print("counter:", counter)
            openai_request = self._get_openai_request()
            response = openai_request.create().choices[0].message
            tool_choices = response.tool_calls
            if not tool_choices and not response.content:
                raise Exception("No response content from the model")
            if not tool_choices:
                print("Final response:", response.content)
                agent_response = AgentResponse(
                    type="finished", content=response.content
                )
                break

            self.temporary_memory.chat_completions_messages.append(response.model_copy())  # type: ignore
            tool_responses = self._invoke_tools(tool_choices)
            agent_response = self._tool_responses_post_process(tool_responses)
            if agent_response.type == "finished":
                break

        if not agent_response:
            raise Exception("No agent response")

        if agent_response.type != "finished":
            raise Exception("Agent did not finish successfully")

        return agent_response

    def _invoke_tools(
        self, tool_choices: list[ChatCompletionMessageToolCall]
    ) -> list[ToolResponse]:
        tool_responses = []

        for tool_choice in tool_choices:
            call_id = tool_choice.id
            tool_name = tool_choice.function.name
            kwargs = {} or json.loads(tool_choice.function.arguments)
            selected_tool = next(tool for tool in self.tools if tool.name == tool_name)
            tool_response = selected_tool.invoke(
                temporary_memory=self.temporary_memory, **kwargs
            )
            tool_responses.append(tool_response)
            openai_tool_response: ChatCompletionToolMessageParam = {
                "role": "tool",
                "tool_call_id": call_id,
                "content": tool_response.content,  # type: ignore
            }
            self.temporary_memory.chat_completions_messages.append(openai_tool_response)

        return tool_responses

    def _get_openai_request(
        self,
        before_request: Optional[OpenAIChatCompletionsRequest] = None,
        before_tool_response: Optional[ToolResponse] = None,
    ) -> OpenAIChatCompletionsRequest:
        if not before_request:
            return OpenAIChatCompletionsRequest(
                messages=self.temporary_memory.chat_completions_messages,
                model=self.model,
                tools=(
                    [tool.tool_schema for tool in self.tools]
                    if self.tools
                    else NOT_GIVEN
                ),
                temperature=0,
                timeout=30,
            )
        if not before_tool_response:
            return OpenAIChatCompletionsRequest(
                messages=before_request.messages,
                model=before_request.model,
                tools=before_request.tools,
                temperature=before_request.temperature,
                timeout=before_request.timeout,
            )

        if before_tool_response.type == "message":
            return OpenAIChatCompletionsRequest(
                messages=self.temporary_memory.chat_completions_messages,
                model=self.model,
                tools=NOT_GIVEN,
                temperature=0,
                timeout=30,
            )

        raise NotImplementedError()

    def _tool_responses_post_process(
        self, tool_responses: list[ToolResponse]
    ) -> AgentResponse:
        if any(tool_response.type == "navigate" for tool_response in tool_responses):
            return AgentResponse(type="navigate", content="Navigate to another tool")
        if any(tool_response.type == "message" for tool_response in tool_responses):
            return AgentResponse(
                type="message", content="Next to generate message from tool"
            )
        if all(tool_response.type == "finished" for tool_response in tool_responses):
            return AgentResponse(type="finished", content="All tools finished")
        return AgentResponse(type="error", content="Error")

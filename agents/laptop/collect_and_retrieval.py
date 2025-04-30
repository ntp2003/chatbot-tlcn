from datetime import datetime
import json
from typing import Any, Callable, Literal, Optional

from openai import NOT_GIVEN, InternalServerError, NotGiven
from overrides import override
from models.laptop import LaptopModel
from models.user_memory import UserIntent, UserMemoryModel
from repositories.redis import get_value
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
    Instruction,
)
from service.laptop import Config, search, LaptopFilter
from agents.config import BRAND_DEFAULT
from repositories.user_memory import update as update_user_memory
from models.user_memory import UpdateUserMemoryModel
from tools.laptop.brand_and_version import Tool as BrandAndVersionTool
from tools.laptop.price import Tool as PriceTool
from tools.laptop.user_intent import Tool as UserIntentTool
from tools.laptop.name import Tool as NameTool


class SystemPromptConfig(SystemPromptConfigBase):
    role: str = "You are an information collector."
    task: str = (
        #"Your task is to collect and update the user's requirements about laptops based on the user's latest message."
        "Your task is to collect and update the user's requirements about the service or product based on the user's latest message."

    )
    skills: list[str] = [
        "Demonstrates robust natural language processing skills that are clear and easy to understand, especially in the field of laptop consulting.",
        "Carefully read and accurately understand the user's requirements in the conversation.",
        "Collect and update a diverse array of information simultaneously with precision and thoroughness.",
    ]
    base_knowledge: list[str] = [
        f"Current date: {datetime.now().strftime('%A, %B %d, %Y')} ({datetime.now().strftime('%Y-%m-%d')})",
    ]
    rules: list[str] = [
        "Your primary responsibility is to diligently collect, verify, and analyze all relevant information. Please ensure your full attention is dedicated exclusively to this task.",
        "You must collect and update the user's requirements by calling appropriate functions concurrently, ensuring that all parameters are correctly assigned.",
        "When a user refers to a laptop without including any price details, do not attempt to collect or update the price information.",
        "If a user asks about the price of a laptop but does not specify a particular price value, there is no need to collect or update any price information.",
        "Do not procedure invalid content.",
    ]
    working_steps: list[str] = [
        (
            "**Step 1:** Read the user's latest message carefully (self-processing without providing any response).\n"
            "   - Understand the acronyms, slang, and abbreviations used in the message if any.\n"
            "   - Identify the user's requirements about laptops.\n"
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
    offset: int = 0


class AgentResponse(AgentResponseBase):
    instructions: list[Instruction] = []
    knowledge: list[str] = []


class Agent(AgentBase):
    def __init__(
        self,
        tools: list[ToolBase] = [
            UserIntentTool(),
            NameTool(),
            BrandAndVersionTool(),
            PriceTool(),
        ],
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        model: ChatModel = _chat_model,
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
        limit: int = 4,
    ):
        self.tools = tools
        self.system_prompt_config = system_prompt_config
        self.model = model
        self.temporary_memory = temporary_memory
        self.limit = limit

    def run(
        self, messages: list[ChatCompletionMessageParam], *args, **kwargs
    ) -> AgentResponse:
        if self.temporary_memory.user_memory is None:
            return AgentResponse(
                type="error",
                content="User memory is not available.",
            )

        self.temporary_memory.chat_completions_messages = (
            self.system_prompt_config.get_openai_messages(messages)
        )

        agent_response = None
        openai_request = self._get_openai_request()
        response = openai_request.create().choices[0].message
        tool_choices = response.tool_calls

        if not tool_choices and not response.content:
            raise Exception("No response content from the model")
        if not tool_choices:
            print("Final response:", response.content)
            agent_response = AgentResponse(type="finished", content=response.content)
        else:
            tool_responses = self._invoke_tools(tool_choices)
            agent_response = self._tool_responses_post_process(tool_responses)

        if not agent_response:
            raise Exception("No agent response")

        if agent_response.type == "message":
            return agent_response

        if agent_response.type != "finished":
            raise Exception("Agent did not finish successfully")

        user_memory = self.temporary_memory.user_memory

        if not user_memory.brand_code and not user_memory.product_name:
            user_memory.brand_code = BRAND_DEFAULT
            self.temporary_memory.user_memory = user_memory

            agent_response.instructions.append(
                Instruction(
                    content="You must ask the user for the brand of the laptop they are interested in such as Dell, HP, Lenovo, etc.",
                )
            )
            return agent_response

        offset = get_value(f"offset:{user_memory.thread_id}")
        offset = int(offset) if offset else 0

        if not user_memory.intent:
            user_memory.intent = UserIntent()

        if user_memory.intent.is_user_needs_other_suggestions:
            user_memory.product_name = None
            offset += self.limit

        self.temporary_memory.offset = offset

        if user_memory.product_name:
            agent_response = self._consult_specific_laptop()
        else:
            agent_response = self._consult_laptops()

        return agent_response

    def _consult_laptops(self) -> AgentResponse:
        user_memory: UserMemoryModel = self.temporary_memory.user_memory # type: ignore
        offset = self.temporary_memory.offset
        laptops = []
        config = Config(limit=self.limit)
        config.offset = offset
        filter = self._get_laptop_filter_from_user_memory(config=config)
        if not user_memory.consultation_status.is_recommending:
            laptops = self.retrieval(filter=filter)

        if len(laptops) > 0:
            user_memory.consultation_status.is_recommending = False
            user_memory.product_name = (
                laptops[0].name if len(laptops) == 1 else user_memory.product_name
            )
            user_memory.current_filter.product_name = (
                laptops[0].name if len(laptops) == 1 else None
            )
            return (
                self._laptops_to_responses(laptops)
                if len(laptops) > 1
                else self._specific_laptop_to_response(laptops[0])
            )

        if offset > 0 and not user_memory.consultation_status.is_recommending:
            config.offset -= self.limit
            filter.config = config
            laptops = self.retrieval(filter=filter)
            len_previous_page = len(laptops)
            config.offset += len_previous_page
            filter.config = config
            self.temporary_memory.offset = config.offset

        config.is_recommending = True
        laptops = self.retrieval(filter=filter)
        if len(laptops) > 0:
            user_memory.consultation_status.is_recommending = True
            user_memory.product_name = (
                laptops[0].name if len(laptops) == 1 else user_memory.product_name
            )
            user_memory.current_filter.product_name = (
                laptops[0].name if len(laptops) == 1 else None
            )
            return self._laptops_to_response(laptops)

        self.temporary_memory.offset = 0
        user_memory.consultation_status.is_recommending = False
        instructions = [
            Instruction(
                content="You should ask the user about another requirement for the laptop they are interested in such as the brand, price, etc.",
                examples=[
                    "Anh/chị có yêu cầu gì khác về laptop không như thương hiệu, giá cả, ...",
                ],
            )
        ]

        if not user_memory.has_contact_info():
            instructions.append(
                Instruction(
                    content="You must ask the user for their contact information to provide better advice on the laptop they are interested in.",
                    examples=[
                        "Để tư vấn tốt hơn cho bạn, bạn có thể cho mình biết số điện thoại hoặc email của bạn không?",
                    ],
                )
            )

        return AgentResponse(
            type="finished",
            instructions=instructions,
        )

    def _consult_specific_laptop(self) -> AgentResponse:
        user_memory: UserMemoryModel = self.temporary_memory.user_memory # type: ignore

        config = Config(limit=1)
        filter = self._get_laptop_filter_from_user_memory(config=config)
        laptops = self.retrieval(
            filter=filter,
            is_recommending=user_memory.consultation_status.is_recommending,
        )

        if not laptops:
            user_memory.product_name = None
            user_memory.current_filter.product_name = None
            user_memory.consultation_status.is_recommending = True
            return self._consult_laptops()

        laptop = laptops[0]
        user_memory.current_filter.product_name = laptop.name
        return self._specific_laptop_to_response(laptop)

    def _invoke_tools(
        self, tool_choices: list[ChatCompletionMessageToolCall]
    ) -> list[ToolResponse]:
        tool_responses = []

        for tool_choice in tool_choices:
            tool_name = tool_choice.function.name
            kwargs = {} or json.loads(tool_choice.function.arguments)
            selected_tool = next(tool for tool in self.tools if tool.name == tool_name)
            tool_response = selected_tool.invoke(
                temporary_memory=self.temporary_memory, **kwargs
            )
            print(f"Tool response for {tool_name}:")
            print(
                 kwargs,
                 (
                     self.temporary_memory.user_memory.model_dump()
                     if self.temporary_memory.user_memory
                     else None
                 ),
             )
            tool_responses.append(tool_response)

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
                type="message",
                instructions=[
                    Instruction(
                        content=tool_response.content,
                    )
                    for tool_response in tool_responses
                    if tool_response.type == "message" and tool_response.content
                ],
            )

        if any(tool_response.type == "error" for tool_response in tool_responses):
            return AgentResponse(
                type="message",
                instructions=[
                    Instruction(
                        content=tool_response.content,
                    )
                    for tool_response in tool_responses
                    if tool_response.type == "error" and tool_response.content
                ],
            )

        if all(tool_response.type == "finished" for tool_response in tool_responses):
            return AgentResponse(type="finished", content="All tools finished")

        raise NotImplementedError(
            "Tool responses post process not implemented for this case"
        )

    def _get_laptop_filter_from_user_memory(self, config: Config | None = None) -> LaptopFilter:
        if not self.temporary_memory.user_memory:
            raise Exception("User memory is not available.")

        user_memory: UserMemoryModel = self.temporary_memory.user_memory # type: ignore
        config = config or Config()

        filter = LaptopFilter(
            config=config,
            brand_code=user_memory.brand_code,
            max_price=user_memory.max_price,
            min_price=user_memory.min_price,
            name=user_memory.current_filter.product_name or user_memory.product_name,
        )

        return filter

    def retrieval(
        self, filter: LaptopFilter | None, is_recommending: bool = False
    ) -> list[LaptopModel]:
        """
        Args:
            filter (LaptopFilter | None): Defaults to None. If None, the filter will be created from the user's memory.

        Returns:
            list[LaptopModel]: List of laptops that match the filter.
        """

        if not filter:
            filter = self._get_laptop_filter_from_user_memory()

        laptops = search(filter)

        return laptops

    def _laptops_to_response(self, laptops: list[LaptopModel]) -> AgentResponse:
        user_memory: UserMemoryModel = self.temporary_memory.user_memory
        knowledge = [laptop.to_text(inclue_key_selling_points=True) for laptop in laptops]

        instructions = []

        if user_memory.consultation_status.is_recommending:
            instructions.append(
                Instruction(
                    content="The information about laptop products in <LAPTOP KNOWLEDGE> may not match the user's requirements. So you should notify the user that this is a recommendation may be match their requirements.",
                    examples=[
                        "Bên em có một số laptop có thể phù hợp với yêu cầu anh/chị:\n<LAPTOP_1>\n<LAPTOP_2>\n<LAPTOP_3>\n\nNếu anh/chị có yêu cầu cụ thể hơn về laptop, vui lòng cho em biết để em có thể tư vấn tốt hơn nhé.",
                    ],
                )
            )
        else:
            instructions.append(
                Instruction(
                    content="The information about laptop products in <LAPTOP KNOWLEDGE> is based on the user's requirements.",
                )
            )

        if not user_memory.has_contact_info():
            instructions.append(
                Instruction(
                    content="You must ask the user for their contact information to provide better advice on the laptop they are interested in.",
                    examples=[
                        "Để tư vấn tốt hơn cho bạn, bạn có thể cho mình biết số điện thoại hoặc email của bạn không?",
                    ],
                )
            )

        return AgentResponse(
            type="finished",
            knowledge=knowledge,
            instructions=instructions,
        )

    def _specific_laptop_to_response(self, laptop: LaptopModel) -> AgentResponse:
        user_memory: UserMemoryModel = self.temporary_memory.user_memory

        instructions = [
            Instruction(
                content="If user has any question about laptop in <LAPTOP KNOWLEDGE>, you should provide concise answer based on <LAPTOP KNOWLEDGE>.",
            ),
            Instruction(
                content="If the information in <LAPTOP KNOWLEDGE> is not enough, you must provide the general information about the laptop in <LAPTOP KNOWLEDGE> and suggest the user to visit the website for more details.",
            ),
        ]

        if not user_memory.has_contact_info():
            instructions.append(
                Instruction(
                    content="You must ask the user for their contact information to provide better advice on the laptop they are interested in.",
                    examples=[
                        "Để tư vấn tốt hơn cho bạn, bạn có thể cho mình biết số điện thoại hoặc email của bạn không?",
                    ],
                )
            )

        return AgentResponse(
            type="finished",
            knowledge=[
                laptop.to_text(
                    inclue_key_selling_points=True,
                    include_promotion=True,
                    include_sku_variants=True,
                    include_description=True,
                )
            ],
            instructions=instructions,
        )
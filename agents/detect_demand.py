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
import weave
from agents.utils import generate_response_by_instructions
from env import env
from db import redis
from service.converter import (
    convert_to_standard_email,
    convert_to_standard_phone_number,
)
from service.email import create_message, send_message
from service.openai import _client, _chat_model
from openai.types.chat_model import ChatModel
from agents.base import (
    Agent as AgentBase,
    Instruction,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)
from models.user_memory import UserMemory, UserMemoryModel, ProductType


class UserContactInfo(BaseModel):
    """
    The information about the user's contact information.
    """

    phone_number: Optional[str] = Field(
        description="The user's phone number that the user provides. If the user not provide, it will be None.",
    )

    email: Optional[str] = Field(
        description="The user's email that the user provides. If the user not provide, it will be None.",
    )


class UserRequest(BaseModel):
    """
    Contains the analysis of the user's request about the user's specific request type and their contact details.
    """

    user_demand: Literal[
        ProductType.MOBILE_PHONE,
        ProductType.LAPTOP,
        ProductType.ACCESSORY,
        ProductType.UNDETERMINED,
    ] = Field(
        description="The type of demand the user is making. That is determined by the latest demand.",
    )

    user_info: UserContactInfo = Field(
        description="The user's contact information.",
    )


class SystemPromptConfig(SystemPromptConfigBase):
    role: str = "Agent analyzes the information in the user request."
    task: str = (
        "Your task is to analyze the user's request and collect the information about the user demand and the user's contact information."
    )
    skills: list[str] = [
        "Understanding natural language, especially in conversations involving special situations such as abbreviations and slang.",
        "Carefully read and accurately understand the context in the conversation.",
    ]
    rules: list[str] = [
        "Just update the user's contact information if the user provides it.",
        "Do not make any assumptions about the user's contact information.",
    ]
    working_steps: list[str] = [
        (
            "**Step 1:** Read the user's latest message carefully (self-processing without providing any response).\n"
            "   - Understand the acronyms, slang, and abbreviations used in the message if any.\n"
            "   - Identify the current user demand and the user's contact information (if user provides).\n"
        ),
        (
            "**Step 2:** Based on Step 1, determine the user's demand type and contact information."
        ),
    ]
    initialization: str = (
        "As a/an <ROLE>, you are required to adhere to the <WORKFLOW> and follow the <RULES> strictly, using your expertise in <SKILLS> to do your task effectively."
    )

    def skills_to_string(self) -> str:
        return "\n".join([f"- {skill}" for skill in self.skills])

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
            *conversation_messages,
            latest_user_message_description,
            rules_message,
            workflow_message,
            initialization_message,
        ]

        return messages


class AgentTemporaryMemory(AgentTemporaryMemoryBase):
    pass


class AgentResponse(AgentResponseBase):
    instructions: list[Instruction] = []


class Agent(AgentBase):
    def __init__(
        self,
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        model: ChatModel = _chat_model,
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
    ):
        self.system_prompt_config: SystemPromptConfig = system_prompt_config
        self.model: ChatModel = model
        self.temporary_memory: AgentTemporaryMemory = temporary_memory

    def run(
        self, messages: list[ChatCompletionMessageParam], *args, **kwargs
    ) -> AgentResponse:
        user_memory = self.temporary_memory.user_memory

        if not user_memory:
            return AgentResponse(
                type="error",
                content="User memory not found.",
            )

        self.temporary_memory.chat_completions_messages = (
            self.system_prompt_config.get_openai_messages(messages)
        )

        response = _client.beta.chat.completions.parse(
            model=self.model,
            messages=self.temporary_memory.chat_completions_messages,
            temperature=0,
            timeout=30,
            response_format=UserRequest,
        )

        user_request = response.choices[0].message.parsed

        if not user_request:
            return AgentResponse(
                type="finished",
                content="No information about the user's request found.",
            )

        print("User request:", user_request.model_dump())

        if user_request.user_demand != ProductType.UNDETERMINED:
            user_memory.intent.product_type = user_request.user_demand

        phone_number = user_request.user_info.phone_number
        email = user_request.user_info.email

        invalid_infos = []
        has_phone_number_before = user_memory.phone_number is not None
        updated_phone_number = False
        standard_phone_number = convert_to_standard_phone_number(phone_number)
        standard_email = convert_to_standard_email(email)

        if phone_number and not standard_phone_number:
            invalid_infos.append("phone number")
        else:
            updated_phone_number = standard_phone_number != user_memory.phone_number
            user_memory.phone_number = standard_phone_number or user_memory.phone_number

        if email and not standard_email:
            invalid_infos.append("email")
        else:
            user_memory.email = standard_email or user_memory.email

        phone_number_is_missing = not user_memory.phone_number

        if (
            not has_phone_number_before and not phone_number_is_missing
        ) or updated_phone_number:
            self._send_email_cs(user_memory)

            return AgentResponse(
                type="message",
                content="The user has provided their contact information. You should thank them for their information.",
                instructions=[
                    Instruction(
                        content="Generate a response to thank the user for providing their contact information.",
                        examples=[
                            "Cảm ơn anh/chị đã cung cấp thông tin liên hệ. Bên em sẽ liên hệ lại với anh/chị trong thời gian sớm nhất. Trong thời gian chờ đợi bạn có thể xem các sản phẩm khác hoặc liên hệ {hotline} để được hỗ trợ nhanh nhất.",
                        ],
                    )
                ],
            )

        if len(invalid_infos) > 0:
            return AgentResponse(
                type="message",
                content="Contact information that the user provides is invalid.",
                instructions=[
                    Instruction(
                        content=f"The information about the {'' and ''.join(invalid_infos)} provided by the user might be invalid. You should politely ask them to provide this information again.",
                        examples=[
                            "Thông tin liên lạc anh/chị cung cấp có vẻ chưa hợp lệ. Anh/chị có thể gửi qua đây lại giúp em với được không ạ?",
                        ],
                    )
                ],
            )

        return AgentResponse(
            type="finished",
            content="The user request has been successfully processed.",
        )

    def _send_email_cs(self, user_memory: UserMemoryModel):
        email = create_message(
            sender=env.SENDER_EMAIL,
            to=env.RECEIVER_EMAIL,
            subject=f"{user_memory.phone_number} - Người dùng cần hỗ trợ",
            message_text=(
                "Người dùng cần hỗ trợ với.\n"
                f"Số điện thoại: {user_memory.phone_number}\n"
                f"Email: {user_memory.email}\n"
                f"Reference: {env.CHAINLIT_HOST}:{env.CHAINLIT_PORT}/thread/{user_memory.thread_id}\n"
            ),
        )
        queue = Queue(connection=redis)
        queue.enqueue(send_message, email)

    @weave.op(name="detect_demand_agent.post_process")
    def post_process(
        self,
        response: AgentResponse,
        user_memory: UserMemoryModel,
    ) -> AgentResponse:
        if response.type == "message":
            knowledge = []
            user_contact_info = (
                f"   - Phone number: {user_memory.phone_number}\n"
                if user_memory.phone_number
                else ""
            ) + (f"   - Email: {user_memory.email}\n" if user_memory.email else "")

            if user_contact_info:
                knowledge = [f"- The user's contact information:\n{user_contact_info}"]

            finished_response = generate_response_by_instructions(
                instructions=response.instructions,
                knowledge=knowledge,
                conversation_history=[],
                model=self.model,
            )

            return AgentResponse(
                type="message",
                content=finished_response,
            )

        return response

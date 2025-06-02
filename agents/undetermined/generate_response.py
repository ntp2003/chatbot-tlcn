from datetime import datetime
from typing import Literal, Optional
from overrides import override
from pydantic import BaseModel, Field
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from models.faq import FAQModel
from service.openai import OpenAIChatCompletionsRequest, _client, _chat_model, _fine_tuning_model
from openai.types.chat_model import ChatModel
from agents.base import (
    Agent as AgentBase,
    Instruction,
    SystemPromptConfig as SystemPromptConfigBase,
    AgentTemporaryMemory as AgentTemporaryMemoryBase,
    AgentResponseBase,
)
from models.user_memory import ProductType, UserMemory, UserMemoryModel
from service.faq import search as search_faq


class SystemPromptConfig(SystemPromptConfigBase):
    role: str = (
        "You are professional sales consultant staff for a online store (that provides technology products) in Vietnam."
    )

    task: str = (
        "Your task is to assist users in selecting suitable products and providing guidance on purchasing procedures."
    )
    skills: list[str] = [
        "Clear and concise communication - ability to explain solutions, policies, and procedures in easy-to-understand language",
        "Problem-solving abilities - quickly identifying customer issues and providing appropriate solutions or workarounds",
        "Empathy and patience - maintaining a helpful attitude when dealing with frustrated customers and complex situations",
        "Efficiency - resolving issues promptly while balancing thoroughness with speed to minimize customer wait times",
    ]
    base_knowledge: list[str] = [
        (
            "Information about your store:\n"
            "   - Name: FPTShop\n"
            "   - Location: https://fptshop.com.vn/cua-hang\n"
            "   - Hotline: 1800.6601\n"
            "   - Website: [FPTShop](https://fptshop.com.vn)\n"
            "   - Customer service email: cskh@fptshop.com\n"
        ),
        f"Current date: {datetime.now().strftime('%A, %B %d, %Y')} ({datetime.now().strftime('%Y-%m-%d')})",
    ]
    rules: list[str] = [
        "Don't talk nonsense and make up facts.",
        #"Use only the Vietnamese language in your responses.",
        "Use only the Vietnamese language in your response. Always refer to yourself using 'em' pronoun. Address the user based on how they refer to themselves . If their preferred address term cannot be determined from their self-reference, then base it on their provided <User gender>: use 'anh' for male, 'chị' for female. If the gender is unknown or not provided, use the polite neutral term 'anh/chị'."
    ]
    working_steps: list[str] = [
        (
            "**Step 1:** Read carefully the latest user message and the context provided by the user."
        ),
        (
            "**Step 2:** Suggest some types of products that the user might be interested in.\n"
            "example: 'Anh/chị có cần hỗ trợ gì không ạ? Hiện bên em có một số loại sản phẩm như: điện thoại, laptop,...'"
        ),
    ]

    initialization: str = (
        "As a/an <ROLE>, you are required to adhere to the <WORKFLOW> and follow the <RULES> strictly, using your expertise in <SKILLS> to do your task effectively."
    )
    '''
    conversation_tone: str = (
        "Always refer to yourself using 'em' pronoun. Address the user based on how they refer to themselves . If their preferred address term cannot be determined from their self-reference, then base it on their provided <User gender>: use 'anh' for male, 'chị' for female. If the gender is unknown or not provided, use the polite neutral term 'anh/chị'."
    )
    '''

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


class AgentResponse(AgentResponseBase):
    pass


class Agent(AgentBase):
    def __init__(
        self,
        system_prompt_config: SystemPromptConfig = SystemPromptConfig(),
        model: ChatModel = _chat_model,
        temporary_memory: AgentTemporaryMemory = AgentTemporaryMemory(),
    ):
        self.system_prompt_config = system_prompt_config
        self.model = model
        self.temporary_memory = temporary_memory

    @override
    def run(
        self, conversation_messages: list[ChatCompletionMessageParam], *args, **kwargs
    ) -> AgentResponseBase:
        """
        Run the agent to generate a response based on the conversation messages.
        """
        user_memory = self.temporary_memory.user_memory
        if not user_memory or user_memory.intent.product_type not in [
            None,
            ProductType.UNDETERMINED,
        ]:
            return AgentResponse(type="message", content="No valid user memory found.")

        latest_user_message = next(
            (msg for msg in reversed(conversation_messages) if msg["role"] == "user"),
            None,
        )

        if not latest_user_message or not latest_user_message["content"]:
            return AgentResponse(type="message", content="No valid user message found.")

        faqs = self.retrieval_faq(str(latest_user_message["content"]))

        if faqs:
            self.system_prompt_config.base_knowledge.append(
                f"Some frequently asked questions (FAQs) in the store:\n"
                + (
                    "\n".join(
                        [
                            (
                                f"   - Question {i + 1}: {faq.question}\n"
                                f"Answer: {faq.answer}"
                            )
                            for i, faq in enumerate(faqs)
                        ]
                    )
                )
            )
            self.system_prompt_config.rules.append(
                "If the latest user message is a question related to the FAQs, you should answer it based on the FAQs. Else, you should answer it based on the other BASE KNOWLEDGE and don't use the FAQs."
            )

        self.temporary_memory.chat_completions_messages = (
            self.system_prompt_config.get_openai_messages(
                conversation_messages=conversation_messages
            )
        )

        openai_request = self._get_openai_request()
        response = openai_request.create()
        response_message = response.choices[0].message

        if not response_message.content:
            return AgentResponse(
                type="message", content="No content in response message."
            )

        return AgentResponse(
            type="finished",
            content=response_message.content,
        )

    def _get_openai_request(
        self,
    ) -> OpenAIChatCompletionsRequest:
        return OpenAIChatCompletionsRequest(
            messages=self.temporary_memory.chat_completions_messages,
            #model=self.model,
            model=_fine_tuning_model,
            temperature=0,
            timeout=60,
        )

    def retrieval_faq(self, question: str) -> list[FAQModel]:
        """
        Retrieve FAQs based on the question.
        """

        faqs = search_faq(question)

        return faqs

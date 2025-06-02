from enum import Enum
import json
from typing import Optional
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from models.laptop import LaptopModel
from uuid import uuid4
from models.thread import ThreadModel
from models.user import UserModel, UserRole
from repositories.user import create as create_user, CreateUserModel
from repositories.thread import create as create_thread, CreateThreadModel
from service.store_chatbot_v2 import gen_answer
from service.openai import _client
import random
import math
from deepeval.test_case.llm_test_case import LLMTestCase
from deepeval.test_case.conversational_test_case import ConversationalTestCase
from repositories.laptop import get_all
from utils import EvaluateContext
from service.wandb import *
import deepeval.models.llms.openai_model as deepeval_models
import weave
from deepeval.metrics.role_adherence.role_adherence import RoleAdherenceMetric
from deepeval.metrics.faithfulness.faithfulness import FaithfulnessMetric
from weave.flow.eval import Evaluation
from weave.flow.dataset import Dataset
import asyncio

gpt_41_mini = deepeval_models.GPTModel(
    model="gpt-4.1-mini",
    timeout=60,
)


class Step(str, Enum):
    GREETING_AND_PROVIDE_NEED = "greeting and provide needs about the laptop"
    SEARCH_LAPTOP_BASE_ON_THE_BRAND = "search laptop base on the brand"
    SEARCH_LAPTOP_BASE_ON_THE_PRICE = "search laptop base on the price"
    SEARCH_LAPTOP_BASE_ON_THE_PURPOSE = "search laptop base on the purpose"
    SELECT_ONE_LAPTOP_FROM_THE_LIST = "select one laptop from the list"
    ASK_FOR_THE_DETAILS_OF_THE_SELECTED_LAPTOP = (
        "ask for the details of the selected laptop"
    )
    PROVIDE_PHONE_NUMBER = "provide phone number"
    PROVIDE_EMAIL = "provide email"


class VietnameseLaptopUserSimulator(BaseModel):
    laptop: LaptopModel
    name: str = "Nguyen Van A"  # Default name, will be overwritten
    age: int = 30  # Default age, will be overwritten
    gender: str = "male"  # Default
    phone_number: str = "0912345678"  # Default phone number, will be overwritten
    email: str = "ntp@gmail.com"  # Default email, will be overwritten
    purpose: str = "work"  # Default purpose for laptop

    min_budget: int = 0
    max_budget: int = (
        100000000  # Default budget range, will be calculated based on laptop price
    )

    basic_laptop_info: str = ""
    full_laptop_info: str = ""

    response_format: Optional[ResponseFormat] = None  # Will be set in init method
    step_history: list[Step] = []
    conversation_history: list[ChatCompletionMessageParam] = []
    user: Optional[UserModel] = None  # Will be created in init method
    thread: Optional[ThreadModel] = None  # Will be created in init method
    llm_test_cases: list[LLMTestCase] = []

    def init(self):
        user_info = self.generate_user_info()

        print(f"Generated user info: {user_info}")
        self.name = user_info["name"]
        self.age = user_info["age"]
        self.gender = user_info["gender"]
        self.phone_number = user_info["phone_number"]
        self.email = user_info["email"]
        self.purpose = user_info["purpose"]

        # Calculate raw budget values
        raw_min_budget = min(self.laptop.price * 0.9, self.laptop.price - 2000000)
        if raw_min_budget < 0:
            raw_min_budget = 0
        raw_max_budget = max(self.laptop.price * 1.1, 0, self.laptop.price + 2000000)

        # Round to millions
        self.min_budget = math.floor(raw_min_budget / 1000000) * 1000000
        self.max_budget = math.ceil(raw_max_budget / 1000000) * 1000000

        print(f"Rounded budget range: {self.min_budget:,} - {self.max_budget:,} VND")

        self.basic_laptop_info = (
            self.laptop.to_text(include_key_selling_points=True)
            + f"- Brand: {self.laptop._get_brand_name()}"
        )
        self.full_laptop_info = self.laptop.to_text(True, True, True, True)
        self.response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "Response",
                "description": "Response from you to the latest user message.",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "response_message": {
                            "type": "string",
                            "description": "Response message for the latest user message. It can be a question or a statement. It should be concise and in Vietnamese.",
                        },
                        "current_step_for_step": {
                            "type": "string",
                            "enum": [step.value for step in Step],
                            "description": "Current step of the response message. It should be one of the steps in the Step enum and match the current step of the conversation.",
                        },
                    },
                    "additionalProperties": False,
                    "required": ["current_step_for_step", "response_message"],
                },
            },
        }
        self.step_history: list[Step] = []
        self.conversation_history: list[ChatCompletionMessageParam] = []
        self.user = create_user(
            CreateUserModel(
                user_name=str(uuid4()), role=UserRole.chainlit_user, gender=self.gender
            )
        )
        self.thread = create_thread(
            CreateThreadModel(id=uuid4(), user_id=self.user.id, name=self.name)
        )
        self.llm_test_cases: list[LLMTestCase] = []

    def generate_user_info(self) -> dict:
        """Generate diverse and random Vietnamese user information with laptop purposes"""
        # ...existing code for name generation (same as phone)...

        # Laptop-specific purposes
        purposes = [
            "work",
            "gaming",
            "study",
            "design",
            "programming",
            "office work",
            "video editing",
            "general use",
            "business",
        ]

        # Generate purpose based on age
        if self.age < 25:
            purpose_weights = [0.2, 0.3, 0.4, 0.05, 0.05]  # More gaming and study
        elif self.age < 40:
            purpose_weights = [0.4, 0.2, 0.1, 0.15, 0.15]  # More work and design
        else:
            purpose_weights = [0.5, 0.1, 0.05, 0.1, 0.25]  # More work and office

        purpose = random.choices(purposes[:5], weights=purpose_weights)[0]

        # Use existing phone generation logic for basic info
        user_info = self._generate_basic_user_info()
        user_info["purpose"] = purpose

        return user_info

    def _generate_basic_user_info(self) -> dict:
        """Generate basic user info (reuse from phone simulator)"""
        # Vietnamese surnames (họ)
        surnames = [
            "Nguyễn",
            "Trần",
            "Lê",
            "Phạm",
            "Hoàng",
            "Huỳnh",
            "Phan",
            "Vũ",
            "Võ",
            "Đặng",
            "Bùi",
            "Đỗ",
            "Hồ",
            "Ngô",
            "Dương",
            "Lý",
            "Mai",
            "Đinh",
            "Lưu",
            "Đào",
            "Chu",
            "Cao",
            "Thái",
            "Tô",
            "Triệu",
            "Hà",
            "Lâm",
            "Vương",
            "Trịnh",
            "Quách",
        ]

        # Vietnamese middle names (tên đệm)
        male_middle_names = [
            "Văn",
            "Minh",
            "Quang",
            "Đức",
            "Hữu",
            "Thành",
            "Tuấn",
            "Duy",
            "Thanh",
            "Hoàng",
            "Anh",
            "Công",
            "Đình",
            "Xuân",
            "Bảo",
            "Hải",
            "Tiến",
            "Nam",
            "Tài",
            "Khang",
        ]

        female_middle_names = [
            "Thị",
            "Thu",
            "Minh",
            "Thanh",
            "Ngọc",
            "Hồng",
            "Thúy",
            "Kim",
            "Phương",
            "Lan",
            "Hương",
            "Mai",
            "Linh",
            "Trang",
            "Diệu",
            "Khánh",
            "Bích",
            "Yến",
            "Như",
            "Ái",
        ]

        # Vietnamese given names (tên)
        male_given_names = [
            "Anh",
            "Bảo",
            "Cường",
            "Dũng",
            "Đức",
            "Giang",
            "Hải",
            "Hiếu",
            "Hùng",
            "Khôi",
            "Long",
            "Minh",
            "Nam",
            "Phong",
            "Quân",
            "Sơn",
            "Tài",
            "Thắng",
            "Tuấn",
            "Việt",
            "Hoàng",
            "Kiên",
            "Linh",
            "Nghĩa",
            "Phúc",
            "Thiên",
            "Tùng",
            "Vinh",
            "Xuân",
            "Yên",
        ]

        female_given_names = [
            "Anh",
            "Bảo",
            "Chi",
            "Dung",
            "Giang",
            "Hà",
            "Hạnh",
            "Hương",
            "Lan",
            "Linh",
            "Mai",
            "Ngọc",
            "Phương",
            "Quỳnh",
            "Thảo",
            "Thu",
            "Trang",
            "Tuyết",
            "Uyên",
            "Yến",
            "Diệu",
            "Hạ",
            "Khánh",
            "Lý",
            "My",
            "Nhi",
            "Oanh",
            "Thùy",
            "Vân",
            "Xuân",
        ]

        # Phone number prefixes for different carriers
        phone_prefixes = [
            "032",
            "033",
            "034",
            "035",
            "036",
            "037",
            "038",
            "039",  # Viettel
            "070",
            "079",
            "077",
            "076",
            "078",  # Mobifone
            "083",
            "084",
            "085",
            "081",
            "082",  # Vinaphone
            "056",
            "058",  # Vietnamobile
            "092",
            "094",
            "088",  # Gmobile
        ]

        # Email domains
        email_domains = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "yandex.com",
            "icloud.com",
            "protonmail.com",
            "tutanota.com",
            "zoho.com",
            "mail.com",
        ]

        # Generate gender first to determine name pattern
        gender = random.choice(["male", "female"])

        # Generate name based on gender
        surname = random.choice(surnames)
        if gender == "male":
            middle_name = random.choice(male_middle_names)
            given_name = random.choice(male_given_names)
        else:
            middle_name = random.choice(female_middle_names)
            given_name = random.choice(female_given_names)

        # Sometimes skip middle name for more diversity
        if random.random() < 0.3:  # 30% chance to skip middle name
            full_name = f"{surname} {given_name}"
        else:
            full_name = f"{surname} {middle_name} {given_name}"

        # Generate age with weighted distribution (more young adults)
        age_ranges = [(18, 25, 0.3), (26, 35, 0.4), (36, 45, 0.2), (46, 65, 0.1)]
        age_range = random.choices(age_ranges, weights=[w for _, _, w in age_ranges])[0]
        age = random.randint(age_range[0], age_range[1])

        # Generate phone number
        prefix = random.choice(phone_prefixes)
        remaining_digits = "".join([str(random.randint(0, 9)) for _ in range(7)])
        phone_number = f"0{prefix[1:]}{remaining_digits}"

        # Generate email with various patterns
        email_patterns = [
            lambda: f"{given_name.lower()}.{surname.lower()}",
            lambda: f"{given_name.lower()}{surname.lower()}",
            lambda: f"{surname.lower()}.{given_name.lower()}",
            lambda: f"{given_name.lower()}{random.randint(1990, 2005)}",
            lambda: f"{surname.lower()}{given_name.lower()}{random.randint(10, 99)}",
            lambda: f"{given_name.lower()}_{surname.lower()}",
        ]

        email_pattern = random.choice(email_patterns)
        email_username = email_pattern()
        # Remove Vietnamese accents for email
        email_username = self._remove_accents(email_username)
        email_domain = random.choice(email_domains)
        email = f"{email_username}@{email_domain}"

        return {
            "name": full_name,
            "age": age,
            "gender": gender,
            "phone_number": phone_number,
            "email": email,
        }

    def _remove_accents(self, text: str) -> str:
        """Remove Vietnamese accents from text for email generation"""
        accent_map = {
            "à": "a",
            "á": "a",
            "ạ": "a",
            "ả": "a",
            "ã": "a",
            "â": "a",
            "ầ": "a",
            "ấ": "a",
            "ậ": "a",
            "ẩ": "a",
            "ẫ": "a",
            "ă": "a",
            "ằ": "a",
            "ắ": "a",
            "ặ": "a",
            "ẳ": "a",
            "ẵ": "a",
            "è": "e",
            "é": "e",
            "ẹ": "e",
            "ẻ": "e",
            "ẽ": "e",
            "ê": "e",
            "ề": "e",
            "ế": "e",
            "ệ": "e",
            "ể": "e",
            "ễ": "e",
            "ì": "i",
            "í": "i",
            "ị": "i",
            "ỉ": "i",
            "ĩ": "i",
            "ò": "o",
            "ó": "o",
            "ọ": "o",
            "ỏ": "o",
            "õ": "o",
            "ô": "o",
            "ồ": "o",
            "ố": "o",
            "ộ": "o",
            "ổ": "o",
            "ỗ": "o",
            "ơ": "o",
            "ờ": "o",
            "ớ": "o",
            "ợ": "o",
            "ở": "o",
            "ỡ": "o",
            "ù": "u",
            "ú": "u",
            "ụ": "u",
            "ủ": "u",
            "ũ": "u",
            "ư": "u",
            "ừ": "u",
            "ứ": "u",
            "ự": "u",
            "ử": "u",
            "ữ": "u",
            "ỳ": "y",
            "ý": "y",
            "ỵ": "y",
            "ỷ": "y",
            "ỹ": "y",
            "đ": "d",
            # Uppercase versions
            "À": "A",
            "Á": "A",
            "Ạ": "A",
            "Ả": "A",
            "Ã": "A",
            "Â": "A",
            "Ầ": "A",
            "Ấ": "A",
            "Ậ": "A",
            "Ẩ": "A",
            "Ẫ": "A",
            "Ă": "A",
            "Ằ": "A",
            "Ắ": "A",
            "Ặ": "A",
            "Ẳ": "A",
            "Ẵ": "A",
            "È": "E",
            "É": "E",
            "Ẹ": "E",
            "Ẻ": "E",
            "Ẽ": "E",
            "Ê": "E",
            "Ề": "E",
            "Ế": "E",
            "Ệ": "E",
            "Ể": "E",
            "Ễ": "E",
            "Ì": "I",
            "Í": "I",
            "Ị": "I",
            "Ỉ": "I",
            "Ĩ": "I",
            "Ò": "O",
            "Ó": "O",
            "Ọ": "O",
            "Ỏ": "O",
            "Õ": "O",
            "Ô": "O",
            "Ồ": "O",
            "Ố": "O",
            "Ộ": "O",
            "Ổ": "O",
            "Ỗ": "O",
            "Ơ": "O",
            "Ờ": "O",
            "Ớ": "O",
            "Ợ": "O",
            "Ở": "O",
            "Ỡ": "O",
            "Ù": "U",
            "Ú": "U",
            "Ụ": "U",
            "Ủ": "U",
            "Ũ": "U",
            "Ư": "U",
            "Ừ": "U",
            "Ứ": "U",
            "Ự": "U",
            "Ử": "U",
            "Ữ": "U",
            "Ỳ": "Y",
            "Ý": "Y",
            "Ỵ": "Y",
            "Ỷ": "Y",
            "Ỹ": "Y",
            "Đ": "D",
        }

        result = ""
        for char in text:
            result += accent_map.get(char, char)
        return result

    def extract_asked_topics(self) -> list[str]:
        """Extract topics that the user has already asked about using OpenAI API"""
        # If no conversation yet, return empty list
        if len(self.conversation_history) < 2:
            return []

        # Create a format for the response
        topic_format: ResponseFormat = {
            "type": "json_schema",
            "json_schema": {
                "name": "AskedTopics",
                "description": "Topics that the user has already asked about in the conversation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of topics that have been asked about in the conversation",
                        }
                    },
                    "additionalProperties": False,
                    "required": ["topics"],
                },
            },
        }

        # Get only the last few messages to avoid token limits
        recent_messages = (
            self.conversation_history[-10:]
            if len(self.conversation_history) > 10
            else self.conversation_history
        )

        # Create the prompt for OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are an assistant that analyzes conversation history to identify what topics a customer has already asked about regarding a laptop. Extract key topics the customer has asked about such as performance, graphics, battery life, price, specs, etc.",
            },
            {
                "role": "user",
                "content": f"Here is a conversation between a customer and a laptop store assistant. Identify what specific topics about the laptop the customer has already asked about in these messages:\n\n"
                + "\n".join(
                    [
                        f"{'Customer' if msg['role'] == 'assistant' else 'Assistant'}: {msg.get('content', '')}"
                        for msg in recent_messages
                    ]
                ),
            },
        ]

        try:
            response = _client.chat.completions.create(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.3,
                response_format=topic_format,
                timeout=60,
            )

            result = json.loads(response.choices[0].message.content or "{}")
            topics = result.get("topics", [])
            return topics[:10]  # Limit to 10 topics
        except Exception as e:
            print(f"Error extracting topics: {e}")
            # Fallback to basic topic extraction
            return ["general laptop information"]

    def suggest_new_topics(self, asked_topics: list[str]) -> list[str]:
        """Suggest topics that haven't been asked about yet using OpenAI API"""
        # Setup the response format
        topic_format: ResponseFormat = {
            "type": "json_schema",
            "json_schema": {
                "name": "SuggestedTopics",
                "description": "Topics that could be asked about the laptop",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "suggested_topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of suggested topics about the laptop that haven't been asked yet",
                        }
                    },
                    "additionalProperties": False,
                    "required": ["suggested_topics"],
                },
            },
        }

        # Create the prompt for OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are an assistant that suggests relevant topics a customer could ask about a laptop. Given the laptop details and topics already asked, suggest new topics that would be helpful for making a purchase decision.",
            },
            {
                "role": "user",
                "content": f"Laptop information:\n{self.full_laptop_info}\n\nTopics already asked about:\n{', '.join(asked_topics)}\n\nSuggest 5 other relevant topics the customer could ask about this laptop that haven't been covered yet.",
            },
        ]

        try:
            response = _client.chat.completions.create(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.7,
                response_format=topic_format,
                timeout=60,
            )

            result = json.loads(response.choices[0].message.content or "{}")
            suggested_topics = result.get("suggested_topics", [])
            return suggested_topics[:5]  # Limit to 5 topics
        except Exception as e:
            print(f"Error suggesting topics: {e}")
            # Fallback to some generic topics
            return [
                "performance specs",
                "warranty policy",
                "accessories",
                "user experience",
                "purchase options",
            ]

    def get_next_user_message(self) -> str:
        latest_step_in_past = self.step_history[-1] if self.step_history else None

        # Add special guidance for Step 6 to help generate diverse questions
        if latest_step_in_past == Step.ASK_FOR_THE_DETAILS_OF_THE_SELECTED_LAPTOP:
            asked_topics = self.extract_asked_topics()
            if asked_topics:
                suggested_topics = self.suggest_new_topics(asked_topics)

        messages: list[ChatCompletionMessageParam] = [
            *self.get_system_prompt(),
            *self.conversation_history,
        ]
        response = _client.chat.completions.create(
            messages=messages,
            model="gpt-4.1-mini",
            temperature=0.7,
            timeout=30,
            response_format=self.response_format,
        )
        response_message = response.choices[0].message.content
        parsed_information = json.loads(response_message or "{}")
        print(
            f"Response: {parsed_information} in turn {len(self.conversation_history) + 1}"
        )
        current_step_for_step = parsed_information.get("current_step_for_step")
        response_message = parsed_information.get("response_message")
        if current_step_for_step and response_message:
            self.step_history.append(Step(current_step_for_step))
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response_message,
                }
            )

            evaluate_context = EvaluateContext()
            assistant_response = gen_answer(
                user_id=self.user.id,
                thread_id=self.thread.id,
                history=self.get_reversed_role_in_conversation_history(),
                evaluate_context=evaluate_context,
            )

            self.conversation_history.append(
                {
                    "role": "user",
                    "content": assistant_response,
                }
            )
            self.llm_test_cases.append(
                LLMTestCase(
                    input=response_message,
                    actual_output=assistant_response,
                    retrieval_context=evaluate_context.knowledge,
                    additional_metadata=evaluate_context.model_dump(),
                )
            )
            return response_message
        else:
            raise ValueError("Invalid response format")

    def get_reversed_role_in_conversation_history(
        self,
    ) -> list[ChatCompletionMessageParam]:
        reversed_history = []
        for message in self.conversation_history:
            # Only include messages that have a 'content' key
            if "content" in message and "role" in message:
                reversed_history.append(
                    {
                        "role": (
                            "user" if message["role"] == "assistant" else "assistant"
                        ),
                        "content": message["content"],
                    }
                )
        return reversed_history

    def simulate_conversation(self, max_turns: int = 20):
        """Simulate laptop purchasing conversation"""
        if not self.conversation_history:
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": "Xin chào, bạn cần hỗ trợ gì ạ?",
                }
            )
        for _ in range(max_turns):
            self.get_next_user_message()
            if (
                self.step_history[-1] == Step.PROVIDE_EMAIL
                or self.step_history[-1] == Step.PROVIDE_PHONE_NUMBER
            ):
                print(f"User {self.name} has provided their contact information.")
                break
        for message in self.conversation_history:
            print(f"{message['role']}: {message.get('content')}")
        for step in self.step_history:
            print(f"Step: {step.value}")

    def get_system_prompt(self) -> list[ChatCompletionMessageParam]:
        role = (
            "# ROLE\n"
            "You are a Vietnamese virtual user playing the role of a customer searching for a new laptop. You are chatting with an online customer service agent.\n"
        )
        profile = (
            f"## PROFILE\n"
            f"- Name: {self.name}\n"
            f"- Age: {self.age}\n"
            f"- Gender: {self.gender}\n"
            f"- Phone number: {self.phone_number}\n"
            f"- Email: {self.email}\n"
            f"- Purpose: {self.purpose}\n"
            f"- Min budget: {self.min_budget}\n"
            f"- Max budget: {self.max_budget}\n"
        )

        latest_step_in_past = self.step_history[-1] if self.step_history else None

        laptop_looking_for = (
            (f"## INFORMATION ABOUT LAPTOP LOOKING FOR\n" f"{self.basic_laptop_info}\n")
            if latest_step_in_past
            in [
                Step.GREETING_AND_PROVIDE_NEED,
                Step.SEARCH_LAPTOP_BASE_ON_THE_BRAND,
                Step.SEARCH_LAPTOP_BASE_ON_THE_PRICE,
                Step.SEARCH_LAPTOP_BASE_ON_THE_PURPOSE,
                Step.SELECT_ONE_LAPTOP_FROM_THE_LIST,
            ]
            else (
                f"## INFORMATION ABOUT LAPTOP LOOKING FOR\n"
                f"{self.full_laptop_info}\n"
            )
        )

        step_descriptions = (
            "## STEP DESCRIPTIONS\n"
            f"1. **{Step.GREETING_AND_PROVIDE_NEED.value}**: Greet the customer support agent and provide your needs about the laptop. Example: 'Mình cần tư vấn laptop', 'Hello', 'Mình cần mua laptop tầm {self.min_budget} đến {self.max_budget} VNĐ', 'Xin chào', 'Tôi cần một chiếc laptop mới cho {self.purpose}'.\n"
            f"2. **{Step.SEARCH_LAPTOP_BASE_ON_THE_BRAND.value}**: Search for a laptop based on the brand. Example: 'Tìm laptop {self.laptop._get_brand_name()}', 'Tìm laptop thương hiệu {self.laptop._get_brand_name()}', '{self.laptop._get_brand_name()}', 'hãng {self.laptop._get_brand_name()}'.\n"
            f"3. **{Step.SEARCH_LAPTOP_BASE_ON_THE_PRICE.value}**: Search for a laptop based on the price. Example: 'Tìm laptop dưới {self.max_budget} VNĐ', 'Tìm laptop giá {self.min_budget} đến {self.max_budget} VNĐ'.\n"
            f"4. **{Step.SEARCH_LAPTOP_BASE_ON_THE_PURPOSE.value}**: Search for a laptop based on the purpose. Example: 'Tìm laptop cho {self.purpose}', 'laptop dành cho {self.purpose}', 'laptop {self.purpose}'.\n"
            f"5. **{Step.SELECT_ONE_LAPTOP_FROM_THE_LIST.value}**: Select one laptop from the suggested list in past. Example: 'Chọn laptop {self.laptop.name} trong danh sách', 'Chọn laptop {self.laptop.name}', 'cái đầu', 'mẫu số 2'.\n"
            f"6. **{Step.ASK_FOR_THE_DETAILS_OF_THE_SELECTED_LAPTOP.value}**: Ask for the details of the selected laptop by analyzing the information in the <INFORMATION ABOUT LAPTOP LOOKING FOR> section. Extract key specifications, features, and selling points from this section, and formulate natural, relevant questions about these aspects. Generate diverse questions that someone would genuinely ask when considering purchasing this specific laptop model. Vary your questions between technical specifications, features, promotions, colors, accessories, user experience, and purchase conditions.\n"
            f"7. **{Step.PROVIDE_PHONE_NUMBER.value}**: Provide your phone number when you need further consultation or are ready to purchase. Example: 'Số điện thoại của mình là {self.phone_number}'.\n"
            f"8. **{Step.PROVIDE_EMAIL.value}**: Provide your email. Example: 'Email của mình là {self.email}'.\n"
        )

        if latest_step_in_past:
            count = 0
            for step in reversed(self.step_history):
                if step == latest_step_in_past:
                    count += 1
                else:
                    break

            # Add special guidance for Step 6 to help generate diverse questions
            if latest_step_in_past == Step.ASK_FOR_THE_DETAILS_OF_THE_SELECTED_LAPTOP:
                asked_topics = self.extract_asked_topics()
                if asked_topics:
                    suggested_topics = self.suggest_new_topics(asked_topics)
                    step_descriptions += (
                        "\n## QUESTION HISTORY AND SUGGESTIONS\n"
                        f"You have already asked about: {', '.join(asked_topics)}.\n"
                        f"Consider asking about new topics such as: {', '.join(suggested_topics)}.\n"
                    )

            step_descriptions += (
                "\n## LATEST STEP IN PAST\n"
                f"Latest step in past: {latest_step_in_past.value}\n"
                f"Stay at step {latest_step_in_past.value} for {count} turns.\n"
            )

        task = (
            "## TASK\n"
            "Generate a response message for the latest user message based on the current step of the conversation. It's like talking to a real customer service agent."
        )

        guidelines = (
            "## GUIDELINES\n"
            "1. The response message should be in Vietnamese.\n"
            "2. When starting the conversation, greet the customer support agent and provide your needs about the laptop. (Step 1)\n"
            "3. If the user asks for the type of product that you are looking for, provide the type of product that you are looking for is a laptop.\n"
            f"4. If the user asks for the brand of the laptop that you are looking for, provide the brand of the laptop that you are looking for is {self.laptop._get_brand_name()} (Step 2).\n"
            f"5. If the user asks for the price of the laptop that you are looking for, provide the price of the laptop that you are looking for is between {self.min_budget} and {self.max_budget} (Step 3).\n"
            f"6. If the user asks for the purpose of the laptop, provide the purpose is {self.purpose} (Step 4).\n"
            f"7. If the user provides a list of laptops and has a laptop that you are looking for ({self.laptop.name}), select that laptop from the list (Step 5).\n"
            "8. If the user provides the details of the selected laptop and asks your contact information, ask for the details of the selected laptop (Step 6).\n"
            "9. If the user provides the details of the selected laptop and the latest step in past is Step 6, provide your phone number or email (Step 7 or Step 8).\n"
            "\n## NOTE:\n"
            "- Imagine you are a real customer who has just interacted with a business. Your response should sound natural and authentic.\n"
            "- You need to stay at the Step 6 minimum 2 turns and maximum 4 turns before moving to Step 7 or Step 8.\n"
            f"- If you can't find the laptop ({self.laptop.name}) in the list of laptops suggested by the customer service agent, you can ask for other laptops (e.g., 'Có mẫu nào khác không?'). "
            "If still unavailable, then provide your contact information (Step 7 or Step 8).\n"
        )

        return [
            {"role": "system", "content": role + "\n" + profile},
            {"role": "system", "content": laptop_looking_for},
            {"role": "system", "content": step_descriptions},
            {"role": "system", "content": task},
            {"role": "system", "content": guidelines},
        ]


@weave.op(name="get_simulated_laptop_user")
def get_simulated_laptop_user(laptop: LaptopModel) -> str:
    """Get a simulated Vietnamese user for the given laptop"""
    simulate_user = VietnameseLaptopUserSimulator(laptop=laptop)
    simulate_user.init()
    simulate_user.simulate_conversation()
    print(f"Simulated user for {laptop.name} has finished the conversation.")
    return simulate_user.model_dump_json()


@weave.op(name=f"evaluate_laptop_conversation")
def evaluate_laptop_conversation(
    output: VietnameseLaptopUserSimulator,
) -> dict:
    """Evaluate the laptop conversation of the simulated user"""
    faithfulness_metric = FaithfulnessMetric(threshold=0.5, model=gpt_41_mini)
    role_adherence_metric = RoleAdherenceMetric(threshold=0.5, model=gpt_41_mini)
    faithfulness_scrores = []
    role_adherence_scores = []

    for llm_test_case in output.llm_test_cases:
        retrieval_context = (
            "\n\n".join(llm_test_case.retrieval_context)
            if llm_test_case.retrieval_context
            else ""
        )

        instruction = (
            llm_test_case.additional_metadata.get("instruction", "")
            if llm_test_case.additional_metadata
            else ""
        )

        chatbot_role = f"""
        # ROLE
        You are professional sales consultant staff for a laptop store.

        {retrieval_context}

        {instruction}

        ## TASK
        Your task is to assist users in selecting suitable laptops and providing guidance on purchasing procedures.
        Base on <INSTRUCTIONS> to provide the response for user.
        """

        convo_test_case = ConversationalTestCase(
            chatbot_role=chatbot_role, turns=[llm_test_case]
        )
        faiithfullness_test_case = LLMTestCase(
            input=llm_test_case.input,
            actual_output=llm_test_case.actual_output,
            retrieval_context=(
                (llm_test_case.retrieval_context or []) + [instruction]
                if instruction
                else []
            ),
        )
        role_adherence_scores.append(role_adherence_metric.measure(convo_test_case))
        faithfulness_scrores.append(
            faithfulness_metric.measure(faiithfullness_test_case)
        )
    return {
        "faithfulness_score": (
            sum(faithfulness_scrores) / len(faithfulness_scrores)
            if faithfulness_scrores
            else 0
        ),
        "role_adherence_score": (
            sum(role_adherence_scores) / len(role_adherence_scores)
            if role_adherence_scores
            else 0
        ),
    }


@weave.op(name="create_laptop_dataset")
def create_laptop_dataset(limit: int = 5) -> Dataset:
    """Create a dataset of simulated Vietnamese users for laptop evaluation"""
    laptops = get_all()[:limit]

    dataset = Dataset(
        name="Laptop-Evaluation-Dataset",
        rows=weave.Table(
            [
                {
                    "laptop": laptop,
                    "simulated_user": get_simulated_laptop_user(laptop),
                }
                for laptop in laptops
            ]
        ),
        description="Dataset of simulated Vietnamese users for laptop evaluation",
    )
    weave.publish(dataset)
    return dataset


@weave.op(name="get_simulated_laptop_user_from_record")
def get_simulated_laptop_user_from_record(
    simulated_user,
) -> VietnameseLaptopUserSimulator:
    """Get a simulated laptop user from a dataset record"""
    return VietnameseLaptopUserSimulator.model_validate_json(simulated_user)


if __name__ == "__main__":
    try:
        dataset = weave.ref("Laptop-Evaluation-Dataset").get()
    except:
        print("Dataset not found, creating a new one...")
        dataset = create_laptop_dataset(limit=10)

    evaluation = Evaluation(
        name="Laptop Evaluation",
        dataset=dataset,
        scorers=[evaluate_laptop_conversation],
        evaluation_name="laptop_evaluation",
    )
    print("Starting laptop evaluation...")
    print(f"Dataset: {dataset.name}")
    print(f"Number of laptops: {len(dataset.rows)}")
    print("Evaluating...")
    asyncio.run(evaluation.evaluate(get_simulated_laptop_user_from_record))

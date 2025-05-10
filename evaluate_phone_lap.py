from uuid import uuid4
from models.user import UserRole
from repositories.user import create as create_user, CreateUserModel
from repositories.thread import create as create_thread, CreateThreadModel
from service.store_chatbot_v2 import gen_answer
import weave
from service.faq import search as search_faq
from service.phone import search as search_phone
from service.laptop import search as search_laptop
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    BaseMetric,
)
from deepeval import evaluate
from service.wandb import *
from weave.flow.eval import Evaluation
import asyncio
import deepeval.models as deepeval_models

#faq_dataset = weave.ref("20250502_210525").get()
phone_dataset = weave.ref("").get() # get test set from wandb

# format for retrieval context
#context_format = "Thông tin về câu hỏi và câu trả lời thường gặp của khách hàng tại FPT Shop:\nCâu hỏi: {question}\nCâu trả lời: {answer}\n"
context_format = "Thông tin về câu trả lời về điện thoại tại FPT Shop:\n Câu trả lời: {answer}\n"
gpt_4_1_mini = deepeval_models.GPTModel(
    model="gpt-4.1-mini",
    timeout=60,
)

# get actual response of chatbot to a given input
def get_actual_answer(input: str) -> str:
    user = create_user(
        CreateUserModel(user_name=str(uuid4()), role=UserRole.chainlit_user)
    )
    thread = create_thread(CreateThreadModel(user_id=user.id, name=user.user_name))

    return gen_answer(
        thread_id=thread.id,
        history=[{"role": "user", "content": str(input)}],
        user_id=user.id,
    )


@weave.op(name="get_phone_test_case") # tích hợp với weave
def get_phone_test_case(input: str, expected_output: str, context: list[str]) -> LLMTestCase:
    #faqs = search_faq(input)
    phones = search_phone(input) # tìm phone liên quan đến input
    actual_answer = get_actual_answer(input) # câu trả lời thực tế của chatbot
    test_case = LLMTestCase(
        input=str(input), # question
        expected_output=expected_output,
        actual_output=actual_answer,
        context=context,
        retrieval_context=[
            context_format.format(answer=phone.answer)
            for phone in phones
        ],
    ) # tạo tesst case với input, expected_output, actual_output, context và retrieval_context
    return test_case


@weave.op(name="evaluate_phone")
def evaluate_phone(input, output: LLMTestCase) -> dict:
    metrics: list[BaseMetric] = [
        ContextualPrecisionMetric(
            model=gpt_4_1_mini, include_reason=False, async_mode=False
        ),
        AnswerRelevancyMetric(
            model=gpt_4_1_mini, include_reason=False, async_mode=False
        ),
        FaithfulnessMetric(model=gpt_4_1_mini, include_reason=False, async_mode=False),
    ]
    # đánh giá response dựa trên 3 metric: ContextualPrecisionMetric, AnswerRelevancyMetric, FaithfulnessMetric

    results_dict = {}
    for metric in metrics:
        result = metric.measure(output)
        results_dict[metric.__class__.__name__] = result

    return results_dict


# khởi tạo và chạy evaluation
evaluation = Evaluation(
    name="Phone Evaluation",
    dataset=phone_dataset,
    scorers=[evaluate_phone], # hàm đánh giá
    evaluation_name="phone_evaluation",
)

asyncio.run(evaluation.evaluate(get_phone_test_case))

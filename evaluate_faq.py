from uuid import uuid4
from models.user import UserRole
from repositories.user import create as create_user, CreateUserModel
from repositories.thread import create as create_thread, CreateThreadModel
from service.store_chatbot_v2 import gen_answer
import weave
from service.faq import search as search_faq
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

faq_dataset = weave.ref("20250502_210525").get()
context_format = "Thông tin về câu hỏi và câu trả lời thường gặp của khách hàng tại FPT Shop:\nCâu hỏi: {question}\nCâu trả lời: {answer}\n"
gpt_4o_mini = deepeval_models.GPTModel(
    model="gpt-4.1-mini",
    timeout=60,
)


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


@weave.op(name="get_faq_test_case")
def get_test_case(input: str, expected_output: str, context: list[str]) -> LLMTestCase:
    faqs = search_faq(input)
    actual_answer = get_actual_answer(input)
    test_case = LLMTestCase(
        input=str(input),
        expected_output=expected_output,
        actual_output=actual_answer,
        context=context,
        retrieval_context=[
            context_format.format(question=faq.question, answer=faq.answer)
            for faq in faqs
        ],
    )
    return test_case


@weave.op(name="evaluate_faq")
def evaluate_faq(input, output: LLMTestCase) -> dict:
    metrics: list[BaseMetric] = [
        ContextualPrecisionMetric(
            model=gpt_4o_mini, include_reason=False, async_mode=False
        ),
        AnswerRelevancyMetric(
            model=gpt_4o_mini, include_reason=False, async_mode=False
        ),
        FaithfulnessMetric(model=gpt_4o_mini, include_reason=False, async_mode=False),
    ]

    results_dict = {}
    for metric in metrics:
        result = metric.measure(output)
        results_dict[metric.__class__.__name__] = result

    return results_dict


evaluation = Evaluation(
    name="FAQ Evaluation",
    dataset=faq_dataset,
    scorers=[evaluate_faq],
    evaluation_name="faq_evaluation",
)

asyncio.run(evaluation.evaluate(get_test_case))

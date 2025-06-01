from uuid import uuid4
from models.user import UserRole
from repositories.user import create as create_user, CreateUserModel
from repositories.thread import create as create_thread, CreateThreadModel
from service.store_chatbot_v2 import gen_answer
import weave
from service.faq import search as search_faq
from deepeval.test_case import LLMTestCase,LLMTestCaseParams, ConversationalTestCase 
from deepeval.metrics.answer_relevancy.answer_relevancy import AnswerRelevancyMetric
from deepeval.metrics.contextual_precision.contextual_precision import ContextualPrecisionMetric
from deepeval.metrics.faithfulness.faithfulness import FaithfulnessMetric
from deepeval.metrics.base_metric import BaseMetric
from deepeval.metrics import ConversationalGEval
from service.wandb import *
from weave.flow.eval import Evaluation
import asyncio
import deepeval.models.llms.openai_model as deepeval_models
import json

finetune_test_dataset = weave.ref("").get()


gpt_41_mini = deepeval_models.GPTModel(
    model="gpt-4.1-mini",
    timeout=60,
)


# Load training data for test cases
def load_training_data(file_path: str):
    test_cases = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                messages = data.get('messages', [])
                if messages:
                    # Extract user message and gender context
                    user_message = next((msg['content'] for msg in messages if msg['role'] == 'user'), None)
                    gender_context = next((msg['content'] for msg in messages if msg['role'] == 'system' and 'User gender:' in msg['content']), None)
                    if user_message and gender_context:
                        test_cases.append({
                            'user_message': user_message,
                            'gender_context': gender_context,
                            'expected_response': next((msg['content'] for msg in messages if msg['role'] == 'assistant'), None)
                        })
    return test_cases

def get_actual_answer(input: str, gender_context: str) -> str:
    user = create_user(
        CreateUserModel(user_name=str(uuid4()), role=UserRole.chainlit_user)
    )
    thread = create_thread(CreateThreadModel(user_id=user.id, name=user.user_name))

    # Add gender context to the conversation
    history = [
        {"role": "system", "content": gender_context},
        {"role": "user", "content": str(input)}
    ]

    return gen_answer(
        thread_id=thread.id,
        history=history,
        user_id=user.id,
    )

@weave.op(name="get_tone_test_case")
def get_tone_test_case(input: str, expected_output: str, gender_context: str) -> LLMTestCase:
    faqs = search_faq(input)
    actual_answer = get_actual_answer(input, gender_context)
    
    # Create context for pronoun evaluation
    pronoun_context = f"Gender context: {gender_context}\nExpected pronouns based on gender: {get_expected_pronouns(gender_context)}"
    
    test_case = LLMTestCase(
        input=str(input),
        expected_output=expected_output,
        actual_output=actual_answer,
        context=[pronoun_context],
        retrieval_context=[
            f"Question: {faq.question}\nAnswer: {faq.answer}"
            for faq in faqs
        ],
    )
    return test_case

def get_expected_pronouns(gender_context: str) -> dict:
    """Extract expected pronouns based on gender context"""
    if "male" in gender_context.lower():
        return {"bot": "em", "user": "anh"}
    elif "female" in gender_context.lower():
        return {"bot": "em", "user": "chị"}
    else:
        return {"bot": "em", "user": "anh/chị"}

@weave.op(name="evaluate_fine_tuned_tone")
def evaluate_fine_tuned_tone(input, output: LLMTestCase) -> dict:
    pronoun_consistency_metric = ContextualPrecisionMetric(
            name="Vietnamese Pronoun Consistency",
            model=gpt_41_mini,
            include_reason=False, 
            async_mode=False,
            criteria=[
                "Proper use of gender-specific pronouns (em-anh, em-chị, em-anh/chị)",
                "Consistent pronoun usage throughout the response",
                "Appropriate level of formality based on gender context",
                "Natural and respectful tone"
            ],
            evaluation_steps=[],
            evaluation_params=[
                LLMTestCaseParams.INPUT, # phan tich input cua user ("anh muốn hỏi..")
                LLMTestCaseParams.ACTUAL_OUTPUT, # phan tich output cua chatbot
                LLMTestCaseParams.CONTEXT,# metric có thể truy cập thông tin "User gender"
            ]
        )

    result_dict = {}
    result = pronoun_consistency_metric.measure(output)
    result_dict[pronoun_consistency_metric.__class__.__name__] = result

    return result_dict

#test với một số lượng nhỏ test case trước:
# evaluate(test_cases=[tc_unknown_gender, tc_male_gender], metrics=[pronoun_evaluation_metric])

#danh gia toan bo
#evaluation_results = evaluate(test_cases=all_test_cases, metrics=[pronoun_evaluation_metric])

evaluation = Evaluation(
        name="Tone Evaluation",
        dataset=dataset,
        scorers=[evaluate_fine_tuned_tone],
        evaluation_name="tone_evaluation",
    )
asyncio.run(evaluation.evaluate(get_test_case))

@weave.op(name="evaluate_fine_tuned_overall")
def evaluate_fine_tuned_overall(input, output: LLMTestCase) -> dict:
    metrics: list[BaseMetric] = [
        ContextualPrecisionMetric(
            model=gpt_41_mini, include_reason=False, async_mode=False
        ),
        AnswerRelevancyMetric(
            model=gpt_41_mini, include_reason=False, async_mode=False
        ),
        FaithfulnessMetric(
            model=gpt_41_mini, include_reason=False, async_mode=False
        ),
    ]

    results_dict = {}
    for metric in metrics:
        result = metric.measure(output)
        results_dict[metric.__class__.__name__] = result

    return results_dict



'''

if __name__ == "__main__":
    # Load test cases from training data
    test_cases = load_training_data("fine-tuning/fine-tuning_data/train_tone_ds1.jsonl")
    
    # Create evaluation dataset
    dataset = weave.dataset(
        name="Tone-Evaluation-Dataset",
        rows=test_cases
    )

    evaluation = Evaluation(
        name="Tone Evaluation",
        dataset=dataset,
        scorers=[evaluate_tone],
        evaluation_name="tone_evaluation",
    )

    print("Starting tone evaluation...")
    print(f"Dataset: {dataset.name}")
    print(f"Number of test cases: {len(dataset.rows)}")
    print("Evaluating...")
    
    asyncio.run(evaluation.evaluate(get_test_case)) 
'''
import asyncio
from deepeval.test_case.llm_test_case import LLMTestCase, LLMTestCaseParams
from deepeval.test_case.conversational_test_case import ConversationalTestCase
from deepeval.metrics.conversational_g_eval.conversational_g_eval import (
    ConversationalGEval,
)
import deepeval.models.llms.openai_model as deepeval_models
from deepeval import evaluate
from service.wandb import *
import weave
from repositories.user import create as create_user, CreateUserModel, update
from repositories.thread import create as create_thread, CreateThreadModel
from service.store_chatbot_v2 import gen_answer, ConfigModel
from uuid import uuid4
from models.user import UserRole
import service.openai as openai_service
from openai.types.chat_model import ChatModel
from weave.flow.dataset import Dataset
from weave.flow.eval import Evaluation

gpt_41_mini = deepeval_models.GPTModel(
    model="gpt-4.1-mini",
    timeout=60,
)
json_file = "conversation_tone.json"
test_dataset: Dataset = weave.ref("conversation_tone").get()
fine_tune_tone_models: Dataset = weave.ref("fine_tune_tone").get()
model = "ft:gpt-4o-mini-2024-07-18:personal::BeMUbWFj:ckpt-step-200"

pronoun_consistency_metric = ConversationalGEval(
    name="Vietnamese Pronoun Consistency",
    criteria="""Đánh giá khả năng của chatbot trong việc sử dụng đại từ nhân xưng tiếng Việt một cách chính xác và nhất quán trong suốt cuộc hội thoại. Cụ thể:
    1. Chatbot (assistant) trong 'actual_output' phải LUÔN LUÔN tự xưng là 'em'.  Ví dụ: 'dạ em chào anh', 'em có thể giúp gì ạ'. KHÔNG được dùng 'tôi', 'mình'
    2. Cách chatbot gọi người dùng (user) phải dựa trên thông tin được cung cấp hoặc cách người dùng tự xưng:
        - Nếu 'User gender' được cung cấp là 'male' hoặc người dùng tự xưng là 'anh' như 'anh muốn hỏi...', chatbot phải gọi người dùng là 'anh'.
        - Nếu 'User gender' được cung cấp là 'female' hoặc người dùng tự xưng là 'chị' như 'chị muốn hỏi...', chatbot phải gọi người dùng là 'chị'.
        - Nếu người dùng tự xưng là 'chú', chatbot phải gọi người dùng là 'chú' và tự xưng 'cháu'.
        - Nếu người dùng tự xưng là 'bác', chatbot phải gọi người dùng là 'bác' và tự xưng 'cháu'.
        - Nếu người dùng tự xưng là 'cô', chatbot phải gọi người dùng là 'cô' và tự xưng 'cháu'. 
        - Nếu 'User gender' được cung cấp là 'unknown' hoặc không được cung cấp, và người dùng không tự xưng theo một đại từ cụ thể nào ở trên, chatbot phải gọi người dùng là 'anh/chị'.

    3. Tính nhất quán: Chatbot phải duy trì cách xưng hô đã được thiết lập với người dùng một cách nhất quán trong các lượt trả lời tiếp theo trong cùng một cuộc hội thoại, trừ khi có thông tin mới rõ ràng thay đổi cách xưng hô.
    4. Không được sử dụng các cách xưng hô không phù hợp hoặc thiếu tôn trọng.
      HƯỚNG DẪN CHẤM ĐIỂM:
    - Điểm 1.0: Tuân thủ hoàn hảo tất cả các quy tắc trên trong mọi lượt của hội thoại.
    - Phạt nặng (điểm gần 0): Nếu chatbot tự xưng sai (ví dụ: xưng 'tôi' thay vì 'em').
    - Phạt nặng (điểm gần 0): Nếu chatbot gọi sai người dùng một cách rõ ràng (ví dụ: context là 'User gender: male' nhưng chatbot gọi là 'chị').
    - Xem xét toàn bộ cuộc hội thoại để đánh giá tính nhất quán.
    """,
    evaluation_params=[
        LLMTestCaseParams.INPUT,  # Để phân tích input của user (ví dụ: "anh muốn hỏi...")
        LLMTestCaseParams.ACTUAL_OUTPUT,  # Để phân tích output của model
        LLMTestCaseParams.CONTEXT,  # Nếu thông tin `User gender` được truyền qua context cho mỗi lượt
    ],
    model=gpt_41_mini,
)


@weave.op(name="evaluate_tone")
def evaluate_tone(conversation_testcase: ConversationalTestCase) -> dict:
    return {
        "pronoun_consistency": pronoun_consistency_metric.measure(conversation_testcase)
    }


@weave.op(name="get_conversation_testcase")
def get_conversation_testcase(
    conversation_id: str, turns: list[dict], config_model: ConfigModel
) -> ConversationalTestCase:
    user = create_user(
        CreateUserModel(user_name=str(uuid4()), role=UserRole.chainlit_user)
    )
    thread = create_thread(CreateThreadModel(user_id=user.id, name=user.user_name))
    llm_test_cases = []
    conversation_history = []
    for turn in turns:
        user.gender = turn.get("user_gender_context")
        user_message = turn["user_input"]
        update(user)
        conversation_history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )
        chatbot_message = gen_answer(
            user_id=user.id,
            thread_id=thread.id,
            history=conversation_history,
            config=config_model,
        )
        conversation_history.append(
            {
                "role": "assistant",
                "content": chatbot_message,
            }
        )
        llm_test_cases.append(
            LLMTestCase(
                input=user_message,
                actual_output=chatbot_message,
                context=[f"User gender: {user.gender or 'unknown'}"],
            )
        )
    return ConversationalTestCase(turns=llm_test_cases, name=conversation_id)


@weave.op(name="evaluate_fine_tune_model")
def evaluate_fine_tune_model(output: ConfigModel):
    scores = []
    for row in test_dataset.rows:
        conversation_id = row["conversation_id"]
        turns = row["turns"]
        conversation_testcase = get_conversation_testcase(
            conversation_id=conversation_id, turns=turns, config_model=output
        )
        result = evaluate_tone(conversation_testcase)
        scores.append(result["pronoun_consistency"])
    return {
        "pronoun_consistency_score": sum(scores) / len(scores),
    }


@weave.op(name="get_fine_tune_tone_model_config")
def get_config_model(fine_tuned_model_checkpoint_id: str) -> ConfigModel:
    return ConfigModel(
        response=fine_tuned_model_checkpoint_id,
        use_fine_tune_tone=True,
    )


if __name__ == "__main__":
    evaluation = Evaluation(
        name="Phone Evaluation",
        dataset=fine_tune_tone_models,
        scorers=[evaluate_fine_tune_model],
        evaluation_name="phone_evaluation",
    )
    asyncio.run(evaluation.evaluate(get_config_model))

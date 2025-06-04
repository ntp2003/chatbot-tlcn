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

pronoun_consistency_metric = ConversationalGEval(
    name="Vietnamese Pronoun Consistency",
    criteria="""Đánh giá khả năng của chatbot trong việc sử dụng đại từ nhân xưng tiếng Việt một cách chính xác và nhất quán trong suốt cuộc hội thoại. 

    THÔNG TIN CẦN PHÂN TÍCH:
    - 'input': Tin nhắn của người dùng - cần phân tích cách người dùng tự xưng và ngữ cảnh
    - 'actual_output': Phản hồi của chatbot - cần đánh giá cách chatbot tự xưng và gọi người dùng
    - 'context': Thông tin bổ sung về người dùng (ví dụ: User gender) và ngữ cảnh cuộc hội thoại

    QUY TẮC ĐÁNH GIÁ:

    1. **Cách chatbot tự xưng trong 'actual_output':**
       - Chatbot **nên** tự xưng là 'em' (được ưu tiên, đặc biệt ở các lượt nói đầu hoặc khi cần làm rõ hành động)
       - Chatbot **TUYỆT ĐỐI KHÔNG** được dùng 'tôi', 'mình' để tự xưng
       - Ngoại lệ: Khi người dùng trong 'input' tự xưng là 'chú', 'bác', 'cô' thì chatbot phải tự xưng 'cháu'

    2. **Cách chatbot gọi người dùng (dựa trên 'input' và 'context'):**
       - Nếu trong 'context' có 'User gender: male' HOẶC người dùng trong 'input' tự xưng 'anh' → chatbot gọi 'anh'
       - Nếu trong 'context' có 'User gender: female' HOẶC người dùng trong 'input' tự xưng 'chị' → chatbot gọi 'chị'
       - Nếu người dùng trong 'input' tự xưng 'chú' → chatbot gọi 'chú' và tự xưng 'cháu'
       - Nếu người dùng trong 'input' tự xưng 'bác' → chatbot gọi 'bác' và tự xưng 'cháu'
       - Nếu người dùng trong 'input' tự xưng 'cô' → chatbot gọi 'cô' và tự xưng 'cháu'
       - Nếu trong 'context' có 'User gender: unknown' hoặc không có thông tin gender, và người dùng trong 'input' không tự xưng rõ ràng → chatbot gọi 'anh/chị'

    3. **Tính nhất quán:** 
       - Phân tích toàn bộ lịch sử hội thoại trong 'context' để đảm bảo chatbot duy trì cách xưng hô đã thiết lập
       - Chỉ chấp nhận thay đổi cách xưng hô khi có thông tin mới rõ ràng trong 'input'

    4. **Tính lịch sự và phù hợp:**
       - Không sử dụng cách xưng hô thiếu tôn trọng hoặc không phù hợp với văn hóa Việt Nam

    HƯỚNG DẪN CHẤM ĐIỂM:
    - **Điểm 1.0:** Tuân thủ hoàn hảo tất cả các quy tắc trên, phù hợp với thông tin trong 'input', 'context' và thể hiện tính nhất quán trong 'actual_output'
    
    - **Phạt nặng (điểm 0.0-0.3):**
      • Chatbot tự xưng sai hoàn toàn ('tôi', 'mình' thay vì 'em')
      • Sử dụng sai giữa 'em' và 'cháu' khi 'input' hoặc 'context' yêu cầu rõ ràng
      • Gọi sai người dùng rõ ràng (ví dụ: 'context' là 'User gender: male' nhưng gọi 'chị')
      • Không nhất quán trong cùng cuộc hội thoại mà không có lý do chính đáng từ 'input' mới
    
    - **Phạt vừa (điểm 0.4-0.7):**
      • Thiếu một số cách xưng hô cần thiết ở những vị trí quan trọng
      • Không tận dụng đầy đủ thông tin từ 'context' để xác định cách xưng hô phù hợp
    
    - **Phạt nhẹ hoặc không phạt (điểm 0.8-1.0):**
      • Chatbot không tự xưng 'em' trong một số ít câu trả lời ngắn, trực tiếp ở các lượt sau, khi vai trò đã được thiết lập và không ảnh hưởng đến tính lịch sự

    CÁCH PHÂN TÍCH:
    1. Đọc kỹ 'context' để hiểu thông tin về người dùng và lịch sử hội thoại
    2. Phân tích 'input' để xác định cách người dùng tự xưng và mong đợi được gọi
    3. Đánh giá 'actual_output' dựa trên các quy tắc trên
    4. Xem xét tính nhất quán với các lượt hội thoại trước đó (nếu có trong context)
    """,
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT,
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
        name="Tone Evaluation",
        dataset=fine_tune_tone_models,
        scorers=[evaluate_fine_tune_model],
        evaluation_name="phone_evaluation",
    )
    asyncio.run(evaluation.evaluate(get_config_model))

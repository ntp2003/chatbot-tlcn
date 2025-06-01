import json
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from deepeval.synthesizer import Synthesizer
from deepeval.dataset import Golden
from deepeval.synthesizer.config import StylingConfig

class ToneType(Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    CASUAL = "casual"

@dataclass
class ToneTestCase:
    user_message: str
    expected_tone: ToneType
    context: str = ""
    expected_keywords: List[str] = None

def load_tone_test_cases() -> List[ToneTestCase]:
    # Define styling configuration for tone testing
    styling_config = StylingConfig(
        input_format="Các câu hỏi bằng tiếng Việt liên quan đến sản phẩm, chính sách bảo hành, thanh toán, giao hàng, và dịch vụ tại FPT Shop.",
        expected_output_format="Câu trả lời tư vấn rõ ràng, chính xác, thể hiện sự chuyên nghiệp và thân thiện như một nhân viên bán hàng của FPT Shop.",
        task="Trả lời các câu hỏi thường gặp của khách hàng về sản phẩm và dịch vụ của FPT Shop nhằm hỗ trợ bán hàng và chăm sóc khách hàng.",
        scenario="Khách hàng tiềm năng hoặc khách hàng hiện tại đang cần được giải đáp nhanh chóng về thông tin mua sắm, chính sách và dịch vụ tại FPT Shop.",
    )

    # Initialize synthesizer
    synthesizer = Synthesizer(
        model="gpt-4",
        max_concurrent=10,
        cost_tracking=True,
        styling_config=styling_config,
    )

    # Example contexts for different tones
    contexts = [
        {
            "context": "Khách hàng hỏi về chính sách bảo hành điện thoại",
            "tone": ToneType.PROFESSIONAL,
            "keywords": ["chuyên nghiệp", "đảm bảo", "chính sách"]
        },
        {
            "context": "Khách hàng cần tư vấn mua điện thoại mới",
            "tone": ToneType.FRIENDLY,
            "keywords": ["thân thiện", "tư vấn", "hỗ trợ"]
        },
        {
            "context": "Khách hàng khiếu nại về sản phẩm",
            "tone": ToneType.FORMAL,
            "keywords": ["trân trọng", "xin lỗi", "giải quyết"]
        },
        {
            "context": "Khách hàng hỏi về khuyến mãi",
            "tone": ToneType.CASUAL,
            "keywords": ["ưu đãi", "hấp dẫn", "đặc biệt"]
        }
    ]

    # Generate test cases using synthesizer
    test_cases = []
    for ctx in contexts:
        goldens = synthesizer.generate_goldens_from_contexts(
            contexts=[[ctx["context"]]],
            num_goldens=2  # Generate 2 test cases per context
        )
        
        for golden in goldens:
            test_cases.append(ToneTestCase(
                user_message=golden.input,
                expected_tone=ctx["tone"],
                context=ctx["context"],
                expected_keywords=ctx["keywords"]
            ))

    return test_cases

def evaluate_tone(model_response: str, test_case: ToneTestCase) -> Dict:
    """
    Đánh giá tone trong câu trả lời
    """
    results = {
        "tone_match": False,
        "keyword_presence": 0,
        "response_length": len(model_response)
    }
    
    # Kiểm tra sự hiện diện của các từ khóa
    if test_case.expected_keywords:
        keyword_count = sum(1 for keyword in test_case.expected_keywords 
                          if keyword.lower() in model_response.lower())
        results["keyword_presence"] = keyword_count / len(test_case.expected_keywords)
    
    # TODO: Implement more sophisticated tone analysis
    # This could include sentiment analysis, formality detection, etc.
    
    return results

def save_tone_results(results: List[Dict], output_file: str):
    """
    Lưu kết quả đánh giá tone
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2) 
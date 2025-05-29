import json
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

@dataclass
class TestCase:
    gender: Gender
    user_message: str
    expected_pronouns: Dict[str, str]  # {"bot": "em", "user": "anh/chị"}
    context: str = ""

def load_test_cases() -> List[TestCase]:
    test_cases = [
        # Test cases cho gender male
        TestCase(
            gender=Gender.MALE,
            user_message="Anh muốn hỏi về chính sách bảo hành",
            expected_pronouns={"bot": "em", "user": "anh"},
            context="Hỏi về chính sách bảo hành"
        ),
        # Test cases cho gender female
        TestCase(
            gender=Gender.FEMALE,
            user_message="Chị muốn mua điện thoại mới",
            expected_pronouns={"bot": "em", "user": "chị"},
            context="Hỏi về mua sản phẩm"
        ),
        # Test cases cho gender unknown
        TestCase(
            gender=Gender.UNKNOWN,
            user_message="Tôi muốn biết giá sản phẩm",
            expected_pronouns={"bot": "em", "user": "anh/chị"},
            context="Hỏi về giá"
        ),
        # Test cases cho chuyển đổi xưng hô
        TestCase(
            gender=Gender.MALE,
            user_message="Tôi muốn đổi sang chị",
            expected_pronouns={"bot": "em", "user": "chị"},
            context="Chuyển đổi xưng hô"
        )
    ]
    return test_cases

def evaluate_pronoun_usage(model_response: str, test_case: TestCase) -> Dict:
    """
    Đánh giá việc sử dụng đại từ trong câu trả lời
    """
    results = {
        "correct_bot_pronoun": False,
        "correct_user_pronoun": False,
        "pronoun_consistency": False
    }
    
    # Kiểm tra đại từ của bot
    if test_case.expected_pronouns["bot"] in model_response.lower():
        results["correct_bot_pronoun"] = True
        
    # Kiểm tra đại từ của user
    if test_case.expected_pronouns["user"] in model_response.lower():
        results["correct_user_pronoun"] = True
        
    # Kiểm tra tính nhất quán
    if results["correct_bot_pronoun"] and results["correct_user_pronoun"]:
        results["pronoun_consistency"] = True
        
    return results

def save_test_results(results: List[Dict], output_file: str):
    """
    Lưu kết quả đánh giá
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2) 
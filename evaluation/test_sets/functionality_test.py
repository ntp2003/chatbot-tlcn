import json
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class ProductType(Enum):
    PHONE = "phone"
    LAPTOP = "laptop"
    ACCESSORY = "accessory"
    UNDETERMINED = "undetermined"

@dataclass
class FunctionalityTestCase:
    user_message: str
    expected_product_type: ProductType
    expected_intent: str
    context: str = ""

def load_functionality_test_cases() -> List[FunctionalityTestCase]:
    test_cases = [
        # Test cases cho điện thoại
        FunctionalityTestCase(
            user_message="Anh muốn mua iPhone 15",
            expected_product_type=ProductType.PHONE,
            expected_intent="purchase",
            context="Hỏi về mua điện thoại"
        ),
        # Test cases cho laptop
        FunctionalityTestCase(
            user_message="Chị cần tư vấn mua laptop",
            expected_product_type=ProductType.LAPTOP,
            expected_intent="consultation",
            context="Hỏi về mua laptop"
        ),
        # Test cases cho phụ kiện
        FunctionalityTestCase(
            user_message="Tôi muốn mua tai nghe",
            expected_product_type=ProductType.ACCESSORY,
            expected_intent="purchase",
            context="Hỏi về mua phụ kiện"
        ),
        # Test cases cho không xác định
        FunctionalityTestCase(
            user_message="Shop có làm việc Chủ Nhật không?",
            expected_product_type=ProductType.UNDETERMINED,
            expected_intent="general_inquiry",
            context="Hỏi về giờ làm việc"
        )
    ]
    return test_cases

def evaluate_functionality(
    model_response: str,
    detected_product_type: ProductType,
    detected_intent: str,
    test_case: FunctionalityTestCase
) -> Dict:
    """
    Đánh giá khả năng phát hiện chức năng
    """
    results = {
        "correct_product_type": False,
        "correct_intent": False,
        "response_relevance": False
    }
    
    # Kiểm tra loại sản phẩm
    if detected_product_type == test_case.expected_product_type:
        results["correct_product_type"] = True
        
    # Kiểm tra intent
    if detected_intent == test_case.expected_intent:
        results["correct_intent"] = True
        
    # Kiểm tra tính liên quan của câu trả lời
    # TODO: Implement more sophisticated relevance checking
    results["response_relevance"] = True
        
    return results

def save_functionality_results(results: List[Dict], output_file: str):
    """
    Lưu kết quả đánh giá chức năng
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2) 
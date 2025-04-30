from typing import Any
from agents.base import AgentTemporaryMemory
from models.user_memory import UserIntent
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the user's intent about consulting or searching for a laptop product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_user_intent",
        role: str = "Collect and update the user's intent about consulting or searching for a laptop product.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "Analyze whether the user is requesting additional laptop product suggestions.",
        ],
        cases_used: list[str] = [
            "The user expresses a desire for consultation or suggestions about other laptop products (e.g., 'Are there any other laptops?', 'Are there any other laptops in this segment?', 'Can you suggest similar laptops?', ...).",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "is_user_needs_other_suggestions": {
                "type": "boolean",
                "default": False,
                "description": "Return True if the user expresses a desire for additional laptop product suggestions or alternatives compared to previously mentioned options (e.g., 'Are there any other laptops?', 'What other laptops are available in this segment?', 'Can you suggest similar alternatives?'). Return False otherwise.",
            }
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the user's intent about consulting or searching for a laptop product.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        is_user_needs_other_suggestions: bool = kwargs.get(
            "is_user_needs_other_suggestions", False
        )

        if not temporary_memory.user_memory.intent:
            temporary_memory.user_memory.intent = UserIntent()

        temporary_memory.user_memory.intent.is_user_needs_other_suggestions = (
            is_user_needs_other_suggestions
        )

        return ToolResponse(
            type="finished", content="User intent collected successfully."
        )

'''
def detect_laptop_intent(text: str) -> Optional[str]:
    """
    Detect user intent for laptops
    Example:
    - "Tôi muốn mua laptop" -> "buy"
    - "Cho tôi xem các loại macbook" -> "view"
    - "So sánh Dell XPS và Macbook Pro" -> "compare"
    """
    # Intent keywords mapping
    INTENT_MAPPING = {
        "buy": ["mua", "đặt", "order", "purchase"],
        "view": ["xem", "tìm", "kiếm", "search", "look"],
        "compare": ["so sánh", "compare", "đối chiếu"],
        "info": ["thông tin", "chi tiết", "cấu hình", "specs"],
        "price": ["giá", "price", "cost", "value"]
    }
    
    text = text.lower()
    
    # Check each intent
    for intent, keywords in INTENT_MAPPING.items():
        for keyword in keywords:
            if keyword in text:
                return intent
                
    return None

def extract_laptop_features(text: str) -> List[str]:
    """
    Extract laptop features from text
    Example:
    - "Laptop gaming cấu hình cao màn 4K" -> ["gaming", "high performance", "4K display"]
    """
    # Common laptop features
    FEATURES = {
        "gaming": ["game", "gaming", "chơi game"],
        "văn phòng": ["office", "work", "làm việc"],
        "đồ họa": ["design", "graphics", "thiết kế"],
        "mỏng nhẹ": ["thin", "light", "portable", "slim"],
        "pin trâu": ["long battery", "battery life"],
        "màn đẹp": ["display", "screen", "retina", "4k", "oled"],
        "cấu hình cao": ["high performance", "powerful", "mạnh"],
        "tản nhiệt tốt": ["cooling", "thermal", "nhiệt độ"],
        "bàn phím": ["keyboard", "mechanical", "rgb"],
        "âm thanh": ["sound", "speaker", "audio"]
    }
    
    text = text.lower()
    found_features = []
    
    # Check each feature
    for feature, keywords in FEATURES.items():
        if feature in text or any(keyword in text for keyword in keywords):
            found_features.append(feature)
            
    return found_features 
'''
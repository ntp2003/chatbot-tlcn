from typing import Any
from agents.base import AgentTemporaryMemory
from models.user_memory import UserIntent
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client

class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the user's intent about consulting or searching for an accessory product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_user_intent",
        role: str = "Collect and update the user's intent about consulting or searching for an accessory product.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "Analyze whether the user is requesting additional accessory product suggestions.",
        ],
        cases_used: list[str] = [
            "The user expresses a desire for consultation or suggestions about other accessory products (e.g., 'Are there any other accessories?', 'Are there any other accessories in this category?', 'Can you suggest similar accessories?', ...).",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "is_user_needs_other_suggestions": {
                "type": "boolean",
                "default": False,
                "description": "Return True if the user expresses a desire for additional accessory product suggestions or alternatives compared to previously mentioned options (e.g., 'Are there any other accessories?', 'What other accessories are available in this category?', 'Can you suggest similar alternatives?'). Return False otherwise.",
            }
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the user's intent about consulting or searching for an accessory product.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )

        is_user_needs_other_suggestions: bool = kwargs.get(
            "is_user_needs_other_suggestions", False
        )

        if not temporary_memory.user_memory.intent:
            temporary_memory.user_memory.intent = UserIntent()

        temporary_memory.user_memory.intent.is_user_needs_other_suggestions = (
            is_user_needs_other_suggestions
        )

        wandb_client.finish_call(
            call,
            output= temporary_memory.user_memory,
        )

        return ToolResponse(
            type="finished", content="User intent collected successfully."
        )

'''
def detect_accessory_intent(text: str) -> Optional[str]:
    """
    Detect user intent for accessories
    Example:
    - "Tôi muốn mua tai nghe" -> "buy"
    - "Cho tôi xem các loại sạc" -> "view"
    - "So sánh các loại ốp lưng" -> "compare"
    """
    # Intent keywords mapping
    INTENT_MAPPING = {
        "buy": ["mua", "đặt", "order", "purchase"],
        "view": ["xem", "tìm", "kiếm", "search", "look"],
        "compare": ["so sánh", "compare", "đối chiếu"],
        "info": ["thông tin", "chi tiết", "mô tả", "đặc điểm"],
        "price": ["giá", "price", "cost", "value"]
    }
    
    text = text.lower()
    
    # Check each intent
    for intent, keywords in INTENT_MAPPING.items():
        for keyword in keywords:
            if keyword in text:
                return intent
                
    return None

def extract_accessory_features(text: str) -> List[str]:
    """
    Extract accessory features from text
    Example:
    - "Tai nghe không dây chống ồn" -> ["không dây", "chống ồn"]
    """
    # Common accessory features
    FEATURES = {
        "không dây": ["wireless", "bluetooth"],
        "chống ồn": ["noise cancelling", "anc"],
        "chống nước": ["waterproof", "water resistant"],
        "sạc nhanh": ["fast charge", "quick charge"],
        "Type-C": ["usb-c", "type c"],
        "cảm ứng": ["touch", "touch control"],
        "pin trâu": ["long battery", "large capacity"]
    }
    
    text = text.lower()
    found_features = []
    
    # Check each feature
    for feature, keywords in FEATURES.items():
        if feature in text or any(keyword in text for keyword in keywords):
            found_features.append(feature)
            
    return found_features 
'''
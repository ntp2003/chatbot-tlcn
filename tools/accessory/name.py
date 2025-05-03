from typing import Any, Optional
from agents.base import AgentTemporaryMemory
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client

class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the name of the specific accessory product the user is interested in.
    """

    def __init__(
        self,
        name: str = "collect_and_update_accessory_name_requirements",
        role: str = "Collect and update the user's requirements about the name of the specific accessory product they are interested in.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            '- If the user is interested in a specific accessory product in the list of suggestions shown in the previous conversation (e.g., "phụ kiện đầu tiên", "cái thứ <number>", ...), you should set the accessory_name parameter to the name of that accessory product.',
        ],
        cases_used: list[str] = [
            "The user mentions the name of the specific accessory product they are interested in.",
            "The user mentions the information about the name of the specific accessory product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "accessory_name": {
                "type": "string",
                "description": "The name of the accessory product the user is interested in."
                " If the user is interested in a specific accessory product in the list of suggestions shown in the previous conversation, you should set this parameter to the name of that accessory product.",
            }
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the name of the specific accessory product the user is interested in.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )

        accessory_name = kwargs.get("accessory_name")

        temporary_memory.user_memory.product_name = (
            accessory_name if accessory_name else temporary_memory.user_memory.product_name
        )

        wandb_client.finish_call(
            call,
            output= temporary_memory.user_memory,
        )

        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

'''
def extract_accessory_name(text: str) -> Optional[str]:
    """
    Extract accessory name from text
    Example:
    - "Tôi muốn mua tai nghe Apple AirPods Pro" -> "AirPods Pro"
    - "Cho tôi xem sạc Samsung 25W" -> "Sạc 25W"
    """
    # Common accessory types in Vietnamese
    ACCESSORY_TYPES = [
        "tai nghe",
        "sạc",
        "cáp sạc",
        "ốp lưng",
        "bao da",
        "miếng dán",
        "pin dự phòng",
        "giá đỡ",
        "bút cảm ứng"
    ]
    
    # Common brands to remove
    BRANDS = ["apple", "samsung", "xiaomi", "huawei", "sony", "anker", "belkin", "logitech"]
    
    text = text.lower()
    
    # Find accessory type
    accessory_type = None
    for type_ in ACCESSORY_TYPES:
        if type_ in text:
            accessory_type = type_
            break
            
    if not accessory_type:
        return None
        
    # Remove common words and brands
    for brand in BRANDS:
        text = text.replace(brand, "")
        
    # Remove common Vietnamese words
    common_words = ["tôi", "muốn", "mua", "xem", "cho", "cái", "chiếc", "của"]
    for word in common_words:
        text = text.replace(word, "")
        
    # Clean up text
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Capitalize words
    text = " ".join(word.capitalize() for word in text.split())
    
    return text if text else None

def clean_accessory_name(name: str) -> str:
    """
    Clean up accessory name
    Example: "   tai Nghe  AIRPODS  pro   " -> "Tai Nghe AirPods Pro"
    """
    if not name:
        return ""
        
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Capitalize words
    return " ".join(word.capitalize() for word in name.split())
'''
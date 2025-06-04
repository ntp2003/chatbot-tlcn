from typing import Any, Optional, Tuple
from models.user_memory import PriceRequirement
from agents.base import AgentTemporaryMemory
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client

class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the price of an accessory product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_accessory_price_requirements",
        role: str = "Collect and update the user's requirements about the price of an accessory product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The standard currency unit is VND. If the user provides the price in another currency, you need to convert it to VND.",
            "If the user use the slang or abbreviations for the currency unit, you need to clarify and convert them to VND.",
        ],
        cases_used: list[str] = [
            "The user mentions the information about the price of an accessory product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "approximate_price": {
                "type": "number",
                "description": "The approximate price the user can accept.",
            },
            "min_price": {
                "type": "number",
                "description": "The minimum price the user can accept.",
            },
            "max_price": {
                "type": "number",
                "description": "The maximum price the user can accept.",
            },
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the price of an accessory product.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )

        approximate_price = kwargs.get("approximate_price")
        min_price = kwargs.get("min_price")
        max_price = kwargs.get("max_price")

        price_requirement_obj = PriceRequirement(
            approximate_price, min_price, max_price
        )

        temporary_memory.user_memory.min_price = price_requirement_obj.min_price
        temporary_memory.user_memory.max_price = price_requirement_obj.max_price

        wandb_client.finish_call(
            call,
            output= temporary_memory.user_memory,
        )

        return ToolResponse(
            type="finished", content="Price requirement collected successfully."
        )
'''
def extract_price_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract price range from text
    Example:
    - "Tai nghe dưới 500k" -> (None, 500000)
    - "Sạc từ 200k đến 500k" -> (200000, 500000)
    - "Cáp giá 300k" -> (300000, 300000)
    """
    # Convert k/K to 000
    text = text.lower().replace(',', '')
    text = re.sub(r'(\d+)\s*k', r'\1000', text, flags=re.IGNORECASE)
    
    # Extract numbers from text
    numbers = [int(num) for num in re.findall(r'\d+', text)]
    
    # No numbers found
    if not numbers:
        return None, None
        
    # Check for price range patterns
    if 'từ' in text and 'đến' in text and len(numbers) >= 2:
        return numbers[0], numbers[1]
        
    if 'dưới' in text and numbers:
        return None, numbers[0]
        
    if 'trên' in text and numbers:
        return numbers[0], None
        
    # Single price
    if len(numbers) == 1:
        return numbers[0], numbers[0]
        
    # Default: take first two numbers as range
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
        
    return None, None

def normalize_price(price: Optional[int]) -> Optional[int]:
    """
    Normalize price to standard format (VND)
    Example: 500 -> 500000
    """
    if price is None:
        return None
        
    # Convert to string to count digits
    price_str = str(price)
    
    # If price has less than 4 digits, assume it's in thousands
    if len(price_str) < 4:
        return price * 1000
        
    return price
'''
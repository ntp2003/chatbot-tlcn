from typing import Any, Optional, Tuple
from agents.base import AgentTemporaryMemory
from service.converter import convert_band_name_to_code
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
import re


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the brand and version of an accessory product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_accessory_brand_and_version_requirements",
        role: str = "Collect and update the user's requirements about the brand and version of an accessory product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The brand refers to the name of the company or label that manufactures the accessory product.",
            "The version refers to the specific model or variant of the accessory product.",
        ],
        cases_used: list[str] = [
            "The user mentions the information about the brand or version of an accessory product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "accessory_brand": {
                "type": "string",
                "description": "The brand of the accessory product the user wants to consult or purchase.",
            },
            "accessory_version": {
                "type": "string",
                "description": "The version of the accessory product the user wants to consult or purchase.",
            },
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the brand and version of an accessory product.
        """

        if not (temporary_memory and temporary_memory.user_memory):
            return ToolResponse(type="error", content="User memory is not available.")

        accessory_brand = kwargs.get("accessory_brand")
        accessory_version = kwargs.get("accessory_version")

        user_memory = temporary_memory.user_memory

        if accessory_brand == user_memory.brand_name:
            return ToolResponse(
                type="finished", content="User requirements collected successfully."
            )

        brand_code = convert_band_name_to_code(accessory_brand)
        if not brand_code:
            return ToolResponse(
                type="message",
                content=(
                    f'You should tell the user: "Our store does not carry {accessory_brand} accessories. '
                    'You can check out other brands like Apple, Samsung, Sony, etc."'
                ),
            )

        user_memory.brand_code = brand_code
        user_memory.brand_name = accessory_brand

        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

def extract_brand_and_version(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract brand and version from accessory text
    Example: 
    - "Tai nghe Apple AirPods Pro 2" -> ("APPLE", "AirPods Pro 2")
    - "Sạc Samsung 25W" -> ("SAMSUNG", "25W")
    """
    # Common accessory brands
    BRAND_MAPPING = {
        "apple": "APPLE",
        "samsung": "SAMSUNG",
        "xiaomi": "XIAOMI",
        "huawei": "HUAWEI",
        "sony": "SONY",
        "anker": "ANKER",
        "belkin": "BELKIN",
        "logitech": "LOGITECH"
    }

    text = text.lower()
    
    # Try to find brand
    brand = None
    version = None
    
    for key, value in BRAND_MAPPING.items():
        if key in text:
            brand = value
            # Remove brand from text to extract version
            version = text.replace(key, "").strip()
            break
    
    # Clean up version
    if version:
        # Remove common words
        version = re.sub(r'^(tai nghe|sạc|cáp|ốp|bao da|miếng dán|pin)\s+', '', version, flags=re.IGNORECASE)
        version = version.strip()
        # Capitalize first letter of each word
        version = " ".join(word.capitalize() for word in version.split())
        
    return brand, version if version else None

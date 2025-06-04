from typing import Any, Optional, Tuple
from agents.base import AgentTemporaryMemory
from service.converter import convert_band_name_to_code
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the brand and version of a laptop product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_laptop_brand_and_version_requirements",
        role: str = "Collect and update the user's requirements about the brand and version of a laptop product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The brand refers to the name of the company or label that manufactures the laptop product.",
            "The version refers to the specific model or variant of the laptop product.",
        ],
        cases_used: list[str] = [
            "The user mentions the information about the brand or version of a laptop product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "laptop_brand": {
                "type": "string",
                "description": "The brand of the laptop product the user wants to consult or purchase.",
                "examples": [
                    {
                        "input": "cần tư vấn về macbook air 13 M4 2025",
                        "output": "Apple",
                    },
                    {
                        "input": "tôi muốn mua laptop khác",
                        "output": None,
                    },
                ],
            },
            "laptop_version": {
                "type": "string",
                "description": "The version of the laptop product the user wants to consult or purchase.",
            },
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the brand and version of a laptop product.
        """

        if not (temporary_memory and temporary_memory.user_memory):
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )

        laptop_brand = kwargs.get("laptop_brand")
        laptop_version = kwargs.get("laptop_version")

        user_memory = temporary_memory.user_memory

        if laptop_brand == user_memory.brand_name:
            wandb_client.finish_call(
                call,
                output="No changes made to user memory.",
            )
            return ToolResponse(
                type="finished", content="User requirements collected successfully."
            )

        brand_code = convert_band_name_to_code(laptop_brand)
        if not brand_code and laptop_brand:
            wandb_client.finish_call(
                call, output=f"{laptop_brand} is not a valid laptop brand."
            )
            return ToolResponse(
                type="message",
                content=(
                    f'You should tell the user: "Our store does not carry {laptop_brand} laptops. '
                    'You can check out other brands like Dell, HP, Lenovo, Apple, etc."'
                ),
            )

        user_memory.brand_code = brand_code if brand_code else None
        user_memory.brand_name = laptop_brand if laptop_brand else None

        wandb_client.finish_call(
            call,
            output=temporary_memory.user_memory,
        )
        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )


'''
def extract_brand_and_version(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract brand and version from laptop text
    Example: 
    - "Laptop Dell XPS 13" -> ("DELL", "XPS 13")
    - "MacBook Pro M2" -> ("APPLE", "MacBook Pro M2")
    """
    # Common laptop brands
    BRAND_MAPPING = {
        "apple": "APPLE",
        "macbook": "APPLE",
        "dell": "DELL",
        "hp": "HP",
        "lenovo": "LENOVO",
        "thinkpad": "LENOVO",
        "asus": "ASUS",
        "acer": "ACER",
        "msi": "MSI",
        "lg": "LG",
        "samsung": "SAMSUNG"
    }
    
    # Common laptop series
    SERIES_MAPPING = {
        "APPLE": ["macbook air", "macbook pro", "imac"],
        "DELL": ["xps", "inspiron", "latitude", "precision", "vostro"],
        "HP": ["pavilion", "envy", "omen", "elitebook", "probook"],
        "LENOVO": ["thinkpad", "ideapad", "legion", "yoga"],
        "ASUS": ["zenbook", "vivobook", "rog", "tuf"],
        "ACER": ["aspire", "nitro", "predator", "swift"],
        "MSI": ["modern", "prestige", "creator", "stealth", "raider"]
    }

    text = text.lower()
    
    # Try to find brand
    brand = None
    version = None
    
    # First check for brand
    for key, value in BRAND_MAPPING.items():
        if key in text:
            brand = value
            break
    
    if brand:
        # Try to find series for this brand
        if brand in SERIES_MAPPING:
            for series in SERIES_MAPPING[brand]:
                if series in text:
                    # Extract everything after series name
                    version_match = re.search(f"{series}\\s+(.+)", text, re.IGNORECASE)
                    if version_match:
                        version = version_match.group(1)
                    else:
                        version = series
                    break
        
        # If no series found, try to extract model number
        if not version:
            # Look for common model number patterns
            model_match = re.search(r'(\w+[\s-]?\d+[a-z0-9]*)', text)
            if model_match:
                version = model_match.group(1)
    
    # Clean up version
    if version:
        version = version.strip()
        version = " ".join(word.capitalize() for word in version.split())
        
    return brand, version if version else None
'''

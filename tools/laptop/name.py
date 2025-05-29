from typing import Any, Optional
from agents.base import AgentTemporaryMemory
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the name of the specific laptop product the user is interested in.
    """

    def __init__(
        self,
        name: str = "collect_and_update_laptop_name_requirements",
        role: str = "Collect and update the user's requirements about the name of the specific laptop product they are interested in.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            '- If the user is interested in a specific laptop product in the list of suggestions shown in the previous conversation (e.g., "laptop đầu tiên", "cái thứ <number>", ...), you should set the laptop_name parameter to the name of that laptop product.',
        ],
        cases_used: list[str] = [
            "The user mentions the name of the specific laptop product they are interested in.",
            "The user mentions the information about the name of the specific laptop product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "laptop_name": {
                "type": "string",
                "description": "The name of the laptop product the user is interested in."
                " If the user is interested in a specific laptop product in the list of suggestions shown in the previous conversation, you should set this parameter to the name of that laptop product.",
                "examples": [
                    {
                        "the suggested list of laptops": "1. Laptop A\n2. Laptop B\n3. Laptop C",
                        "input": "Tôi quan tâm đến chiếc laptop đầu tiên.",
                        "output": "Laptop A",
                    },
                    {
                        "the suggested list of laptops": "1. Laptop A v1\n2. Laptop B v2\n3. Laptop C v3",
                        "input": "laptop B",
                        "output": "Laptop B v2",
                    },
                ],
            }
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the name of the specific laptop product the user is interested in.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )

        laptop_name = kwargs.get("laptop_name")

        temporary_memory.user_memory.product_name = (
            laptop_name if laptop_name else temporary_memory.user_memory.product_name
        )

        wandb_client.finish_call(
            call,
            output=temporary_memory.user_memory,
        )

        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )


'''
def extract_laptop_name(text: str) -> Optional[str]:
    """
    Extract laptop name from text
    Example:
    - "Tôi muốn mua Macbook Pro M2" -> "MacBook Pro M2"
    - "Cho tôi xem Dell XPS 13" -> "XPS 13"
    """
    # Common laptop brands and series
    BRANDS = {
        "macbook": ["air", "pro"],
        "dell": ["xps", "inspiron", "latitude", "precision", "vostro"],
        "hp": ["pavilion", "envy", "omen", "elitebook", "probook"],
        "lenovo": ["thinkpad", "ideapad", "legion", "yoga"],
        "asus": ["zenbook", "vivobook", "rog", "tuf"],
        "acer": ["aspire", "nitro", "predator", "swift"],
        "msi": ["modern", "prestige", "creator", "stealth", "raider"]
    }
    
    text = text.lower()
    
    # Remove common Vietnamese words
    common_words = ["tôi", "muốn", "mua", "xem", "cho", "cái", "chiếc", "laptop", "máy tính"]
    for word in common_words:
        text = text.replace(word, "")
    
    # Try to find brand and series
    for brand, series_list in BRANDS.items():
        if brand in text:
            # Check for series
            for series in series_list:
                if series in text:
                    # Extract everything after series
                    match = re.search(f"{series}\\s+(.+)", text, re.IGNORECASE)
                    if match:
                        model = match.group(1).strip()
                        return f"{series.capitalize()} {model.capitalize()}"
                    return series.capitalize()
            
            # If no series found, try to extract model number
            model_match = re.search(r'(\w+[\s-]?\d+[a-z0-9]*)', text)
            if model_match:
                return model_match.group(1).strip().capitalize()
    
    return None

def clean_laptop_name(name: str) -> str:
    """
    Clean up laptop name
    Example: "   macbook  PRO  m2   " -> "MacBook Pro M2"
    """
    if not name:
        return ""
        
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Special cases for common terms
    name = name.replace("Macbook", "MacBook")
    name = name.replace("Probook", "ProBook")
    name = name.replace("Elitebook", "EliteBook")
    name = name.replace("Ideapad", "IdeaPad")
    name = name.replace("Thinkpad", "ThinkPad")
    name = name.replace("Zenbook", "ZenBook")
    name = name.replace("Vivobook", "VivoBook")
    
    # Capitalize remaining words
    return " ".join(word.capitalize() for word in name.split())
'''

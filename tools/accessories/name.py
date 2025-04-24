from typing import Any
from agents.base import AgentTemporaryMemory
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool


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

        accessory_name = kwargs.get("accessory_name")

        temporary_memory.user_memory.product_name = (
            accessory_name if accessory_name else temporary_memory.user_memory.product_name
        )

        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

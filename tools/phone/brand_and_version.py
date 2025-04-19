from typing import Any
from agents.base import AgentTemporaryMemory
from service.converter import convert_band_name_to_code
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the brand and version of a phone product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_phone_brand_and_version_requirements",
        role: str = "Collect and update the user's requirements about the brand and version of a phone product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The brand refer to the name of the company or label that manufactures the phone product.",
            "The version refer to the specific model or variant of the phone product.",
        ],
        cases_used: list[str] = [
            "The user mentions the information about the brand or version of a phone product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "phone_brand": {
                "type": "string",
                "description": "The brand of the phone product the user wants to consult or purchase.",
            },
            "phone_version": {
                "type": "string",
                "description": "The version of the phone product the user wants to consult or purchase.",
            },
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the brand and version of a phone product.
        """

        if not (temporary_memory and temporary_memory.user_memory):
            return ToolResponse(type="error", content="User memory is not available.")

        phone_brand = kwargs.get("phone_brand")
        phone_version = kwargs.get("phone_version")

        user_memory = temporary_memory.user_memory

        if phone_brand == user_memory.brand_name:
            return ToolResponse(
                type="finished", content="User requirements collected successfully."
            )

        brand_code = convert_band_name_to_code(phone_brand)
        if not brand_code:
            return ToolResponse(
                type="message",
                content=(
                    f'You should tell the user: "Our store does not carry {phone_brand} phones. '
                    'You can check out other brands like Samsung, iPhone, etc."'
                ),
            )

        user_memory.brand_code = brand_code
        user_memory.brand_name = phone_brand

        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

from typing import Any
from models.user_memory import PriceRequirement
from agents.base import AgentTemporaryMemory
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the price of a phone product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_phone_price_requirements",
        role: str = "Collect and update the user's requirements about the price of a phone product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The standard currency unit is VND. If the user provides the price in another currency, you need to convert it to VND.",
            "If the user use the slang or abbreviations for the currency unit, you need to clarify and convert them to VND.",
        ],
        cases_used: list[str] = [
            "The user mentions the information about the price of a phone product they want to consult or purchase.",
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
        Invoke the tool to collect and update the requirements about the price of a phone product.
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

        wandb_client.finish_call(call, output=temporary_memory.user_memory)
        return ToolResponse(
            type="finished", content="Price requirement collected successfully."
        )

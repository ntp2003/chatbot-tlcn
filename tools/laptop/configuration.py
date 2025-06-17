from typing import Any
from agents.base import AgentTemporaryMemory
from service.converter import convert_band_name_to_code
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client
from models.user_memory import NumericConfiguration


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the configuration of a phone product.
    """

    def __init__(
        self,
        name: str = "collect_and_update_laptop_configuration",
        role: str = "Collect and update the user's requirements about the configuration of a laptop product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The configuration of a laptop product includes hardware specifications such as color, brand, and other features.",
            "The brand refers to the name of the company or label that manufactures the laptop product.",
            "Extract the specific color mentioned by the user when they express interest in purchasing or searching for a laptop with that color. Only extract colors when the user is making a declarative statement about wanting a laptop of that color or asking to find laptops of that color. Do not extract colors from yes/no questions or when the user is asking about a specific laptop's color availability.",
        ],
        cases_used: list[str] = [
            "The user mentions the color of the laptop they want to consult or purchase.",
            "The user mentions the brand of the laptop they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "laptop_color": {
                "type": "string",
                "description": "The color of the laptop product that the user needs to search for or purchase. It should be a specific real-world color name, not a general term.",
                "examples": [
                    {
                        "input": "Tìm laptop có mầu <color>.",
                        "output": "<color>",
                    },
                    {
                        "input": "Laptop màu đen",
                        "output": "đen",
                    },
                    {
                        "input": "Laptop <A> có màu <color> không?",
                        "output": None,
                    },
                    {
                        "input": "Laptop này có màu xanh không?",
                        "output": None,
                    },
                    {
                        "input": "Laptop nào có màu <color>?",
                        "output": "<color>",
                    },
                    {
                        "input": "Có màu khác ko?",
                        "output": None,
                    },
                    {
                        "input": "laptop có màu j?",
                        "output": None,
                    },
                ],
            },
            "laptop_brand": {
                "type": "string",
                "description": "The brand of the laptop product the user wants to consult or purchase.",
                "examples": [
                    {
                        "input": "cần tư vấn về macbook air 13 M4 2025",
                        "output": "Apple",
                    },
                    {
                        "input": "tìm laptop Dell Inspiron 15",
                        "output": "Dell",
                    },
                    {
                        "input": "laptop HP có tốt không?",
                        "output": "HP",
                    },
                    {
                        "input": "laptop Lenovo ThinkPad X1",
                        "output": "Lenovo",
                    },
                    {
                        "input": "tôi muốn mua laptop khác",
                        "output": None,
                    },
                ],
            },
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the requirements about the configuration of a phone product.
        """
        if not (temporary_memory and temporary_memory.user_memory):
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )

        laptop_color = kwargs.get("laptop_color", None)

        temporary_memory.user_memory.color = (
            laptop_color or temporary_memory.user_memory.color
        )

        laptop_brand = kwargs.get("laptop_brand")
        if laptop_brand == temporary_memory.user_memory.brand_name:
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

        temporary_memory.user_memory.brand_code = brand_code if brand_code else None
        temporary_memory.user_memory.brand_name = laptop_brand if laptop_brand else None

        wandb_client.finish_call(call, output=temporary_memory.user_memory)
        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

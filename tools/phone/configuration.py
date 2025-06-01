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
        name: str = "collect_and_update_phone_configuration",
        role: str = "Collect and update the user's requirements about the configuration of a phone product for consultation or search.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "The configuration of a phone product includes hardware specifications such as storage (ROM), color, and other features.",
            "Extract the specific color mentioned by the user when they express interest in purchasing or searching for a phone with that color. Only extract colors when the user is making a declarative statement about wanting a phone of that color or asking to find phones of that color. Do not extract colors from yes/no questions or when the user is asking about a specific phone's color availability.",
            "Extract exact phone storage (ROM) values as min=max=value, ranges as min/max boundaries, open-ended ranges with reasonable upper bounds, ignore non-storage specs (RAM/battery), return null if no storage requirements found.",
        ],
        cases_used: list[str] = [
            "The user mentions the color or storage of the phone they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "phone_color": {
                "type": "string",
                "description": "The color of the phone product that the user needs to search for or purchase.",
                "examples": [
                    {
                        "input": "Tìm điện thoại có mầu <color>.",
                        "output": "<color>",
                    },
                    {
                        "input": "Điện thoại màu đen",
                        "output": "đen",
                    },
                    {
                        "input": "Điện thoại <A> có màu <color> không?",
                        "output": None,
                    },
                    {
                        "input": "Điện thoại này có màu xanh không?",
                        "output": None,
                    },
                    {
                        "input": "Điện thoại nào có màu <color>?",
                        "output": "<color>",
                    },
                ],
            },
            "phone_storage": {
                "type": "object",
                "title": "Phone Storage (ROM)",
                "description": "The storage capacity of the phone product that the user needs to search for or purchase.",
                "properties": {
                    "min_value": {
                        "type": "integer",
                        "description": "The minimum storage capacity (ROM) in GB that the user requires.",
                    },
                    "max_value": {
                        "type": "integer",
                        "description": "The maximum storage capacity (ROM) in GB that the user requires.",
                    },
                },
                "examples": [
                    {
                        "input": "Tìm điện thoại có dung lượng <min_value>GB đến <max_value>GB.",
                        "output": {
                            "min_value": "<min_value>",
                            "max_value": "<max_value>",
                        },
                    },
                    {
                        "input": "điện thoại rom 8gb",
                        "output": {"min_value": 8, "max_value": 8},
                    },
                    {
                        "input": "Điện thoại có ram <RAM requirement>",
                        "output": None,
                    },
                    {
                        "input": "điện thoại này có mẫu 512GB không?",
                        "output": None,
                    },
                    {
                        "input": "Xem thông tin mẫu 64GB",
                        "output": {"min_value": 64, "max_value": 64},
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

        phone_color = kwargs.get("phone_color", None)
        phone_storage = kwargs.get("phone_storage", {}) or {}
        phone_storage = NumericConfiguration(**phone_storage)

        temporary_memory.user_memory.color = (
            phone_color or temporary_memory.user_memory.color
        )
        if phone_storage.min_value is not None or phone_storage.max_value is not None:
            temporary_memory.user_memory.rom = phone_storage

        wandb_client.finish_call(call, output=temporary_memory.user_memory)
        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

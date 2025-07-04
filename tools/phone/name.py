from typing import Any
from agents.base import AgentTemporaryMemory
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the requirements about the name of the specific phone product the user is interested in.
    """

    def __init__(
        self,
        name: str = "collect_and_update_phone_name_requirements",
        role: str = "Collect and update the user's requirements about the name of the specific phone product they are interested in.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            'If the user is interested in a specific phone product in the list of suggestions shown in the previous conversation (e.g., "điện thoại đầu tiên", "cái thứ <number>", ...), you should set the phone_name parameter to the name of that phone product.',
        ],
        cases_used: list[str] = [
            "The user mentions the name of the specific phone product they are interested in.",
            "The user mentions the information about the name of the specific phone product they want to consult or purchase.",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "phone_name": {
                "type": "string",
                "description": "The name of the phone product the user is interested in."
                " If the user is interested in a specific phone product in the list of suggestions shown in the previous conversation, you should set this parameter to the name of that phone product.",
                "examples": [
                    {
                        "the suggested list of phones": "1. Phone A\n2. Phone B\n3. Phone C",
                        "input": "I am interested in the first phone.",
                        "output": "Phone A",
                    },
                    {
                        "the suggested list of phones": "1. Phone A v1\n2. Phone B v2\n3. Phone C v3",
                        "input": "phone B",
                        "output": "Phone B v2",
                    },
                    {
                        "the suggested list of phones": "1. Phone brand A series 1\n2. Phone brand B series 2\n3. Phone brand C series 3",
                        "input": "I want to buy the phone series 1.",
                        "output": "Phone brand A series 1",
                    },
                    {
                        "The one suggested phone in the consultation process": "Phone X",
                        "input": "details about it",
                        "output": "Phone X",
                    },
                    {
                        "input": "điện thoại iphone",
                        "output": None,
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
        Invoke the tool to collect and update the requirements about the name of the specific phone product the user is interested in.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )
        phone_name = kwargs.get("phone_name")

        temporary_memory.user_memory.product_name = (
            phone_name if phone_name else temporary_memory.user_memory.product_name
        )
        wandb_client.finish_call(call, output=temporary_memory.user_memory)
        return ToolResponse(
            type="finished", content="User requirements collected successfully."
        )

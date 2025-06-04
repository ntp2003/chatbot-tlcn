from typing import Any
from agents.base import AgentTemporaryMemory
from models.user_memory import UserIntent
from tools.base import ToolResponse
from tools.langgpt_template import LangGPTTemplateTool
from service.wandb import client as wandb_client


class Tool(LangGPTTemplateTool):
    """
    Tool for collecting and updating the user's intent
    """

    def __init__(
        self,
        name: str = "collect_and_update_user_intent",
        role: str = "Collect and update the user's intent about consulting or searching for a phone product.",
        prerequisites: list[str] = [],
        rules: list[str] = [
            "Collect and update based on the latest user message.",
            "Analyze whether the user is requesting additional phone product suggestions.",
        ],
        cases_used: list[str] = [
            "The user expresses a desire for consultation or suggestions about other phone products (e.g., 'Are there any other phones?', 'Are there any other phones in this segment?', ...).",
        ],
        returns: list[str] = [],
        params: dict[str, Any] = {
            "is_user_needs_other_suggestions": {
                "type": "boolean",
                "default": False,
                "description": "Return True if the user expresses a desire for additional phone product suggestions or alternatives compared to previously mentioned options (e.g., 'Are there any other phones?', 'What other phones are available in this segment?', 'Can you suggest similar alternatives?'). Return False otherwise.",
            }
        },
    ):
        super().__init__(name, role, prerequisites, rules, cases_used, returns, params)

    def invoke(
        self, temporary_memory: AgentTemporaryMemory | None, *args, **kwargs
    ) -> ToolResponse:
        """
        Invoke the tool to collect and update the user's intent about consulting or searching for a phone product.
        """

        if not temporary_memory or not temporary_memory.user_memory:
            return ToolResponse(type="error", content="User memory is not available.")

        call = wandb_client.create_call(
            op=self.name,
            inputs={"kwargs": kwargs, "user_memory": temporary_memory.user_memory},
        )
        is_user_needs_other_suggestions: bool = kwargs.get(
            "is_user_needs_other_suggestions", False
        )

        if not temporary_memory.user_memory.intent:
            temporary_memory.user_memory.intent = UserIntent()

        temporary_memory.user_memory.intent.is_user_needs_other_suggestions = (
            is_user_needs_other_suggestions
        )

        wandb_client.finish_call(call, output=temporary_memory.user_memory)
        return ToolResponse(
            type="finished", content="User intent collected successfully."
        )

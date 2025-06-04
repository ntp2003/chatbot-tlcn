from typing import Any
from .base import ToolBase, ToolResponse
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


class LangGPTTemplateTool(ToolBase):
    def __init__(
        self,
        name: str,
        role: str,
        prerequisites: list[str] = [],
        rules: list[str] = [],
        cases_used: list[str] = [],
        returns: list[str] = [],
        params: dict[str, Any] = {},
    ):
        self.role = role
        self.prerequisites = prerequisites
        self.rules = rules
        self.cases_used = cases_used
        self.returns = returns

        description = f"# ROLE:\n{self.role}"

        if self.prerequisites:
            description += f"\n\n## PREREQUISITES:\n{[f'- {prerequisite}' for prerequisite in self.prerequisites]}"

        if self.cases_used:
            description += (
                f"\n\n## CASES USED:\n{[f'- {case}' for case in self.cases_used]}"
            )

        if self.rules:
            description += f"\n\n## RULES:\n{[f'- {rule}' for rule in self.rules]}"

        if self.returns:
            description += (
                f"\n\n## RETURNS:\n{[ f'- {return_}' for return_ in self.returns]}"
            )

        super().__init__(name=name, description=description, parameters=params)

    def reload_tool_schema(self):
        self.description = f"# ROLE:\n{self.role}"
        if self.prerequisites:
            self.description += f"\n\n## PREREQUISITES:\n{[f'- {prerequisite}' for prerequisite in self.prerequisites]}"
        if self.cases_used:
            self.description += (
                f"\n\n## CASES USED:\n{[f'- {case}' for case in self.cases_used]}"
            )
        if self.rules:
            self.description += f"\n\n## RULES:\n{[f'- {rule}' for rule in self.rules]}"
        if self.returns:
            self.description += (
                f"\n\n## RETURNS:\n{[f'- {return_}' for return_ in self.returns]}"
            )
        return super().reload_tool_schema()

    def invoke(self, *args, **kwargs) -> ToolResponse:
        raise NotImplementedError()

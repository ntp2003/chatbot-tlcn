from typing import Any, Literal, Optional, OrderedDict
from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from overrides import override
from pydantic import ConfigDict, Field
from pydantic.json_schema import (
    GenerateJsonSchema,
    JsonSchemaValue,
    JsonSchemaMode,
    DEFAULT_REF_TEMPLATE,
)
from pydantic_core.core_schema import CoreSchema


class ToolResponse(BaseModel):
    type: Literal["finished", "navigate", "error", "message"]
    content: Optional[str] = None


# class GenerateToolJsonSchema(GenerateJsonSchema):
#     @override
#     def generate(
#         self, schema: CoreSchema, mode: JsonSchemaMode = "validation"
#     ) -> JsonSchemaValue:
#         schema = super().generate(schema, mode=mode)  # type: ignore
#         schema.pop("additionalProperties", None)
#         schema.pop("title", None)

#         # Định nghĩa thứ tự mong muốn
#         for prop in schema.get("properties", {}).values():
#             ordered = OrderedDict()
#             for key in [
#                 "title",
#                 "type",
#                 "enum",
#                 "default",
#                 "description",
#                 "properties",
#                 "examples",
#             ]:
#                 if key in prop:
#                     ordered[key] = prop[key]
#             others = set(prop.keys()) - set(ordered.keys())
#             other_dict = {key: prop[key] for key in others}
#             prop.clear()
#             prop.update(ordered)
#             prop.update(other_dict)

#         # ordered = OrderedDict()
#         # other_dict = {}
#         # for key in [
#         #     "type",
#         #     "properties",
#         #     "required",
#         #     "additionalProperties",
#         #     "examples",
#         # ]:
#         #     if key in schema:
#         #         ordered[key] = schema[key]
#         return schema


# class ToolParams(BaseModel):
#     a: int = Field(
#         description="The first number",
#         default=1,
#     )
#     b: int = Field(
#         description="The second number",
#         default=2,
#     )
#     response: ToolResponse | None = Field(
#         description="Response from the tool", default=None
#     )


#     @classmethod
#     def model_json_schema(
#         cls,
#         by_alias: bool = True,
#         ref_template: str = DEFAULT_REF_TEMPLATE,
#         schema_generator: type[GenerateJsonSchema] = GenerateToolJsonSchema,
#         mode: JsonSchemaMode = "validation",
#     ) -> dict[str, Any]:
#         return super().model_json_schema(
#             by_alias=by_alias,
#             ref_template=ref_template,
#             schema_generator=schema_generator,
#             mode=mode,
#         )


class ToolBase:
    tool_schema: ChatCompletionToolParam

    def __init__(self, name: str, description: str, parameters: dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.tool_schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        key: value for key, value in self.parameters.items()
                    },
                },
            },
        }

    def reload_tool_schema(self):
        self.tool_schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        key: value for key, value in self.parameters.items()
                    },
                },
            },
        }

    def invoke(self, *args, **kwargs) -> ToolResponse:
        raise NotImplementedError()

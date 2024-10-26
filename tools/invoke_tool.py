from .faq import tool_json_schema as faq_tool_json_schema, invoke as invoke_faq_tool
from openai.types.chat import ChatCompletionToolParam


def get_tool_name(tool_json_schema: ChatCompletionToolParam) -> str:
    return tool_json_schema["function"]["name"]


def invoke(tool_name: str, args: dict, user_input: str | None = None) -> str:
    print("Invoking tool:", tool_name)
    print("Args:", args)

    if tool_name == get_tool_name(faq_tool_json_schema):
        print("Invoking FAQ tool")
        return invoke_faq_tool(args.get("question"))  # type: ignore

    return "Tool name not found"

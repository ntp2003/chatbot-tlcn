from uuid import UUID
from .faq import tool_json_schema as faq_tool_json_schema, invoke as invoke_faq_tool
from .collect_requirement import (
    tool_json_schema as collect_requirement_tool_json_schema,
    invoke as invoke_collect_requirement_tool,
)
from .search_phone_database import (
    tool_json_schema as search_phone_database_tool_json_schema,
    invoke as invoke_search_phone_database_tool,
)
from .collect_user_contact_info import (
    tool_json_schema as collect_user_contact_info_tool_json_schema,
    invoke as invoke_collect_user_contact_info_tool,
)
from openai.types.chat import ChatCompletionToolParam
import chainlit as cl
from repositories.user_memory import get_user_memory_by_thread_id, create_user_memory
from models.user_memory import CreateUserMemoryModel


def get_tool_name(tool_json_schema: ChatCompletionToolParam) -> str:
    return tool_json_schema["function"]["name"]


@cl.step(type="tool")
def invoke_with_chainlit(
    user_id: UUID,
    thread_id: UUID,
    tool_name: str,
    args: dict,
    user_input: str | None = None,
) -> str:
    return invoke(user_id, thread_id, tool_name, args, user_input)


def invoke(
    user_id: UUID,
    thread_id: UUID,
    tool_name: str,
    args: dict,
    user_input: str | None = None,
) -> str:
    user_memory = get_user_memory_by_thread_id(thread_id)
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )

    print("\n\n\n")
    print("Invoking tool:", tool_name)
    print("Args:", args)
    print("\n\n\n")

    if tool_name == get_tool_name(faq_tool_json_schema):
        return invoke_faq_tool(args.get("faq_question"))  # type: ignore

    if tool_name == get_tool_name(search_phone_database_tool_json_schema):
        return invoke_search_phone_database_tool(
            user_memory,
            args.get("phone_brand"),
            args.get("phone_name"),
            args.get("user_needs_other_suggestions", False),
        )

    if tool_name == get_tool_name(collect_requirement_tool_json_schema):
        return invoke_collect_requirement_tool(
            user_memory, args.get("user_demand"), args.get("price_requirement", {})
        )

    if tool_name == get_tool_name(collect_user_contact_info_tool_json_schema):
        return invoke_collect_user_contact_info_tool(
            user_memory, args.get("phone_number"), args.get("email")
        )

    return "Tool name not found"

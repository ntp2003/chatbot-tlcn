from openai.types.chat import ChatCompletionToolParam
from models.user_memory import UserMemoryModel, PriceRequirement
from repositories.user_memory import update_user_memory
from models.user_memory import UserDemand
from .utils.search import PhoneFilter
from repositories.redis import set_value

tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "collect_and_update_user_requirements_tool",
        "description": """
# ROLE
Collect and update the user's requirements and demands.

## RULES
- You need to clarify the user's demand accurately.
- Base on the chat context to identify the user's demands and requirements effectively.
- The standard currency unit is VND. If the user provides the price in another currency, you need to convert it to VND.
- If the user use the slang or abbreviations for the currency unit, you need to clarify and convert them to VND.

## RETURNS
- Intructions for next actions after collecting and updating the user's requirements and demands.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "user_demand": {
                    "type": "string",
                    "enum": ["mobile phone", "another product"],
                    "description": "The user's demand for consultation or purchase.\n"
                    "Return 'mobile phone' if the user is interested in purchasing or seeking consultation regarding a mobile phone.\n"
                    "Otherwise, return 'another product'.",
                },
                "price_requirement": {
                    "type": "object",
                    "description": "The user's price requirement for the product they are interested in or want to consult.",
                    "properties": {
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
                },
            },
        },
    },
}


def invoke(
    user_memory: UserMemoryModel, user_demand: str | None, price_requirement: dict
) -> str:
    if user_demand:
        user_memory.user_demand = UserDemand(user_demand)

    if price_requirement:
        old_filter = PhoneFilter(
            min_price=user_memory.min_price, max_price=user_memory.max_price
        )
        approximate_price = price_requirement.get("approximate_price")
        min_price = price_requirement.get("min_price")
        max_price = price_requirement.get("max_price")

        price_requirement_obj = PriceRequirement(
            approximate_price, min_price, max_price
        )

        user_memory.min_price = price_requirement_obj.min_price
        user_memory.max_price = price_requirement_obj.max_price
        new_filter = PhoneFilter(
            min_price=user_memory.min_price, max_price=user_memory.max_price
        )
        if not old_filter.__eq__(new_filter):
            user_memory.product_name = None
            set_value(str(user_memory.thread_id), 0)

    update_user_memory(user_memory)

    if user_memory.user_demand is None:
        return 'You should ask the user: "Which product are you interested in?"'

    if user_memory.user_demand == UserDemand.MOBILE_PHONE:
        return (
            "Collected and updated the user's requirement for a mobile phone.\n"
            "## NEXT ACTIONS\n"
            "- You must proceed to search the phone database."
        )

    return (
        "Your store has not supported this product yet. "
        "You must suggest the user to phone products or contact the store though hotline or email for more information."
    )

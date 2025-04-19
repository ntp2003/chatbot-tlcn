from openai.types.chat import ChatCompletionToolParam
from models.phone import Phone, PhoneModel
from models.user_memory import UserMemoryModel
from repositories.user_memory import update_user_memory
from repositories.phone import search_phone_by_filter, search_phone_by_phone_name
from .utils.search import PhoneFilter
from service.converter import convert_band_name_to_code
from .utils.config import BRAND_DEFAULT, ASK_CONTACT_INFO_FOR_FURTHER_CONSULT_PROMPT
from repositories.redis import set_value, get_value

tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "search_phone_database_tool",
        "description": """
## ROLE
Search the phone database.

## PREREQUISITES
- Collected and updated the user's requirements and identified the user's demands accurately.
- The user interested in purchasing or seeking consultation regarding information via phone.

## RULES
- If the user is interested in a specific phone product in the list of suggestions shown in the previous conversation (e.g., "điện thoại đầu tiên", "cái thứ <number>", ...), you should set the phone_name parameter to the name of that phone product.

## RETURNS
- Information about the phone product that matches the user's requirements or the other suggestions if the exact match is not found.
- Intructions to guide you respond to the user's queries effectively.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_brand": {
                    "type": "string",
                    "description": "The brand of the phone the user is interested in.",
                },
                "phone_name": {
                    "type": "string",
                    "description": "The name of the phone product the user is interested in."
                    " If the user is interested in a specific phone product in the list of suggestions shown in the previous conversation, you should set this parameter to the name of that phone product.",
                },
                "user_needs_other_suggestions": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Return True if the user expresses a desire for consultation or suggestions about other phone products "
                        '(e.g., "Are there any other phones?", "Are there any other phones in this segment?", ...) compared to the previous suggestions.'
                        " Otherwise, return False."
                    ),
                },
            },
        },
    },
}


def invoke(
    user_memory: UserMemoryModel,
    phone_brand: str | None,
    phone_name: str | None,
    user_needs_other_suggestions: bool,
) -> str:
    phone_name = phone_name if phone_name != user_memory.product_name else None
    brand_code = convert_band_name_to_code(phone_brand)
    page = get_value(str(user_memory.thread_id))
    page = int(page) if page else 0  # type: ignore

    if user_needs_other_suggestions:
        page += 1

    if phone_brand and not brand_code:
        return f'You should tell the user: "Our store does not carry {phone_brand} phones. You can check out other brands like Samsung, iPhone, etc."'

    if brand_code and user_memory.brand_code not in [
        None,
        BRAND_DEFAULT,
        brand_code,
    ]:
        user_memory.product_name = None
        page = 0

    if brand_code:
        user_memory.brand_code = brand_code
    if phone_name:
        user_memory.product_name = phone_name
    update_user_memory(user_memory)
    set_value(str(user_memory.thread_id), page)

    if not user_memory.brand_code and not user_memory.product_name:
        user_memory.brand_code = BRAND_DEFAULT
        update_user_memory(user_memory)
        return "You must ask the user for the brand of the phone they are interested in such as Samsung, iPhone, etc.\n"

    if user_memory.product_name:
        return (
            (
                _search_phone_by_name(user_memory.product_name)
                + ASK_CONTACT_INFO_FOR_FURTHER_CONSULT_PROMPT
            )
            if not user_memory.has_contact_info()
            else _search_phone_by_name(user_memory.product_name)
        )

    phone_filter = PhoneFilter(
        brand_code=(
            user_memory.brand_code if user_memory.brand_code != BRAND_DEFAULT else None
        ),
        max_price=user_memory.max_price,
        min_price=user_memory.min_price,
    )

    return (
        (
            _search_phone_by_filter(phone_filter, page)
            + ASK_CONTACT_INFO_FOR_FURTHER_CONSULT_PROMPT
        )
        if not user_memory.has_contact_info()
        else _search_phone_by_filter(phone_filter, page)
    )


def _search_phone_by_name(
    phone_name: str, threshold_1: float = 0.75, threshold_2: float = 0.6
) -> str:
    result_text = ""
    phone = search_phone_by_phone_name(phone_name, 1, threshold_1)
    if len(phone) > 0:
        result_text = f"## Below is the information of the phone product that the user is interested in:\n"
        return (
            result_text
            + phone[0].to_text(
                inclue_key_selling_points=True,
                include_promotion=True,
                include_sku_variants=True,
                include_description=True,
            )
            + "\n"
            + "## If the user has any questions about the product, you can provide shortly the answer based on the information above. You don't need to provide the information that not related to the user's question."
        )
    else:
        phones = search_phone_by_phone_name(phone_name, 3, threshold_2)

        if len(phones) > 0:
            result_text = f"## The phone product that the user is interested in with name '{phone_name}' is not found. Below are some suggestions for the user:\n"
            result_text += _phones_to_text(phones)
        else:
            result_text += "You must say: 'I'm sorry, I couldn't find the phone you're looking for. You can look for other phones.'"

    return result_text


def _search_phone_by_filter(phone_filter: PhoneFilter, page: int = 0) -> str:
    result_text = None
    phones = search_phone_by_filter(phone_filter, Phone.score.expression, page=page)
    filter_json = phone_filter.model_dump(exclude_none=True)
    filter_remove_list = []

    if len(phones) > 0:
        result_text = f"## Below is the information of the phone product that matches the user's requirements:\n"
        result_text += _phones_to_text(phones)

    while len(phones) == 0 and len(list(filter_json.keys())) > 0:
        pop_item = filter_json.popitem()
        filter_remove_list.append(f"{pop_item[0]} is {pop_item[1]}")
        phones = search_phone_by_filter(
            PhoneFilter(**filter_json), Phone.score.expression, page=page
        )
        if len(phones) > 0:
            result_text = (
                f"## The phone product that matches the user's requirements ({', '.join(filter_remove_list)}) is not found. "
                "Below are some suggestions for the user:\n"
            )
            result_text += _phones_to_text(phones)
            break

    if result_text is None and page > 0:
        result_text = 'There are no more products to suggest to the user, so next, please say: "Sorry, apart from the products we just mentioned, it seems we do not have any other items that match your needs. Do you have any other requirements? We offer a wide range of products that might suit you."'

    return (
        result_text
        if result_text
        else "You must say: 'I'm sorry, I couldn't find the phone you're looking for. You can look for other phones.'"
    )


def _phones_to_text(phones: list[PhoneModel]) -> str:
    result_text = ""
    for i, phone in enumerate(phones):
        result_text += f"{i+1}. {phone.to_text(inclue_key_selling_points=True)}\n"
    return result_text

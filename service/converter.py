from repositories.brand import query_by_semantic
from email_validator import EmailNotValidError, validate_email
import phonenumbers


def convert_band_name_to_code(
    brand_name: str | None, threshold: float = 0.7
) -> str | None:
    if not brand_name:
        return None

    brand = query_by_semantic(f"Brand: {brand_name}", 1, threshold)

    if len(brand) == 0:
        return None

    return brand[0].id


def convert_to_standard_email(raw_email: str | None) -> str | None:
    if not raw_email:
        return None

    try:
        email = validate_email(raw_email)
        return email.normalized
    except EmailNotValidError:
        return None


def convert_to_standard_phone_number(raw_phone_numbers: str | None) -> str | None:
    if not raw_phone_numbers:
        return None

    try:
        phone_numbers = phonenumbers.parse(raw_phone_numbers, "VN")
        if (
            phonenumbers.is_valid_number(phone_numbers)
            and phone_numbers.national_number
        ):
            return "0" + str(phone_numbers.national_number)
    except phonenumbers.NumberParseException:
        return None

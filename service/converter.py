from repositories.brand import query_by_semantic
from email_validator import EmailNotValidError, validate_email # validate and normalize email
import phonenumbers # parse và validate phone number

# convert brand name to brand_code
def convert_band_name_to_code(
    brand_name: str | None, threshold: float = 0.7
) -> str | None:
    '''
    args: brand_name và ngưỡng simiilarity threshold
    Tìm brand gần nhất với brand_name truyền vào
    Trả về brand_code của brand đó
    '''
    if not brand_name:
        return None

    brand = query_by_semantic(f"Brand: {brand_name}", 1, threshold) # lấy ra BrandModel gần nhất với brand_name

    if len(brand) == 0:
        return None

    return brand[0].id #lấy ra brand_code (id) của brand đầu tiên trong list brand result query_by_semantic

    '''
    brand_code = convert_brand_name_to_code("Sam Sung") # Return Brand_Model(SamSung).id
    '''

# chuẩn hóa email
def convert_to_standard_email(raw_email: str | None) -> str | None:
    if not raw_email:
        return None

    try:
        email = validate_email(raw_email) # validate raw_email
        return email.normalized # chuẩn hóa email
    except EmailNotValidError:
        return None
'''
email = convert_to_standard_email("User@EXAMPLE.COM")  # return 'user@example.com
'''
# chuẩn hóa sdt theo định dạng VN
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
'''
phone = convert_to_standard_phone_number("+84912345678")  # return '0912345678'
'''
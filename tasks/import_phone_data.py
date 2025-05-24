import math
import time
import httpx
import jsonlines
from sqlalchemy import table
from db import Session
from env import env
from bs4 import BeautifulSoup
import os
from models.phone import CreatePhoneModel, Phone
from repositories.phone import upsert_phone
from service.embedding import get_embedding

"""
How to run:
python
from tasks.import_phone_data import *
import_jsonl_to_database()
"""

post_url = "https://papi.fptshop.com.vn/gw/v1/public/fulltext-search-service/category"

header = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "content-type": "application/json",
    "order-channel": "1",
    "origin": "https://fptshop.com.vn",
    "priority": "u=1, i",
    "referer": "https://fptshop.com.vn/",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}

category_slug = "dien-thoai"

file_path = "tasks/phone_data.jsonl"


# Đọc dữ liệu từ file jsonl và import vào database bằng cách gọi  import_batch_data_to_database()
def import_jsonl_to_database(
    file_path: str = file_path,
    start_offset: int = 0,
    limit: int | float = math.inf,
    batch_size: int = 10,
):
    if not os.path.isfile(file_path):
        extract_fpt_phone_data(file_path=file_path)

    with jsonlines.open(file_path) as reader:
        current_offset = -1
        batch = []
        for phone in reader:
            current_offset += 1
            if start_offset <= current_offset < start_offset + limit:
                batch.append(phone)
                if len(batch) // batch_size == 1:
                    import_batch_data_to_database(batch)
                    batch = []
        if len(batch) > 0:
            import_batch_data_to_database(batch)


# gửi dữ liệu lên db bằng cách gọi upsert_phone()
def import_batch_data_to_database(batch: list[dict]):
    for phone in batch:
        id = phone.get("code")
        name = phone.get("name", "not known")
        slug = phone.get("slug", "dien-thoai")
        brand_code = phone.get("brand", {}).get("code")
        product_type = phone.get("productType", {}).get("name")
        description = phone.get("description", "not description")
        promotions = phone.get("promotions", [])
        skus = phone.get("skus", [])
        key_selling_points = phone.get("keySellingPoints", [])
        price = phone.get("price", -1)
        score = phone.get("score", 0)
        # name_embedding = get_embedding(name)
        name_embedding = get_embedding(f"Phone Name: {name}")
        if id is not None:
            print(f"Upserting phone: {id}, {name}, {brand_code}")

            upsert_phone(
                CreatePhoneModel(
                    id=id,
                    name=name,
                    slug=slug,
                    brand_code=brand_code,
                    product_type=product_type,
                    description=description,
                    promotions=promotions,
                    skus=skus,
                    key_selling_points=key_selling_points,
                    price=price,
                    score=score,
                    data=phone,
                    name_embedding=name_embedding,
                )
            )


def extract_fpt_phone_data(
    skip_count: int = 0,
    batch_size: int = 16,
    sleep_after_batch: int | None = None,
    limit: int | float = math.inf,
    file_path: str = file_path,
):
    start_time = time.time()
    print("Import is running...")

    # Gui req API lấy ds sản phẩm trong danh mục điện thoại
    with httpx.Client() as client:
        imported_count = 0

        body = {
            "sortMethod": "noi-bat",
            "slug": category_slug,
            "skipCount": skip_count,
            "maxResultCount": batch_size,
            "categoryType": "category",
        }

        response = client.post(
            post_url,
            json=body,
            headers=header,
            timeout=20.0,
        )
        response.raise_for_status()  # check for error
        response_data = dict(response.json())
        total_count = response_data.get("totalCount")
        items = response_data.get("items")

        if total_count is None or total_count <= 0 or items is None:
            raise Exception(f"not found category ({category_slug})")

        # Lấy mô tả của sản phẩm
        for item in items:
            item["description"] = get_description(item.get("slug"))

        # Ghi dữ liệu vào file jsonl
        if len(items) > limit:
            write_to_jsonlines(items[0:limit], file_path)
            imported_count += len(items)
        else:
            while len(items) > 0 and imported_count + len(items) <= limit:
                write_to_jsonlines(items, file_path)
                imported_count += len(items)
                if len(items) < batch_size:
                    break
                if sleep_after_batch is not None:
                    time.sleep(sleep_after_batch)

                body["skipCount"] = imported_count

                response = client.post(
                    post_url,
                    json=body,
                    headers=header,
                    timeout=20.0,
                )

                response.raise_for_status()
                response_data = dict(response.json())
                items = response_data.get("items")
                if items is None:
                    raise Exception(f"not found category ({category_slug})")
                for item in items:
                    description = get_description(item.get("slug"))
                    if description:
                        item["description"] = description

        print(f"Import successful {imported_count} {category_slug} items")
        print("--- %s seconds ---" % (time.time() - start_time))


# Ghi dữ liệu vào file jsonl
def write_to_jsonlines(data: dict | list[dict], file_path: str = file_path):
    with jsonlines.open(file_path, "a") as writer:
        if type(data) is dict:
            writer.write(data)
        else:
            writer.write_all(data)


from markdownify import MarkdownConverter


class IgnoreImageConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """

    def convert_img(self, el, text, parent_tags):
        return ""


# Create shorthand method for conversion
def md(html, **options):
    return IgnoreImageConverter(**options).convert(html)


# Lấy thông tin mô tả của sản phẩm
def get_description(item_slug: str) -> str | None:
    url = f"{env.FPTSHOP_BASE_URL}/{item_slug}"

    response = httpx.get(url, headers=header)
    data = BeautifulSoup(response.content, "html.parser")
    description_object = data.find("div", {"id": "MoTaSanPham"})
    if description_object is None:
        return None

    description_object = description_object.select_one(  # type: ignore
        # "div.relative.w-full .description-container"
        "div.ProductContent_description-container__miT3z"
    )

    if description_object is None:
        return None

    i_tag = description_object.find("i")
    if i_tag is not None:
        i_tag.decompose()

    return md(str(description_object)).replace("\n\n", "\n")


"""
How to run:
python
from tasks.import_phone_data import *
update_embedding()
"""


def update_embedding():
    with Session() as session:
        phones = session.query(Phone).all()
        for phone in phones:
            phone.name_embedding = get_embedding(f"Phone Name: {phone.name}")
            session.add(phone)

        session.commit()

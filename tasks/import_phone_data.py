import math
import time
import httpx
import jsonlines
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
import_phone_data_jsonl_to_database()
"""
## vào trang danh sách điện thoại , f12 quan sat Network 
post_url = "https://papi.fptshop.com.vn/gw/v1/public/fulltext-search-service/category"
# copy từ phần headers trong network 
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


# read data from jsonl file and import to database iterately using import_batch_data_to_database()
def import_phone_data_jsonl_to_database(
    file_path: str = file_path,
    start_offset: int = 0,
    limit: int | float = math.inf,
    batch_size: int = 10,
):
    if not os.path.isfile(file_path):
        # if not exis file data jsonl -> call extract func to crawl data to file jsonl path
        extract_fpt_phone_data(file_path=file_path)

    #open in format jsonl , each line is a JSON object
    with jsonlines.open(file_path) as reader:
        current_offset = -1
        batch = []
        for phone in reader:
            current_offset += 1
            if start_offset <= current_offset < start_offset + limit:
                batch.append(phone)
                if len(batch) // batch_size == 1:
                    import_batch_data_to_database(batch)
                    batch = []  # reset batch after imported 
        if len(batch) > 0:  # process the final batch
            import_batch_data_to_database(batch)


# send data in batch data to db using upsert_phone()
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
        name_embedding = get_embedding(name)
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

# crawl data from fpt
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

        # init request , lấy trong phần request payload là cấu trúc body được sử dụng
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
                if len(items) < batch_size: # hết sản phẩm
                    break
                if sleep_after_batch is not None:
                    time.sleep(sleep_after_batch)

                body["skipCount"] = imported_count  # cập nhật skipCount để lấy batch tiếp theo (skipCount = 16 , lấy 16 items tiếp theo , skipCount = 32..)
                # lặp lại cho đến khi lấy đủ dữ liệu
                response = client.post(
                    post_url,
                    json=body,
                    headers=header,
                    timeout=20.0,
                )

                response.raise_for_status()
                response_data = dict(response.json())
                items = response_data.get("items") # get batch_size = 16 items đầu tiên
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


# Lấy thông tin mô tả của sản phẩm
def get_description(item_slug: str) -> str | None:
    # truy cập vào trang chi tiết của sản phẩm
    url = f"{env.FPTSHOP_BASE_URL}/{item_slug}"

    response = httpx.get(url, headers=header)
    data = BeautifulSoup(response.content, "html.parser") # BS parse html
    # tìm và trích xuất nội dung mô tả từ element có id ThongTinSanPham
    description_object = data.find("div", {"id": "ThongTinSanPham"})
    if description_object is None:
        return None

    description_object = description_object.select_one(  # type: ignore
        #"div.relative.w-full .description-container"
        "div.ProductContent_description-container__miT3z"
    )

    if description_object is None:
        return None

    contents = description_object.select("p, h2")

    return "\n".join([i.get_text() for i in contents])


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

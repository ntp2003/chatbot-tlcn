import math
import time
import httpx
import jsonlines
import os
import sys

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import env
from bs4 import BeautifulSoup
from models.laptop import CreateLaptopModel  # Cần tạo model này
from repositories.laptop import upsert_laptop  # Cần tạo repository này
from service.embedding import get_embedding

"""
How to run:
python
from tasks.import_laptop_data import *
import_laptop_data_jsonl_to_database()
"""

'''
Cần chạy extract đưa data vào jsonl rồi từ file jsonl import data cho brands trước rồi mới import data cho laptop
'''

# request URL (API)
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

category_slug = "may-tinh-xach-tay"  

file_path = "tasks/laptop_data.jsonl"  

def import_laptop_data_jsonl_to_database(
    file_path: str = file_path,
    start_offset: int = 0,
    limit: int | float = math.inf,
    batch_size: int = 10,
):
    if not os.path.isfile(file_path):
        extract_fpt_laptop_data(file_path=file_path)

    with jsonlines.open(file_path) as reader:
        current_offset = -1
        batch = []
        for laptop in reader:
            current_offset += 1
            if start_offset <= current_offset < start_offset + limit:
                batch.append(laptop)
                if len(batch) >= batch_size :
                    import_batch_data_to_database(batch)
                    batch = []
        if len(batch) > 0:
            import_batch_data_to_database(batch)

def import_batch_data_to_database(batch: list[dict]):
    for laptop in batch:
        id = laptop.get("code")
        name = laptop.get("name", "not known")
        slug = laptop.get("slug", "laptop")
        brand_code = laptop.get("brand", {}).get("code")
        product_type = laptop.get("productType", {}).get("name")
        description = laptop.get("description", "not description")
        promotions = laptop.get("promotions", [])
        skus = laptop.get("skus", [])
        key_selling_points = laptop.get("keySellingPoints", [])
        price = laptop.get("price", -1)
        score = laptop.get("score", 0)
        name_embedding = get_embedding(name)
        
        if id is not None:
            print(f"Upserting laptop: {id}, {name}, {brand_code}")

            try:
                upsert_laptop(
                    CreateLaptopModel(
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
                        data=laptop,
                        name_embedding=name_embedding,
                    )
                )
            except Exception as e:
                print(f"Error upserting laptop: {id}, {name}, {brand_code}")
                print(e)

def extract_fpt_laptop_data(
    skip_count: int = 0,
    batch_size: int = 16,
    sleep_after_batch: int | None = None,
    limit: int | float = math.inf,
    file_path: str = file_path,
):
    start_time = time.time()
    print("Import is running...")

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
        response.raise_for_status()
        response_data = dict(response.json())
        total_count = response_data.get("totalCount")
        items = response_data.get("items")

        if total_count is None or total_count <= 0 or items is None:
            raise Exception(f"not found category ({category_slug})")

        # Lấy mô tả của sản phẩm
        for item in items:
            item["description"] = get_description(item.get("slug"))

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

def write_to_jsonlines(data: dict | list[dict], file_path: str = file_path):
    with jsonlines.open(file_path, "a") as writer:
    #with jsonlines.open(file_path, "w") as writer: 
    # Cach nay co van de , vi qa moi batch data lai dong mo file 1 lan => Dan den batch moi se ghi de len data batch cu
        if type(data) is dict:
            writer.write(data)
        else:
            writer.write_all(data)

def get_description(item_slug: str) -> str | None:
    '''
    Lấy nội dung mô tả sản phẩm từ trang chi tiết FPTShop.

    Args:
        item_slug: Phần slug của URL sản phẩm (ví dụ: 'dien-thoai/samsung-galaxy-m55').
    '''
    url = f"{env.FPTSHOP_BASE_URL}/{item_slug}"

    response = httpx.get(url, headers=header)
    data = BeautifulSoup(response.content, "html.parser")
    description_object = data.find("div", {"id": "ThongTinSanPham"})
    if description_object is None:
        return None

    description_object = description_object.select_one(
        #"div.relative.w-full .description-container"
        #"div.ProductContent_description-container__miT3z"
        "div.ProductContent_description-container__miT3z"
    )

    if description_object is None:
        print(f"Không tìm thấy description container (ProductContent_description-container__miT3z) cho slug: {item_slug}")
        return None

    #contents = description_object.select("p, h2")
    contents = description_object.select("p,h3")
    if not contents:
        print(f"Không tìm thấy thẻ p hoặc h3 bên trong description container cho slug: {item_slug}")
        return None

    #return "\n".join([i.get_text() for i in contents])
    # trích xuất text và ghép nối lại, thêm strip=True để loại bỏ khoảng trắng thừa
    description_text = "\n".join([tag.get_text(strip=True) for tag in contents])

    # --- Kết thúc phần chỉnh sửa ---

    return description_text
    '''
    # THÊM ** VÀO ĐẦU VÀ CUỐI CỦA TEXT KHI LÀ H3
     processed_texts = []
    for tag in contents:
        text = tag.get_text(strip=True)
        if tag.name == 'h3':
            # Nếu là thẻ h3, thêm Markdown bold
            processed_texts.append(f"**{text}**")
        elif tag.name == 'p':
            # Nếu là thẻ p, giữ nguyên text
             processed_texts.append(text)
        # Bỏ qua các thẻ khác nếu có (mặc dù select chỉ lấy p và h3)

    # Ghép nối các phần đã xử lý
    description_text = "\n".join(processed_texts)
    # --- Kết thúc phần chỉnh sửa ---

    return description_text
    '''
'''
def test_get_description():

    slug_to_test = 'may-tinh-xach-tay/lenovo-gaming-legion-5-16irx9-i7-14650hx-32gb'
    description_content = get_description(slug_to_test)

    if description_content:
        print(f"--- Mô tả cho sản phẩm {slug_to_test} ---")
        print(description_content)
    else:
        print(f"Không lấy được mô tả cho sản phẩm {slug_to_test}.")
    
if __name__ == "__main__":
    test_get_description()
'''
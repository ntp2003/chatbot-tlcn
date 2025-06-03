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
from repositories.laptop_variant import (
    delete_laptop_variants_by_laptop_id,
    create_laptop_variant,
    CreateLaptopVariantModel,
)
from models.laptop_variant import LaptopVariantModel, Variant
from service.crawl_data import get_attributes, get_description

"""
How to run:
python
from tasks.import_laptop_data import *
import_laptop_data_jsonl_to_database()
"""

"""
Cần chạy extract đưa data vào jsonl rồi từ file jsonl import data cho brands trước rồi mới import data cho laptop
"""

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
                if len(batch) >= batch_size:
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
        # name_embedding = get_embedding(name)
        name_embedding = get_embedding(f"Laptop Name: {name}")

        if id is not None and brand_code is not None and product_type is not None:
            print(f"Upserting laptop: {id}, {name}, {brand_code}")

            try:
                laptop_model = upsert_laptop(
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
                        min_price=(
                            min([sku.get("currentPrice", 0) for sku in skus])
                            if skus
                            else price
                        ),
                        max_price=(
                            max([sku.get("currentPrice", 0) for sku in skus])
                            if skus
                            else price
                        ),
                        score=score,
                        data=laptop,
                        name_embedding=name_embedding,
                        variants_table_text=variants_to_markdown(skus),
                    )
                )

                delete_laptop_variants_by_laptop_id(id)
                laptop_variants: list[LaptopVariantModel] = []
                for sku in skus:
                    sku_id = sku.get("sku", "")
                    laptop_variants.append(
                        create_laptop_variant(
                            CreateLaptopVariantModel(
                                laptop_id=id,
                                attributes=sku.get("attributes", []),
                                slug=sku.get("slug", ""),
                                sku=sku_id,
                                name=sku.get("name", "not known"),
                                data=sku,
                                variants=[
                                    Variant(**variant)
                                    for variant in sku.get("variants", [])
                                ],
                            )
                        )
                    )
                laptop_model.attributes_table_text = (
                    convert_json_list_to_markdown_table(
                        [
                            laptop_variant.attributes
                            for laptop_variant in laptop_variants
                        ]
                    )
                )
                upsert_laptop(
                    CreateLaptopModel(
                        name_embedding=name_embedding, **laptop_model.model_dump()
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
            timeout=40.0,
        )
        response.raise_for_status()
        response_data = dict(response.json())
        total_count = response_data.get("totalCount")
        items = response_data.get("items")

        if total_count is None or total_count <= 0 or items is None:
            raise Exception(f"not found category ({category_slug})")

        # Lấy mô tả của sản phẩm và attributes cho từng sku
        for item in items:
            item["description"] = get_description(item.get("slug"))
            skus = []
            for sku in item.get("skus", []):
                sku["attributes"] = get_attributes(sku.get("sku", ""))
                skus.append(sku)
            item["skus"] = skus

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
                    # timeout=20.0,
                    timeout=40.0,  # tang thoi gian timeout
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
                    skus = []
                    for sku in item.get("skus", []):
                        sku["attributes"] = get_attributes(sku.get("sku", ""))
                        skus.append(sku)
                    item["skus"] = skus

        print(f"Import successful {imported_count} {category_slug} items")
        print("--- %s seconds ---" % (time.time() - start_time))


def write_to_jsonlines(data: dict | list[dict], file_path: str = file_path):
    with jsonlines.open(file_path, "a") as writer:
        # with jsonlines.open(file_path, "w") as writer:
        # Cach nay co van de , vi qa moi batch data lai dong mo file 1 lan => Dan den batch moi se ghi de len data batch cu
        if type(data) is dict:
            writer.write(data)
        else:
            writer.write_all(data)


# ...existing code for get_description function...

import json
from collections import defaultdict


def format_value(value):
    """Format giá trị thành string phù hợp"""
    if value is None:
        return ""
    elif isinstance(value, str):
        return value.strip()
    elif isinstance(value, list):
        if len(value) == 0:
            return ""
        # Xử lý list có object với displayValue
        formatted_items = set()
        for item in value:
            if isinstance(item, dict) and "displayValue" in item:
                formatted_items.add(item["displayValue"])
            else:
                formatted_items.add(str(item))
        return ", ".join(formatted_items)
    elif isinstance(value, dict):
        # Nếu là dict, lấy displayValue nếu có
        if "displayValue" in value:
            return value["displayValue"]
        else:
            return str(value)
    else:
        return str(value)


def convert_json_list_to_markdown_table(json_data_list):
    """
    Chuyển đổi danh sách JSON data thành bảng markdown
    """
    # Dictionary để lưu trữ tất cả attributes theo propertyName
    all_attributes = defaultdict(lambda: defaultdict(list))

    # Thu thập tất cả attributes từ tất cả JSON objects
    for json_idx, json_data in enumerate(json_data_list):
        for group in json_data:
            group_name = group["groupName"]
            for attr in group["attributes"]:
                property_name = attr["propertyName"]
                display_name = attr["displayName"]
                unit = attr.get("unit", "")
                value = attr.get("value")

                # Lưu thông tin attribute
                all_attributes[property_name]["display_name"] = display_name
                all_attributes[property_name]["unit"] = unit
                all_attributes[property_name]["group_name"] = group_name
                all_attributes[property_name]["values"].append(format_value(value))

    # Tạo bảng markdown
    markdown_lines = []

    # Header
    headers = ["Nhóm", "Thuộc tính", "Giá trị"]
    markdown_lines.append("| " + " | ".join(headers) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Data rows
    for property_name, attr_info in all_attributes.items():
        group_name = attr_info["group_name"]
        display_name = attr_info["display_name"]
        unit = attr_info["unit"] or ""

        # Gộp tất cả values thành một string, loại bỏ duplicates và empty values
        unique_values = []
        for val in attr_info["values"]:
            if val and val not in unique_values:
                unique_values.append(val)

        formatted_values = ", ".join(unique_values) if unique_values else ""
        # Nếu không có giá trị nào, bỏ qua dòng này
        if not formatted_values or not formatted_values.strip():
            continue

        # Gộp unit và formatted_values
        if unit and formatted_values:
            combined_value = f"{formatted_values} ({unit})"
        elif formatted_values:
            combined_value = formatted_values
        elif unit:
            combined_value = f"({unit})"
        else:
            combined_value = ""

        row = [group_name, display_name, combined_value]
        markdown_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(markdown_lines)


def variants_to_markdown(products: list[dict]) -> str:
    if not products:
        return "Không có sản phẩm nào."

    # Xác định tất cả các loại variant để tạo cột động
    variant_keys = set()
    for product in products:
        for variant in product.get("variants", []):
            variant_keys.add(variant.get("propertyName"))
    variant_keys = sorted(variant_keys)

    # Tạo header bảng Markdown
    headers = (
        ["Tên sản phẩm"]
        + [key.capitalize() for key in variant_keys]
        + ["Giá gốc", "Giá hiện tại"]
    )
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"

    # Tạo từng dòng cho bảng
    rows = []
    for product in products:
        name = f"{product['displayName']}"
        original_price = f"{product['originalPrice']:,}₫"
        current_price = f"{product['currentPrice']:,}₫"

        # Chuẩn bị variant theo đúng cột
        variant_map = {
            v["propertyName"]: v["displayValue"] for v in product.get("variants", [])
        }
        variant_values = [variant_map.get(key, "") for key in variant_keys]

        row = (
            "| "
            + " | ".join([name] + variant_values + [original_price, current_price])
            + " |"
        )
        rows.append(row)

    return "\n".join([header_row, separator_row] + rows)


"""
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
"""

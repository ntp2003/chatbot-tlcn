from copy import deepcopy
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from service.crawl_data import FPTShopCommentCrawler, md
from repositories.phone import get_all_ids as get_all_phone_ids
from repositories.laptop import get_all_ids as get_all_laptop_ids
from repositories.comment import (
    create as create_comment,
    CreateCommentModel,
    CommentModel,
)
import asyncio

comment_crawler = FPTShopCommentCrawler(max_retries=8)


def import_phone_comment_data() -> None:
    """
    Import comment data for all phones.
    """
    phone_ids = get_all_phone_ids()
    for phone_id in phone_ids:
        comments = comment_crawler.crawl_all_comments_sync(phone_id, batch_size=100)
        for comment in comments:
            import_comment_data(comment, product_id=phone_id, product_type="phone")


def import_laptop_comment_data() -> None:
    """
    Import comment data for all laptops.
    """
    laptop_ids = get_all_laptop_ids()
    for laptop_id in laptop_ids:
        comments = comment_crawler.crawl_all_comments_sync(laptop_id, batch_size=100)
        for comment in comments:
            if not comment.get("content"):
                continue

            import_comment_data(comment, product_id=laptop_id, product_type="laptop")


def parse_iso_datetime(iso_str: str) -> datetime:
    # Loại bỏ 'Z' và phân tích định dạng ISO 8601 có microseconds
    dt = datetime.strptime(iso_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f")
    # Gắn múi giờ UTC
    return dt.replace(tzinfo=timezone.utc)


def import_comment_data(
    comment_data: dict, product_id: str, product_type: str, parent_id: int | None = None
) -> None:
    """
    Import comment data into the database.
    """

    comment_data["content"] = md(comment_data["content"])
    comment_data_copy = deepcopy(comment_data)

    # remove unnecessary fields for create model
    comment_data_copy.pop("children", None)
    comment_data_copy.pop("media", None)
    comment_data_copy.pop("creationTime", None)
    comment_data_copy.pop("isAdministrator", None)
    comment_data_copy.pop("fullName", None)

    comment_data_copy["creation_time"] = parse_iso_datetime(
        comment_data["creationTime"]
    )
    comment_data_copy["creation_time_display"] = comment_data.get(
        "creationTimeDisplay", None
    )
    comment_data_copy["is_administrator"] = comment_data.get("isAdministrator", False)
    comment_data_copy["full_name"] = comment_data.get("fullName", None)

    print(f"Importing comment data for product {product_id} of type {product_type}")
    print(f"Comment data: {comment_data_copy}")
    print(f"Parent ID: {parent_id}")

    new_model = create_comment(
        CreateCommentModel(
            **comment_data_copy,
            product_id=product_id,
            product_type=product_type,
            parent_id=parent_id,
        )
    )

    chilren = comment_data.get("children", [])

    if chilren:
        for child in chilren:
            import_comment_data(child, product_id, product_type, new_model.id)


if __name__ == "__main__":
    import_phone_comment_data()
    import_laptop_comment_data()

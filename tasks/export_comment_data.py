import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from repositories.comment import get_all as get_all_comments, CommentModel
import json


def comment_model_to_raw_data(comment: CommentModel) -> Dict[str, Any]:
    """
    Convert CommentModel to raw crawler data format.
    """
    raw_data = {
        "id": comment.id,
        "content": comment.content,
        "creationTime": (
            comment.creation_time.isoformat().replace("+00:00", "Z")
            if comment.creation_time
            else None
        ),
        "creationTimeDisplay": comment.creation_time_display,
        "isAdministrator": comment.is_administrator,
        "fullName": comment.full_name,
        "score": comment.score,
        "likeCount": comment.like_count,
        "tags": comment.tags,
        "children": [],
        "media": [],  # Media data is not stored in current model
    }

    # Remove None values to match original crawler format
    return {k: v for k, v in raw_data.items() if v is not None}


def build_comment_tree(comments: List[CommentModel]) -> List[Dict[str, Any]]:
    """
    Build hierarchical comment tree from flat list of comments.
    """
    comment_dict = {}

    # First pass: convert all comments to raw format and index by id
    for comment in comments:
        raw_comment = comment_model_to_raw_data(comment)
        comment_dict[comment.id] = raw_comment

    # Second pass: build tree structure
    root_comments = []
    for comment in comments:
        if comment.parent_id is None:
            if comment.score is not None:
                continue  # Skip comments with score None
            root_comments.append(comment_dict[comment.id])
        else:
            # Child comment - add to parent's children
            if comment.parent_id in comment_dict:
                comment_dict[comment.parent_id]["children"].append(
                    comment_dict[comment.id]
                )

    return root_comments


def export_comments_by_product(
    product_id: str, product_type: str
) -> List[Dict[str, Any]]:
    """
    Export all comments for a specific product in raw crawler format.
    """
    # Get all comments for the product
    all_comments = get_all_comments()
    product_comments = [
        comment
        for comment in all_comments
        if comment.product_id == product_id and comment.product_type == product_type
    ]

    return build_comment_tree(product_comments)


def export_all_comments_to_json(output_file: str = "exported_comments.json") -> None:
    """
    Export all comments grouped by product to JSON file.
    """
    all_comments = get_all_comments()

    # Group comments by product
    products = {}
    for comment in all_comments:
        product_key = f"{comment.product_type}_{comment.product_id}"
        if product_key not in products:
            products[product_key] = []
        products[product_key].append(comment)

    # Convert each product's comments to raw format
    exported_data = {}
    for product_key, comments in products.items():
        product_type, product_id = product_key.split("_", 1)
        exported_data[product_key] = {
            "product_id": product_id,
            "product_type": product_type,
            "comments": build_comment_tree(comments),
        }

    # Save to JSON file
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exported_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"Exported comments to {output_path}")


def export_comments_for_product(
    product_id: str, product_type: str, output_file: str | None = None
) -> None:
    """
    Export comments for a specific product to JSON file.
    """
    comments = export_comments_by_product(product_id, product_type)

    if output_file is None:
        output_file = f"comments_{product_type}_{product_id}.json"

    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2, default=str)

    print(
        f"Exported {len(comments)} comments for {product_type} {product_id} to {output_path}"
    )


def export_comments_to_dataframe() -> pd.DataFrame:
    """
    Export all comments to pandas DataFrame (flattened structure).
    """
    all_comments = get_all_comments()

    data = []
    for comment in all_comments:
        row = {
            "id": comment.id,
            "product_id": comment.product_id,
            "product_type": comment.product_type,
            "content": comment.content,
            "score": comment.score,
            "like_count": comment.like_count,
            "full_name": comment.full_name,
            "is_administrator": comment.is_administrator,
            "parent_id": comment.parent_id,
            "tags": ", ".join(comment.tags) if comment.tags else "",
            "creation_time": comment.creation_time,
            "creation_time_display": comment.creation_time_display,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        }
        data.append(row)

    return pd.DataFrame(data)


def export_comments_to_csv(output_file: str = "exported_comments.csv") -> None:
    """
    Export all comments to CSV file.
    """
    df = export_comments_to_dataframe()
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Exported {len(df)} comments to {output_path}")


def export_product_comments_to_dataframe(
    product_id: str, product_type: str
) -> pd.DataFrame:
    """
    Export comments for a specific product to pandas DataFrame.
    """
    df = export_comments_to_dataframe()
    return df[(df["product_id"] == product_id) & (df["product_type"] == product_type)]


if __name__ == "__main__":
    # Example usage:
    # Export all comments
    export_all_comments_to_json()

    # Export comments for specific product
    # export_comments_for_product("some_product_id", "phone")

import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from service.embedding import get_list_embedding
from sklearn.metrics.pairwise import cosine_similarity, cosine_distances

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

from sklearn.feature_extraction.text import TfidfVectorizer
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
            if comment.content is None or not comment.content.strip():
                continue
            
            if comment.score is not None:
                continue
            if not quality_check(comment.content):
                continue
            
            root_comments.append(comment_dict[comment.id])
        else:
            # Child comment - add to parent's children
            if comment.parent_id in comment_dict:
                comment_dict[comment.parent_id]["children"].append(
                    comment_dict[comment.id]
                )
                
    
    try:
        with open("vietnamese_stopwords.txt", "r", encoding="utf-8") as f:
            vietnamese_stopwords = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
        
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=vietnamese_stopwords,
            ngram_range=(1, 2),
            min_df=2
        )
        
        tfidf_matrix = vectorizer.fit_transform([root_comment["content"] for root_comment in root_comments])
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find near-duplicates (similarity > 0.8)
        to_remove = set()
        for i in range(len(similarity_matrix)):
            if i in to_remove:
                continue
            for j in range(i + 1, len(similarity_matrix)):
                if similarity_matrix[i, j] > 0.9:  # Adjust threshold as needed
                    to_remove.add(j)
                    
        root_comments = [
            root_comments[i] for i in range(len(root_comments)) if i not in to_remove
        ]
        print(f"Removed {len(to_remove)} near-duplicates")
        
    except Exception as e:
        print(f"Near-duplicate removal failed: {e}")
    finally:
        for i, root_comment in enumerate(root_comments):
        

    
    
    return root_comments


def quality_check(text: str, min_words=3, min_chars=10, 
                         min_alnum_ratio=0.6, max_digit_ratio=0.3,
                         min_unique_chars=5, max_repeated_chars=4) -> bool:
    """Enhanced quality checking with multiple criteria"""
    
    if not text or not isinstance(text, str):
        return False
        
    text = text.strip()
    if len(text) < min_chars:
        return False
        
    # Word count check
    words = text.split()
    if len(words) < min_words:
        return False
    
    # Character composition checks
    total_chars = len(text)
    alnum_count = sum(c.isalnum() for c in text)
    digit_count = sum(c.isdigit() for c in text)
    unique_chars = len(set(text.lower()))
    
    # Alphanumeric ratio
    if alnum_count / total_chars < min_alnum_ratio:
        return False
    
    # Too many digits (likely spam/noise)
    if digit_count / total_chars > max_digit_ratio:
        return False
    
    # Character diversity
    if unique_chars < min_unique_chars:
        return False
    
    # Repeated character sequences
    if re.search(rf"(.)\1{{{max_repeated_chars},}}", text):
        return False
    
    # Only punctuation
    if re.fullmatch(r"[^\w\s]+", text):
        return False
            
    return True

def sample_with_clustering(self, texts: List[str], indices: List[int], 
                         target_count: int, random_state=42) -> List[int]:
    """Sample texts using clustering for maximum diversity with cosine distance"""

    if len(texts) <= target_count:
        return indices

    # Generate embeddings
    embeddings = get_list_embedding(texts)

    # Clustering
    kmeans = KMeans(n_clusters=target_count, random_state=random_state, n_init=20)
    labels = kmeans.fit_predict(embeddings)
    centroids = kmeans.cluster_centers_

    selected_indices = []

    for cluster_id in range(target_count):
        # Find texts in this cluster
        cluster_mask = labels == cluster_id
        if not np.any(cluster_mask):
            continue

        cluster_indices = np.where(cluster_mask)[0]
        cluster_embeddings = embeddings[cluster_mask]
        centroid = centroids[cluster_id]

        # Calculate cosine distances to centroid
        cosine_dists = cosine_distances(cluster_embeddings, centroid.reshape(1, -1)).flatten()

        # Find text with minimum cosine distance (most similar to centroid)
        best_idx = cluster_indices[np.argmin(cosine_dists)]
        selected_indices.append(indices[best_idx])

    return selected_indices


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

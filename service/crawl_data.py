import asyncio
from time import sleep
from typing import Optional
from bs4 import BeautifulSoup
import httpx
from markdownify import MarkdownConverter
import random
from repositories.comment import CommentModel, get, get_by_product


class IgnoreImageConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """

    def convert_img(self, el, text, parent_tags):
        return ""

    def convert(self, html):
        soup = BeautifulSoup(html, "html.parser")
        i_tag = soup.find("i")
        if i_tag is not None:
            i_tag.decompose()
        return self.convert_soup(soup)


# Create shorthand method for conversion
def md(html, **options):
    return IgnoreImageConverter(**options).convert(html)


header = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "content-type": "application/json",
    "order-channel": "1",
    "origin": "https://fptshop.com.vn",
    "referer": "https://fptshop.com.vn/",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}

cookies = {
    "cf_clearance": "nFlGMMbXxUGoiEkx_3DkQMl9AaxSs6jR0lauUzDe.IM-1748777740-1.2.1.1-JsUXaBKx.Turo.rdMI2EcosliXykZbS.o5hbHQFXfAxfP84aCRJw3ti578y0ZAS8J5T1DZ4PudGCm5iiB69d9qFNncrHCHGQcLwyf0VWp0CTmvtolDo7TVrSd.94neanysthZA8_U4wbirTVBeH_TOCqx.mnJS6zvg3DufWbivWs3vqqomt9_6gRRKmA_R7AJZvN1IrQaTCBhdBP4ytFu.2qZ_lK5v70qRH25N628xRIdCJDwx5.14vrSy42KqgeDSwqj1LpoLh2qElE4B15inFpi2U0Zz_WZDAM3ScX1EaeEB5aDWUHd2DqH3ry_6xrXsDADoM3oGxKLbViPVprgWjovEL.SIrym2Uel.l29B0",
}


def get_description(slug: str, markdown_format: bool = False) -> str:
    """
    Get the description of a brand by its slug.
    If markdown_format is True, return the description in markdown format.
    """
    url = f"https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/product/description?slug={slug}"

    with httpx.Client() as client:
        response = client.get(url, headers=header, timeout=60)
        response.raise_for_status()
        data = response.json()
        description = data.get("data", {}).get("description", "")

        if markdown_format:
            return md(description).replace("\n\n", "\n")
        return description


def get_price_information(sku: str) -> dict:
    """
    Get the price information of a product by its slug.
    Returns a dictionary with price information.
    """
    url = f"https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/product/advance-information?sku={sku}"

    with httpx.Client() as client:
        response = client.get(url, headers=header, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {})


def get_attributes(sku: str) -> list[dict]:
    """
    Get product attributes using Playwright's request context to bypass 403.
    """
    url = f"https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/product/attribute?sku={sku}"

    with httpx.Client() as client:
        response = client.get(url, headers=header, timeout=60)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise e
        data = response.json()
        return data.get("data", {}).get("attributeItem", [])


class FPTShopCommentCrawler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.base_url = (
            "https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/comment/list"
        )
        self.headers = header
        self.max_retries = max_retries
        self.base_delay = base_delay

    def create_payload(
        self,
        product_id: str,
        skip_count: int = 0,
        max_result_count: int = 6,
        sort_method: int = 1,
    ) -> dict:
        """Tạo payload cho request"""
        return {
            "content": {"id": product_id, "type": "PRODUCT"},
            "state": ["ACTIVE"],
            "skipCount": skip_count,
            "maxResultCount": max_result_count,
            "sortMethod": sort_method,
        }

    async def fetch_comments_async(
        self, product_id: str, skip_count: int = 0, max_result_count: int = 6
    ) -> Optional[dict]:
        """Async function to fetch comments for a product with retry mechanism"""
        payload = self.create_payload(product_id, skip_count, max_result_count)

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.base_url, json=payload, headers=self.headers
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt) + random.uniform(0, 1)
                    print(
                        f"HTTP error for product {product_id} (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    print(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    print(f"Max retries exceeded for product {product_id}: {e}")
                    return None
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt) + random.uniform(0, 1)
                    print(
                        f"Unexpected error for product {product_id} (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    print(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    print(f"Max retries exceeded for product {product_id}: {e}")
                    return None

    def fetch_comments_sync(
        self, product_id: str, skip_count: int = 0, max_result_count: int = 6
    ) -> Optional[dict]:
        """Synchronous function to fetch comments for a product with retry mechanism"""
        payload = self.create_payload(product_id, skip_count, max_result_count)

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        self.base_url, json=payload, headers=self.headers
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt) + random.uniform(0, 1)
                    print(
                        f"HTTP error for product {product_id} (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    print(f"Retrying in {delay:.2f} seconds...")
                    sleep(delay)
                else:
                    print(f"Max retries exceeded for product {product_id}: {e}")
                    return None
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt) + random.uniform(0, 1)
                    print(
                        f"Unexpected error for product {product_id} (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    print(f"Retrying in {delay:.2f} seconds...")
                    sleep(delay)
                else:
                    print(f"Max retries exceeded for product {product_id}: {e}")
                    return None

    async def crawl_all_comments_async(
        self, product_id: str, batch_size: int = 6
    ) -> list[dict]:
        """Crawl all comments for a product using async requests"""
        all_comments = []
        skip_count = 0

        while True:
            print(
                f"Fetching comments {skip_count} to {skip_count + batch_size} for product {product_id}"
            )

            result = await self.fetch_comments_async(product_id, skip_count, batch_size)

            if not result or result.get("status") != 200:
                print(f"Failed to fetch comments at skip_count {skip_count}")
                break

            data = result.get("data", {})
            items = data.get("items", [])

            if not items:
                print("No more comments found")
                break

            all_comments.extend(items)
            total_count = data.get("totalCount", 0)

            print(
                f"Fetched {len(items)} comments. Total so far: {len(all_comments)}/{total_count}"
            )

            # If we've fetched all comments
            if len(all_comments) >= total_count:
                break

            skip_count += batch_size

            # Add delay to be respectful to the server
            await asyncio.sleep(1)

        return all_comments

    def crawl_all_comments_sync(
        self, product_id: str, batch_size: int = 6
    ) -> list[dict]:
        """Crawl all comments for a product using synchronous requests"""
        all_comments = []
        skip_count = 0

        while True:
            print(
                f"Fetching comments {skip_count} to {skip_count + batch_size} for product {product_id}"
            )

            result = self.fetch_comments_sync(product_id, skip_count, batch_size)

            if not result or result.get("status") != 200:
                print(f"Failed to fetch comments at skip_count {skip_count}")
                break

            data = result.get("data", {})
            items = data.get("items", [])

            if not items:
                print("No more comments found")
                break

            all_comments.extend(items)
            total_count = data.get("totalCount", 0)

            print(
                f"Fetched {len(items)} comments. Total so far: {len(all_comments)}/{total_count}"
            )

            # If we've fetched all comments
            if len(all_comments) >= total_count:
                break

            skip_count += batch_size

            # Add delay to be respectful to the server
            sleep(random.choice([1, 2, 3, 4, 5]))

        return all_comments

    async def crawl_multiple_products_async(
        self, product_ids: list[str]
    ) -> dict[str, list[dict]]:
        """Crawl comments for multiple products asynchronously"""
        results = {}

        for product_id in product_ids:
            print(f"\nCrawling comments for product: {product_id}")
            comments = await self.crawl_all_comments_async(product_id)
            results[product_id] = comments
            print(
                f"Completed crawling {len(comments)} comments for product {product_id}"
            )

        return results


class CommentDataExporter:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def format_datetime_for_api(self, dt: datetime) -> str:
        """Format datetime to API format"""
        if dt:
            return dt.isoformat().replace("+00:00", "Z")
        return None

    def calculate_time_display(self, creation_time: datetime) -> str:
        """Calculate display time (e.g., '7 ngày trước')"""
        if not creation_time:
            return ""

        now = datetime.utcnow().replace(tzinfo=creation_time.tzinfo)
        diff = now - creation_time

        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes} phút trước" if minutes > 0 else "Vừa xong"
            else:  # Less than 1 day
                hours = diff.seconds // 3600
                return f"{hours} giờ trước"
        elif diff.days == 1:
            return "1 ngày trước"
        elif diff.days < 7:
            return f"{diff.days} ngày trước"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} tuần trước"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} tháng trước"
        else:
            years = diff.days // 365
            return f"{years} năm trước"

    def export_comment_to_dict(self, comment: Comment) -> Dict[str, Any]:
        """Convert Comment model to API format dictionary"""
        # Get media data
        media_data = {"images": [], "videos": []}

        for media in comment.media:
            if media.media_type == MediaTypeEnum.IMAGE:
                media_data["images"].append(media.media_url)
            elif media.media_type == MediaTypeEnum.VIDEO:
                media_data["videos"].append(media.media_url)

        # Convert replies to API format
        children = []
        for reply in comment.replies:
            children.append(self.export_comment_to_dict(reply))

        return {
            "id": comment.id,
            "creationTime": self.format_datetime_for_api(comment.creation_time),
            "creationTimeDisplay": comment.creation_time_display
            or self.calculate_time_display(comment.creation_time),
            "content": comment.content or "",
            "score": comment.score,
            "like": comment.like_count,
            "fullName": comment.full_name,
            "isAdministrator": comment.is_administrator,
            "media": media_data,
            "children": children,
        }

    def export_product_comments(
        self, product_id: str, skip_count: int = 0, max_result_count: int = 6
    ) -> Dict[str, Any]:
        """Export comments for a product in API response format"""
        with self.SessionLocal() as db:
            # Get total count
            total_count = (
                db.query(Comment)
                .filter(Comment.product_id == product_id)
                .filter(Comment.parent_id.is_(None))
                .count()
            )

            # Get main comments with pagination
            main_comments = (
                db.query(Comment)
                .filter(Comment.product_id == product_id)
                .filter(Comment.parent_id.is_(None))
                .options(selectinload(Comment.replies).selectinload(Comment.media))
                .options(selectinload(Comment.media))
                .order_by(Comment.creation_time.desc())
                .offset(skip_count)
                .limit(max_result_count)
                .all()
            )

            # Convert to API format
            items = []
            for comment in main_comments:
                items.append(self.export_comment_to_dict(comment))

            return {
                "status": 200,
                "message": "success",
                "data": {"totalCount": total_count, "items": items},
            }

    def export_all_product_comments(self, product_id: str) -> Dict[str, Any]:
        """Export all comments for a product without pagination"""
        with self.SessionLocal() as db:
            # Get all main comments
            main_comments = (
                db.query(Comment)
                .filter(Comment.product_id == product_id)
                .filter(Comment.parent_id.is_(None))
                .options(selectinload(Comment.replies).selectinload(Comment.media))
                .options(selectinload(Comment.media))
                .order_by(Comment.creation_time.desc())
                .all()
            )

            # Convert to API format
            items = []
            for comment in main_comments:
                items.append(self.export_comment_to_dict(comment))

            return {
                "status": 200,
                "message": "success",
                "data": {"totalCount": len(items), "items": items},
            }

    def export_multiple_products(
        self, product_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Export comments for multiple products"""
        results = {}
        for product_id in product_ids:
            print(f"Exporting comments for product: {product_id}")
            results[product_id] = self.export_all_product_comments(product_id)
            print(f"Exported {results[product_id]['data']['totalCount']} comments")
        return results

    def export_to_json_file(self, product_id: str, filename: Optional[str] = None):
        """Export product comments to JSON file"""
        if not filename:
            filename = f"exported_comments_{product_id}.json"

        data = self.export_all_product_comments(product_id)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Exported {data['data']['totalCount']} comments to {filename}")
        return filename

    def export_multiple_to_json(
        self, product_ids: List[str], filename: Optional[str] = None
    ):
        """Export multiple products to JSON file"""
        if not filename:
            filename = "exported_all_comments.json"

        data = self.export_multiple_products(product_ids)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        total_comments = sum(
            product_data["data"]["totalCount"] for product_data in data.values()
        )
        print(
            f"Exported {total_comments} comments for {len(product_ids)} products to {filename}"
        )
        return filename

    def get_product_list(self) -> List[str]:
        """Get list of all product IDs in database"""
        with self.SessionLocal() as db:
            result = db.query(Comment.product_id).distinct().all()
            return [row[0] for row in result]

    def export_with_filters(
        self,
        product_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_admin_only: bool = False,
        min_score: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Export comments with filters"""
        with self.SessionLocal() as db:
            query = db.query(Comment).filter(Comment.parent_id.is_(None))

            if product_ids:
                query = query.filter(Comment.product_id.in_(product_ids))

            if start_date:
                query = query.filter(Comment.creation_time >= start_date)

            if end_date:
                query = query.filter(Comment.creation_time <= end_date)

            if include_admin_only:
                query = query.filter(Comment.is_administrator == True)

            if min_score:
                query = query.filter(Comment.score >= min_score)

            comments = (
                query.options(selectinload(Comment.replies).selectinload(Comment.media))
                .options(selectinload(Comment.media))
                .order_by(Comment.creation_time.desc())
                .all()
            )

            # Group by product_id
            products = {}
            for comment in comments:
                if comment.product_id not in products:
                    products[comment.product_id] = []
                products[comment.product_id].append(
                    self.export_comment_to_dict(comment)
                )

            # Format response
            result = {}
            for product_id, items in products.items():
                result[product_id] = {
                    "status": 200,
                    "message": "success",
                    "data": {"totalCount": len(items), "items": items},
                }

            return result

    def validate_exported_data(
        self, original_file: str, exported_file: str
    ) -> Dict[str, Any]:
        """Compare original crawled data with exported data"""
        with open(original_file, "r", encoding="utf-8") as f:
            original = json.load(f)

        with open(exported_file, "r", encoding="utf-8") as f:
            exported = json.load(f)

        # Compare structure and counts
        orig_count = (
            len(original.get("comments", []))
            if "comments" in original
            else original["data"]["totalCount"]
        )
        exp_count = exported["data"]["totalCount"]

        # Count total items including replies
        def count_all_items(items):
            count = len(items)
            for item in items:
                count += count_all_items(item.get("children", []))
            return count

        orig_total = (
            count_all_items(original.get("comments", []))
            if "comments" in original
            else count_all_items(original["data"]["items"])
        )
        exp_total = count_all_items(exported["data"]["items"])

        return {
            "original_main_comments": orig_count,
            "exported_main_comments": exp_count,
            "original_total_items": orig_total,
            "exported_total_items": exp_total,
            "main_comments_match": orig_count == exp_count,
            "total_items_match": orig_total == exp_total,
            "structure_preserved": exported.get("status") == 200 and "data" in exported,
        }

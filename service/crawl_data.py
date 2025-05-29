from bs4 import BeautifulSoup
import httpx
from markdownify import MarkdownConverter


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
    Get the attributes of a product by its SKU.
    Returns a list of attributes.
    """
    url = f"https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/product/attribute?sku={sku}"

    with httpx.Client() as client:
        response = client.get(url, headers=header, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("attributeItem", [])

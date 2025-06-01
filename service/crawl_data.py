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


from playwright.sync_api import sync_playwright


from playwright.sync_api import sync_playwright
import json


def get_attributes(sku: str) -> list[dict]:
    """
    Get product attributes using Playwright's request context to bypass 403.
    """
    url = f"https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/product/attribute?sku={sku}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        request_context = context.request

        response = request_context.get(url)
        if response.status != 200:
            raise Exception(f"Failed to fetch: {response.status}")

        result = response.json()
        browser.close()

        return result.get("data", {}).get("attributeItem", [])

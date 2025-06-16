

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
phone_category_slug = "dien-thoai"

'''get the list product url'''

'''get all comment in product url'''
def get_all_comment_in_product_url(product_url: str):
    body = {
        "content": {
            "productId": product_url,
        }
    }
    with httpx.Client() as client:
        response = client.post(post_url, json=body, headers=header)
        response.raise_for_status()
        response_data = dict(response.json())
        return response_data
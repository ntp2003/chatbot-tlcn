import json
from airtable import Airtable

# Airtable configuration
BASE_ID = 'appyBXwMJrk8r7ej1'  # Replace with your Airtable Base ID
API_KEY = 'patFMTOCAlGwOP4Vf.cbb1e22ed464459b833f0ef3b87521856b3f48590c20184563af1089ffa5fef8'  # Replace with your Airtable API Key
TABLE_NAME = 'Phone_Product'  # Replace with your table name

# Initialize Airtable instance
airtable = Airtable(BASE_ID, TABLE_NAME, API_KEY)

# Load JSONL data and process each line as a separate JSON object
with open('phone_data.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            record = json.loads(line)  # Load each JSON object separately
            # Map fields to match Airtable structure
            fields = {
                "Tên sản phẩm": record["name"],
                "Mã sản phẩm": record["code"],
                "Thương hiệu": record["brand"]["name"],
                "Giá gốc": record["originalPrice"],
                "Giá hiện tại": record["currentPrice"],
                "Phần trăm giảm giá": record["discountPercentage"],
                "Kho": record["totalInventory"],
                "Màu sắc": [variant["value"] for variant in record["variants"] if variant["propertyName"] == "color"],
                "Dung lượng ROM": [variant["value"] for variant in record["variants"] if variant["propertyName"] == "rom"]
            }
            # Insert each record into Airtable
            airtable.insert(fields)
            print(f"Uploaded: {record['name']}")
        except json.JSONDecodeError as e:
            print(f"Failed to load record due to JSON error: {e}")

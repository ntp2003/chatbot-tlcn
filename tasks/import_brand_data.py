from repositories.brand import upsert_brand
from models.brand import CreateBrandModel
import time
from service.embedding import get_embedding
import json

file_path = "tasks/unique_brands.json"


# how to run:
# python
# from tasks.import_brand_data import import_json
# import_json()
def import_brand_json(file_path: str = file_path):
    start_time = time.time()

    print("Import is running...")

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

        if not data:
            raise Exception("Data is empty")

        if type(data) != list:
            raise Exception("Data is not a list")

        for brand in data:
            id = brand.get("code")
            name = brand.get("name")
            if id and name:
                upsert_brand(
                    CreateBrandModel(
                        id=id, name=name, embedding=get_embedding(f"Brand: {name}")
                    )
                )

    print(f"Import successful")
    print("--- %s seconds ---" % (time.time() - start_time))

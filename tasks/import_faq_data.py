from repositories.faq import upsert as upsert_faq
from models.faq import CreateFAQModel
import time
import pandas as pd
from service.embedding import get_embedding

selected_attr = ["id", "title", "category", "question", "answer"]

file_path = "tasks/faqs.csv"


def _preprocessing_data_in_batch(batch: pd.DataFrame):
    batch = batch[selected_attr]  # pyright: ignore
    batch.dropna(inplace=True)
    batch.drop_duplicates(subset=["id"], inplace=True)
    batch = batch.astype(
        {
            "id": "int",
            "title": "str",
            "category": "str",
            "question": "str",
            "answer": "str",
        }
    )

    return batch


# how to run:
# python
# from tasks.import_faq_data import import_csv
# import_csv()
def import_csv(
    file_path: str = file_path,
    start_offset: int = 0,
    limit: int | None = None,
    batch_size: int = 10,
):
    start_time = time.time()

    print("Import is running...")

    with pd.read_csv(
        file_path, skiprows=start_offset, nrows=limit, chunksize=batch_size
    ) as reader:
        for batch in reader:
            batch = _preprocessing_data_in_batch(batch)
            if batch.shape[0] == 0:  # pyright: ignore
                continue

            for _i, row in batch.iterrows():
                content = (
                    "Câu hỏi: " + row["question"] + "\nCâu trả lời: " + row["answer"]
                )

                faq = CreateFAQModel(
                    id=row["id"],
                    title=row["title"],
                    category=row["category"],
                    question=row["question"],
                    answer=row["answer"],
                    embedding=get_embedding(content),
                )

                upsert_faq(faq)

    print(f"Import successful")
    print("--- %s seconds ---" % (time.time() - start_time))

from repositories.faq import upsert_faq
from models.faq import CreateFAQModel
import time 
import pandas as pd
from service.embedding import get_embedding

selected_attr =  ['id', 'title', 'category', 'question', 'answer']
file_path = "tasks/faqs.csv"

# tiền xử lý dữ liệu trong batch
def _preprocessing_data_in_batch(batch: pd.DataFrame):
    # pyright: ignore bỏ qua cảnh báo trình kiểm tra type
    batch = batch[selected_attr] # pyright: ignore 
    batch.dropna(inplace=True) # remove rows with missing values , inplace=True -> thay đổi trực tiếp lên df batch thay vì tạo bản copy mới
    batch.drop_duplicate(subset=['id'], inplace=True) # remove duplicate rows based on id
    batch = batch.astype(
        {
            "id":"int",
            "title":"str",
            "category":"str",
            "question":"str",
            "answer":"str"
        }
    ) # chuẩn hóa kiểu dữ liệu , dùng astype chuyển đổi kiểu dữ liệu của các cột
    return batch

'''
how to run:


'''

def import_csv(
    file_path: str=file_path,
    start_offset: int = 0, # start from row 0
    limit: int|None = None, # số lượng dòng tối đa cần đọc
    batch_size: int = 10 # số lượng dòng xử lý trong mỗi batch
):
    start_time = time.time()
    print("Import is running...")
    # Đọc file csv theo từng batch
    with pd.read_csv(
        file_path, skiprows = start_offset, nrows = limit, chunksize=batch_size
    ) as reader:
        for batch in reader: 
            # tiền xử lý dữ liệu trong bacth
            batch = _preprocessing_data_in_batch(batch)
            if batch.shape[0] == 0 : # pyright: ignore
                continue # bỏ qua nếu batch rỗng

            for _i,row in batch.iterrows(): # iterate over batch df rows as (index, Series) pairs
                content = (
                    "Câu hỏi: " + row["question"] + "\nCâu trả lời: " + row["answer"]
                )
                faq = CreateFAQModel(
                    id = row['id'],
                    title= row['title'],
                    category = row['category'],
                    question = row['question'],
                    answer = row['answer'],
                    embedding = get_embedding(content) # tạo embedding vector cho câu hỏi và câu trả lời
                )
                upsert_faq(faq)
    
    print("Import successfully")
    print("--- %s secocnds ---" % (time.time() - start_time))
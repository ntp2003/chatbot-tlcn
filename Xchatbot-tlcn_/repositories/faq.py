from typing import Optional
import numpy as np

from db import Session
from models.faq import FAQ, FAQModel, CreateFAQModel
from sqlalchemy import select 
from service.embedding import get_embedding
import chainlit as cl

def create_faq(data:CreateFAQModel) -> FAQModel:
    with Session() as session:
        #faq=FAQ(**data.model_dump())
        faq = FAQ(
            id =data.id,
            title = data.title,
            category = data.category,
            question = data.question,
            answer = data.answer,
            embedding = data.embedding
        )
        session.add(faq)
        session.commit()
        
        return FAQModel.model_validate(faq) # validate faq and return it as pydantic (FAQModel) model

def update_faq(data: CreateFAQModel)-> int:
    with Session() as session:
        '''
        update_info = data.model_dump()
        update_info.pop("id",None)
        '''
        update_info = data.model_dump(exclude={"id"}) # gen a dictionary resprentation of data model , exclude id field
        update_count = (
            session.query(FAQ)
            .filter(FAQ.id == data.id)
            .update(update_info) # type: ignore
        )
        session.commit()
        return update_count # trả về số lượng bản ghi được cập nhật , (0 nếu không có bản ghi nào được cập nhật)

# update or insert
def upsert_faq(data: CreateFAQModel)->FAQModel:
    with Session() as session:
        if update_faq(data) == 0: # FAQ chưa tồn tại trong db -> không có bản ghi được update
            return create_faq(data)
        else: # lấy ra bản ghi được update để trả về
            updated_faq = session.execute(select(FAQ).where(FAQ.id == data.id)).scalar_one() # execute select và trả về bản ghi duy nhất dưới dạng scalar (giá trị đơn)
        return FAQModel.model_validate(updated_faq)


#  search FAQ base on  cosine distance of embedding vector
def query_by_semantic(
        question:str, top_k:int=4, threshold: Optional[float] = None
) -> list[FAQModel]:
    with Session() as session:
        embedding = get_embedding(question) # create embedding vector for question
        # tìm cac FAQ có embedding gần nhất với embedding của câu hỏi dựa trên cosine_distance
        faqs = (
            session.execute(
                select(FAQ)
                .order_by(FAQ.embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            .scalars().all() # trả về iterator các FAQ object
        )
        if threshold is not None:
            results = []
            for faq in faqs:
                c = np.dot(embedding,faq.embedding)
                print(faq.question,c)
                if c > threshold:
                    results.append(FAQModel.model_validate(faq)) # giữ lại các kết quả vượt ngưỡng
            return results
        
        return [FAQModel.model_validate(faq) for faq in faqs] # convert to pydantic model
from db import Session
from typing import Optional, List
from models.phone import CreatePhoneModel, Phone, PhoneModel
from sqlalchemy import select, case


#Tạo phone entity 
def create_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        phone = Phone(
            id=data.id,
            name=data.name,
            brand_code=data.brand_code,
            product_type_code=data.product_type_code,
            description=data.description,
            promotions=data.promotions,
            skus=data.skus,
            variants=data.variants,
            key_selling_points=data.key_selling_points,
            data=data.data,
        )
        session.add(phone)
        session.commit()

        #Xác thực phone entity 
        return PhoneModel.model_validate(phone)

# Truy xuất phone entity từ database dựa trên id
def get_phone(phone_id: int) -> Optional[PhoneModel]:
    with Session() as session:
        phone = session.get(Phone, phone_id) # dùng get của sqlalchemy để truy xuất phone entity từ database
        if phone is None:
            return None

        return PhoneModel.model_validate(phone)


# Cập nhật phone entity trong database
def update_phone(data: CreatePhoneModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None) # loại bỏ id từ thông tin cập nhật
        # Truy vấn lấy ra phone entity dựa trên id và cập nhật thông tin mới (update_info được truyền vào từ CreatePhoneModel)
        update_count = (
            session.query(Phone)
            .filter(Phone.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count # trả về số lượng phone entity (record) đã được cập nhật


# cập nhật hoặc chèn 1 entity phone mới vào database
def upsert_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        #Không có bản ghi nào được cập nhật => id chưa tồn tại trong db => tạo mới phone entity
        if update_phone(data) == 0:
            return create_phone(data)
        
        #Nếu có ít nhất 1 bản ghi được cập nhật => id đã tồn tại trong db => cập nhật thông tin phone entity
        id = data.id
        #Truy vấn lấy ra phone entity dã cập nhật từ db dựa trên id
        updated_phone = session.execute(
            select(Phone).where(Phone.id == id)
        ).scalar_one()

        return PhoneModel.model_validate(updated_phone)

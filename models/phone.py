from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ARRAY, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from .base import Base

class Phone(Base):
    __tablename__: str = "phones"

    id: Mapped[str] = mapped_column(Text, primary_key=True) #code = 688430714833

    name: Mapped[str] = mapped_column(Text)  # Tên sản phẩm Samsung Galaxy S24 FE 5G
    #orginal_price: Mapped[int] = mapped_column()  # originalPrice
    #current_price: Mapped[int] = mapped_column()  # currentPrice

    brand_code: Mapped[Optional[str]] = mapped_column(Text,nullable=True)  # "brand" : { "name" : "Samsung" , "code" : "93" } => brand_code = 93
    product_type_code : Mapped[Optional[str]] = mapped_column(Text,nullable=True) # "productType": {"code": "01001","name": "Android"}  
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Mô tả sản phẩm
    #image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URL hình ảnh

    # "promotions" : [{"content": "","image":{ "src":"", "title":""}}, {"content": "","image":{ "src":"", "title":""}},..]
    promotions: Mapped[Optional[list[dict]]] = mapped_column(JSONB, nullable=True)

    # "Skus" : [{"name":"","sku":"","originalPrice": int , "currentPrice": int,"statusOnWeb": {"code": int, "displayName":""}, "discountPercentage":"","variants":[]},{},..]
    skus: Mapped[Optional[list[dict]]] = mapped_column(JSONB, nullable=True)

    variants : Mapped[Optional[list[dict]]] = mapped_column(JSONB, nullable=True) # "variants" : [{"displayOrder": "","code": "","propertyName":"","displayValue":""}, {},..]
   
    # "keySellingPoints" [{"Code": 4, "Name": "Camera chuyên nghiệp"},{},..]
    key_selling_points: Mapped[Optional[list[dict]]] = mapped_column(JSONB, nullable=True)
    data: Mapped[dict] = mapped_column(JSONB) #data gốc
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

class CreatePhoneModel(BaseModel):
    id: str
    name: str
    brand_code: Optional[str] = None
    product_type_code: Optional[str] = None
    description: Optional[str] = None
    promotions: Optional[list[dict]] = None
    skus: Optional[list[dict]] = None
    variants: Optional[list[dict]] = None
    key_selling_points: Optional[list[dict]] = None
    data: dict
 
class PhoneModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    brand_code: Optional[str] = None
    product_type_code: Optional[str] = None
    description: Optional[str] = None
    promotions: Optional[list[dict]] = None
    skus: Optional[list[dict]] = None
    variants: Optional[list[dict]] = None
    key_selling_points: Optional[list[dict]] = None
    data: dict
    created_at: datetime
    updated_at: datetime

'''
class Phone(Base):
    __tablename__: str = "phones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)

    data: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreatePhoneModel(BaseModel):
    id: str
    data: dict


class PhoneModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    data: dict

    created_at: datetime
    updated_at: datetime
'''
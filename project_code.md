 ưng dụng chatbot bằng chainlit giả lập bán hàng với data từ fptshop.vn được chia thành FAQ và phone lưu trong database là docker container Postgresql, sử dụng mô hình GPT với API của openai để trả lời các câu hỏi về FAQ, phone từ người dùng alembic để quản lý các version
app.py (chạy bằng $ chainlit run app.py -w)
from chainlit_process.authentication import *
from chainlit_process.message import *
import alembic.config
from literalai import LiteralClient
from env import env
import subprocess


client = LiteralClient(api_key=env.LITERAL_API_KEY)
client.instrument_openai()
command = ["rq", "worker", "--with-scheduler"]
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
alembic.config.main(argv=["--raiseerr", "upgrade", "head"])

db.py
from sqlalchemy import engine
from sqlalchemy.orm import sessionmaker
from env import env
from redis import Redis

db = engine.create_engine(
    f"postgresql://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}",
    echo=True,
    pool_pre_ping=True,
)

vectordb_conn_str = f"postgresql+psycopg://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}"
Session = sessionmaker(db)
redis = Redis(
    host=env.REDIS_HOST,
    port=env.REDIS_PORT,
    password=env.REDIS_PASSWORD,
    decode_responses=True,
)

chainlit_process/authentication.py
from typing import Optional
import chainlit as cl
from repositories.user import auth_user

#decorator chainlit regis hàm auth_callback gọi khi user xác thực bằng mật khẩu
@cl.password_auth_callback  # type: ignore
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    user = auth_user(username, password)

    if not user:
        return None

    return cl.User(identifier=user.user_name, metadata={"user_id": str(user.id)})

chainlit_process/message.py
from uuid import UUID
import chainlit as cl
from service.store_chatbot import gen_answer


@cl.on_message
async def main(message: cl.Message):
    conversation = cl.chat_context.get()
    message.author = "user"
    user_id = UUID(cl.context.session.user.metadata["user_id"])  # type: ignore
    thread_id = UUID(cl.context.session.thread_id)
    print("User ID:", user_id)
    print("Thread ID:", thread_id)
    await gen_answer(user_id, thread_id, conversation).send()


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    pass
models/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

models/brand.py
from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import DateTime, String
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import Vector


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreateBrandModel(BaseModel):
    id: str
    name: str
    embedding: list[float]


class BrandModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    embedding: list[float]
    created_at: datetime
    updated_at: datetime
models/faq.py
from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import VECTOR


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str] = mapped_column(Text(), nullable=False)
    question: Mapped[str] = mapped_column(Text(), nullable=False)
    answer: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreateFAQModel(BaseModel):
    id: int
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]


class FAQModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    question: str
    answer: str
    embedding: list[float]
    created_at: datetime
    updated_at: datetime

models/phone.py

from datetime import datetime, timezone
from typing import Optional
from unittest import result
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ARRAY, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from .base import Base
from env import env
from pgvector.sqlalchemy import Vector


class Phone(Base):
    __tablename__: str = "phones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    brand_code: Mapped[str] = mapped_column(Text, nullable=False)
    product_type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    promotions: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=False)
    skus: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=False)
    key_selling_points: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=False)
    price: Mapped[int] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Text, nullable=False)
    name_embedding: Mapped[list[float]] = mapped_column(Vector, nullable=False)
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
    data: dict = {}
    name: str
    slug: str
    brand_code: str
    product_type: str
    description: str
    promotions: list[dict]
    skus: list[dict]
    key_selling_points: list[dict]
    price: int
    score: float
    name_embedding: list[float]


class PhoneModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    data: dict = {}
    name: str
    slug: str
    brand_code: str
    product_type: str
    description: str
    promotions: list[dict]
    skus: list[dict]
    key_selling_points: list[dict]
    price: int
    score: float
    name_embedding: list[float]
    created_at: datetime
    updated_at: datetime

    def _get_original_price(self) -> int:
        return self.data.get("originalPrice", 0)

    def _get_current_price(self) -> int:
        return self.data.get("currentPrice", 0)

    def _get_key_selling_points_text(
        self, prefix: str = "- ", separator: str = "\n"
    ) -> str | None:
        selling_point_texts = []

        for point in self.key_selling_points:
            point_text = f"{prefix}{point['title']}"
            description = point.get("description", "")
            if len(description) > 0:
                point_text += f" {description}"
            selling_point_texts.append(point_text)

        return (
            separator.join(selling_point_texts)
            if len(selling_point_texts) > 0
            else None
        )

    def _get_promotion_text(
        self, prefix: str = "- ", separator: str = "\n"
    ) -> str | None:
        promotion_texts = []

        for promotion in self.promotions:
            promotion_text = f"{prefix}{promotion['content']}"
            promotion_texts.append(promotion_text)

        return separator.join(promotion_texts) if len(promotion_texts) > 0 else None

    def _get_sku_variants_text(
        self, prefix: str = "", separator: str = ", "
    ) -> str | None:
        sku_texts = []

        for sku in self.skus:
            variant_texts = []
            for variant in sku.get("variants", []):
                variant_text = f"{variant['displayValue']} ({variant['propertyName']})"
                variant_texts.append(variant_text)
            sku_text = f"{prefix}{' - '.join(variant_texts)}"
            sku_texts.append(sku_text)

        return separator.join(sku_texts) if len(sku_texts) > 0 else None

    def _get_brand_name(self) -> str:
        return self.data.get("brand", {}).get("name", "not known")

    def is_on_sale(self) -> bool:
        return self._get_current_price() < self._get_original_price()

    def to_text(
        self,
        include_description: bool = False,
        include_promotion: bool = False,
        include_sku_variants: bool = False,
        inclue_key_selling_points: bool = False,
    ) -> str:
        result = f"Phone: [{self.name}]({env.FPTSHOP_BASE_URL}/{self.slug})\n"

        if self.is_on_sale():
            result += f"- Price: ~~{self._get_original_price()}~~ {self._get_current_price()}\n"
        else:
            result += f"- Price: {self._get_current_price()}\n"

        if inclue_key_selling_points:
            key_selling_points_text = self._get_key_selling_points_text(
                prefix=" ", separator=","
            )

            result += (
                f"- Key selling points: {key_selling_points_text}\n"
                if key_selling_points_text
                else ""
            )

        if include_promotion:
            promotion_text = self._get_promotion_text(prefix=" - ", separator="\n")
            result += f"- Promotions:\n{promotion_text}\n" if promotion_text else ""

        if include_sku_variants:
            sku_variants_text = self._get_sku_variants_text()
            result += f"- Variants: {sku_variants_text}\n" if sku_variants_text else ""

        if include_description:
            result += f"- Description: [{self.description}]"

        return result

models/user.py
from datetime import datetime, timezone
from typing import Optional
from .base import Base
from sqlalchemy import String, UUID, DateTime
import uuid
from sqlalchemy.orm import mapped_column, Mapped
from pydantic import BaseModel, ConfigDict

#Define ORM model cho entity User 
class User(Base):
    __tablename__ = "users" #table name in db

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    ) # primary key table users, UUID type, default value is uuid.uuid4
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

#Pydantic model để tạo mới user
class CreateUserModel(BaseModel):
    id: Optional[uuid.UUID] = None
    user_name: str
    password: str


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    password: str

    created_at: datetime
    updated_at: datetime

models/user_memory.py
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict
from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Float, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID


class UserDemand(str, Enum):
    MOBILE_PHONE = "mobile phone"
    ANOTHER_PRODUCT = "another product"


class PriceRequirement(BaseModel):
    min_price: int | None = None
    max_price: int | None = None

    def __init__(
        self,
        approximate_price: int | None,
        min_price: int | None,
        max_price: int | None,
        diff: int = 500000,
    ):
        BaseModel.__init__(self)
        if approximate_price:
            self.min_price = approximate_price - diff
            self.max_price = approximate_price + diff
        else:
            self.min_price = min_price
            self.max_price = max_price


class UserMemory(Base):
    __tablename__ = "user_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_demand: Mapped[UserDemand | None] = mapped_column(Text, nullable=True)
    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class CreateUserMemoryModel(BaseModel):
    user_id: uuid.UUID
    thread_id: uuid.UUID


class UserMemoryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    thread_id: uuid.UUID
    user_demand: UserDemand | None
    product_name: str | None
    brand: str | None
    min_price: int | None
    max_price: float | None
    phone_number: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime

repositories/brand.py
from typing import Optional

import numpy as np
from db import Session
from models.brand import CreateBrandModel, Brand, BrandModel
from sqlalchemy import select
from service.embedding import get_embedding


def create_brand(data: CreateBrandModel) -> BrandModel:
    with Session() as session:
        brand = Brand(
            id=data.id,
            name=data.name,
            embedding=data.embedding,
        )

        session.add(brand)
        session.commit()

        return BrandModel.model_validate(brand)


def update_brand(data: CreateBrandModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(Brand)
            .filter(Brand.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count


def upsert_brand(data: CreateBrandModel) -> BrandModel:
    with Session() as session:
        if update_brand(data) == 0:
            return create_brand(data)
        id = data.id

        updated_Brand = session.execute(
            select(Brand).where(Brand.id == id)
        ).scalar_one()

        return BrandModel.model_validate(updated_Brand)


def query_by_semantic(
    brand_name: str, top_k: int = 4, threshold: Optional[float] = None
) -> list[BrandModel]:
    with Session() as session:
        embedding = get_embedding(brand_name)
        brands = (
            session.execute(
                select(Brand)
                .order_by(Brand.embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            .scalars()
            .all()
        )

        if threshold:
            results = []
            for brand in brands:
                c = np.dot(embedding, brand.embedding)
                print(brand.name, c)
                if c > threshold:
                    results.append(BrandModel.model_validate(brand))
            return results

        return [BrandModel.model_validate(brand) for brand in brands]

repositories/faq.py
from typing import Optional

import numpy as np
from db import Session
from models.faq import CreateFAQModel, FAQ, FAQModel
from sqlalchemy import select
from service.embedding import get_embedding


def create_faq(data: CreateFAQModel) -> FAQModel:
    with Session() as session:
        faq = FAQ(
            id=data.id,
            title=data.title,
            category=data.category,
            question=data.question,
            answer=data.answer,
            embedding=data.embedding,
        )

        session.add(faq)
        session.commit()

        return FAQModel.model_validate(faq)


def update_faq(data: CreateFAQModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(FAQ)
            .filter(FAQ.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count


def upsert_faq(data: CreateFAQModel) -> FAQModel:
    with Session() as session:
        if update_faq(data) == 0:
            return create_faq(data)
        id = data.id

        updated_faq = session.execute(select(FAQ).where(FAQ.id == id)).scalar_one()

        return FAQModel.model_validate(updated_faq)


def query_by_semantic(
    question: str, top_k: int = 4, threshold: Optional[float] = None
) -> list[FAQModel]:
    with Session() as session:
        embedding = get_embedding(question)
        faqs = (
            session.execute(
                select(FAQ)
                .order_by(FAQ.embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            .scalars()
            .all()
        )

        if threshold:
            results = []
            for faq in faqs:
                c = np.dot(embedding, faq.embedding)
                print(faq.question, c)
                if c > threshold:
                    results.append(FAQModel.model_validate(faq))
            return results

        return [FAQModel.model_validate(faq) for faq in faqs]

repositories/phone.py
from ast import stmt
from db import Session
from typing import Optional, List
from models.phone import CreatePhoneModel, Phone, PhoneModel
from sqlalchemy import select, case
from tools.utils.search import PhoneFilter
from sqlalchemy.sql.elements import ColumnElement
from service.embedding import get_embedding
import numpy as np


# Tạo phone entity
def create_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        phone = Phone(
            id=data.id,
            name=data.name,
            slug=data.slug,
            brand_code=data.brand_code,
            product_type=data.product_type,
            description=data.description,
            promotions=data.promotions,
            skus=data.skus,
            key_selling_points=data.key_selling_points,
            price=data.price,
            score=data.score,
            data=data.data,
            name_embedding=data.name_embedding,
        )
        session.add(phone)
        session.commit()

        # Xác thực phone entity
        return PhoneModel.model_validate(phone)


# Truy xuất phone entity từ database dựa trên id
def get_phone(phone_id: int) -> Optional[PhoneModel]:
    with Session() as session:
        phone = session.get(
            Phone, phone_id
        )  # dùng get của sqlalchemy để truy xuất phone entity từ database
        if phone is None:
            return None

        return PhoneModel.model_validate(phone)


# Cập nhật phone entity trong database
def update_phone(data: CreatePhoneModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)  # loại bỏ id từ thông tin cập nhật
        # Truy vấn lấy ra phone entity dựa trên id và cập nhật thông tin mới (update_info được truyền vào từ CreatePhoneModel)
        update_count = (
            session.query(Phone)
            .filter(Phone.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count  # trả về số lượng phone entity (record) đã được cập nhật


# cập nhật hoặc chèn 1 entity phone mới vào database
def upsert_phone(data: CreatePhoneModel) -> PhoneModel:
    with Session() as session:
        # Không có bản ghi nào được cập nhật => id chưa tồn tại trong db => tạo mới phone entity
        if update_phone(data) == 0:
            return create_phone(data)

        # Nếu có ít nhất 1 bản ghi được cập nhật => id đã tồn tại trong db => cập nhật thông tin phone entity
        id = data.id
        # Truy vấn lấy ra phone entity dã cập nhật từ db dựa trên id
        updated_phone = session.execute(
            select(Phone).where(Phone.id == id)
        ).scalar_one()

        return PhoneModel.model_validate(updated_phone)


def search_phone_by_filter(
    filter: PhoneFilter,
    order_by: ColumnElement,
    is_desc: bool = True,
    limit: int = 4,
    page: int = 0,
) -> List[PhoneModel]:
    with Session() as session:
        condition = filter.condition_expression()

        stmt = (
            select(Phone).filter(condition) if condition is not None else select(Phone)
        )

        stmt = (
            stmt.order_by(order_by.desc() if is_desc else order_by)
            .limit(limit)
            .offset(page * limit)
        )

        phones = session.execute(stmt).scalars().all()
        return [PhoneModel.model_validate(phone) for phone in phones]


def search_phone_by_phone_name(
    phone_name: str, top_k: int = 4, threshold: Optional[float] = None
) -> List[PhoneModel]:
    with Session() as session:
        embedding = get_embedding(phone_name)
        phones = (
            session.execute(
                select(Phone)
                .order_by(Phone.name_embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            .scalars()
            .all()
        )

        if threshold:
            results = []
            for phone in phones:
                c = np.dot(embedding, phone.name_embedding)
                print(phone.name, c)
                if c > threshold:
                    results.append(PhoneModel.model_validate(phone))
            return results

        return [PhoneModel.model_validate(phone) for phone in phones]

repositories/redis.py
from db import redis
from redis.typing import EncodableT, ResponseT


def get_value(key: str) -> ResponseT:
    return redis.get(key)


def set_value(key: str, value: EncodableT, expire_time: int = 3600 * 24):
    redis.set(key, value, ex=expire_time)

repositories/user.py
from uuid import UUID
from db import Session
from typing import Optional, List
from models.user import CreateUserModel, User, UserModel
from sqlalchemy import select, case


def create_user(data: CreateUserModel) -> UserModel:
    with Session() as session:
        user = User(
            user_name=data.user_name,
            password=data.password,
        )

        session.add(user)
        session.commit()

        return UserModel.model_validate(user)


def auth_user(user_name: str, password: str) -> Optional[UserModel]:
    with Session() as session:
        stmt = (
            select(User)
            .select_from(User)
            .where((User.user_name == user_name) & (User.password == password))
        )

        user = session.execute(stmt).scalar()

        if user is None:
            return None
        return UserModel.model_validate(user)


def get_user(user_id: UUID) -> Optional[UserModel]:
    with Session() as session:
        user = session.get(User, user_id)
        if user is None:
            return None

        return UserModel.model_validate(user)


def update_user(data: UserModel) -> int:
    with Session() as session:
        update_info = data.model_dump()
        update_info.pop("id", None)
        update_count = (
            session.query(User)
            .filter(User.id == data.id)
            .update(update_info)  # type: ignore
        )
        session.commit()
        return update_count

repositories/user_memory.py
from models.user_memory import UserMemory, CreateUserMemoryModel, UserMemoryModel
from db import Session
from sqlalchemy import select, update
import uuid


def create_user_memory(data: CreateUserMemoryModel) -> UserMemoryModel:
    with Session() as session:
        user_memory = UserMemory(user_id=data.user_id, thread_id=data.thread_id)

        session.add(user_memory)
        session.commit()

        return UserMemoryModel.model_validate(user_memory)


def get_user_memory_by_thread_id(thread_id: uuid.UUID) -> UserMemoryModel | None:
    with Session() as session:
        user_memory = session.execute(
            select(UserMemory).where(UserMemory.thread_id == thread_id)
        ).scalar_one_or_none()

        return UserMemoryModel.model_validate(user_memory) if user_memory else None


def update_user_memory(user_memory: UserMemoryModel) -> UserMemoryModel:
    with Session() as session:
        session.execute(
            update(UserMemory)
            .where(UserMemory.thread_id == user_memory.thread_id)
            .values(**user_memory.model_dump())
        )
        session.commit()

        return user_memory

service/converter.py
from repositories.brand import query_by_semantic
from email_validator import EmailNotValidError, validate_email
import phonenumbers


def convert_band_name_to_code(
    brand_name: str | None, threshold: float = 0.7
) -> str | None:
    if not brand_name:
        return None

    brand = query_by_semantic(f"Brand: {brand_name}", 1, threshold)

    if len(brand) == 0:
        return None

    return brand[0].id


def convert_to_standard_email(raw_email: str | None) -> str | None:
    if not raw_email:
        return None

    try:
        email = validate_email(raw_email)
        return email.normalized
    except EmailNotValidError:
        return None


def convert_to_standard_phone_number(raw_phone_numbers: str | None) -> str | None:
    if not raw_phone_numbers:
        return None

    try:
        phone_numbers = phonenumbers.parse(raw_phone_numbers, "VN")
        if (
            phonenumbers.is_valid_number(phone_numbers)
            and phone_numbers.national_number
        ):
            return "0" + str(phone_numbers.national_number)
    except phonenumbers.NumberParseException:
        return None

service/email.py
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from env import env
import os

# Scopes required to send an email
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _authenticate_gmail():
    """Authenticate the user and return the Gmail API service."""
    creds = None
    # Load previously saved credentials
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If credentials are not valid or do not exist, initiate the login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                env.GOOGLE_APPLICATION_CREDENTIALS, SCOPES
            )
            creds = flow.run_local_server(port=12345)
        # Save credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def create_message(sender: str, to: str, subject: str, message_text: str) -> dict:
    """Create an email message."""
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_message(
    message: dict[str, str] | str, service=_authenticate_gmail(), user_id: str = "me"
):
    """Send an email using the Gmail API."""
    try:
        sent_message = (
            service.users().messages().send(userId=user_id, body=message).execute()
        )
        print(f"Message sent successfully: {sent_message['id']}")
    except Exception as error:
        print(f"An error occurred: {error}")

service/embedding.py
from openai import OpenAI
from env import env


_client = OpenAI(api_key=env.OPENAI_API_KEY)
_model = "text-embedding-3-small"


def get_embedding(text, model=_model):
    text = text.replace("\n", " ")
    return _client.embeddings.create(input=[text], model=model).data[0].embedding


def get_list_embedding(texts, model="text-embedding-3-small"):
    texts = [text.replace("\n", " ") for text in texts]
    return [
        item.embedding
        for item in _client.embeddings.create(input=texts, model=model).data
    ]

service/openai.py
from typing import Iterable, Optional
from uuid import UUID
from env import env
from openai import NotGiven, OpenAI
import json
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
)
from tools.invoke_tool import invoke


_model = "gpt-4o-mini"
_client = OpenAI(
    api_key=env.OPENAI_API_KEY,
)


def gen_answer(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
    tools: Iterable[ChatCompletionToolParam],
    max_iterator: int = 5,
    model: str = _model,
) -> str:
    counter = 0
    response = (
        _client.chat.completions.create(
            messages=messages,
            model=model,
            user=str(user_id),
            tools=tools,
            temperature=0,
            timeout=30,
        )
        .choices[0]
        .message
    )

    tool_choices = response.tool_calls

    if not tool_choices:
        if not response.content:
            raise Exception("No response content from the model")
        print("Final response:", response.content)
        return response.content

    while tool_choices and counter < max_iterator:
        counter += 1
        print("counter:", counter)
        messages.append(response.model_copy())  # type: ignore
        print("\n\n==== tool_calls ====\n\n")
        for tool in tool_choices:
            print(tool.function.name)
            call_id = tool.id
            tool_name = tool.function.name
            args = json.loads(tool.function.arguments)
            tool_response: ChatCompletionToolMessageParam = {
                "role": "tool",
                "tool_call_id": call_id,
                "content": invoke(user_id, thread_id, tool_name, args),
            }
            messages.append(tool_response)  # type: ignore
            print("Tool response:", tool_response["content"])
        response = (
            _client.chat.completions.create(
                messages=messages,
                model=model,
                user=str(user_id),
                tools=tools,
                temperature=0,
                timeout=30,
            )
            .choices[0]
            .message
        )
        tool_choices = response.tool_calls

    if counter == max_iterator:
        raise Exception(
            f"Maximum iteration reached ({max_iterator}). Please try again."
        )
    if not response.content:
        raise Exception("No response content from the model")

    print("Final response:", response.content)
    return response.content

service/store_chatbot.py
from typing import Optional
from uuid import UUID
from tools.faq import tool_json_schema as faq_tool
from chainlit import Message as cl_Message
from .openai import (
    gen_answer as gen_openai_answer,
)
from openai.types.chat import ChatCompletionMessageParam
from datetime import datetime
from tools.collect_requirement import tool_json_schema as collect_requirement_tool
from tools.search_phone_database import tool_json_schema as search_phone_database_tool
from tools.collect_user_contact_info import (
    tool_json_schema as collect_user_contact_info_tool,
)
from models.message import Message

tools = [
    collect_requirement_tool,
    search_phone_database_tool,
    faq_tool,
    collect_user_contact_info_tool,
]

role_prompt = """# ROLE
You are professional sales consultant staff for a phone store.

## PROFILE
- Language: Vietnamese
- Description: Your task is to assist users in selecting suitable products and providing guidance on purchasing procedures.

## SKILLS
- Answering questions about store's policies and products.
- Assisting users in selecting suitable products based on their requirements and demands.
- Clarifying user's demands and requirements effectively.
- Communicating in a professional and friendly manner.
"""

knowledge_prompt = f"""## BASIC KNOWLEDGE
- Information about your phone store:
    - Name: FPTShop
    - Location: https://fptshop.com.vn/cua-hang
    - Hotline: 1800.6601
    - Website: [FPTShop](https://fptshop.com.vn)
    - Customer service email: cskh@fptshop.com
- Current time: {datetime.now().strftime("%A, %B %d, %Y %I:%M %p")}
"""

constraints_prompt = """## CONSTRAINTS
- Don't talk nonsense and make up facts. Limit asking the user unless necessary.
- Do not proactively ask the user for any information unless there is an instruction in the context. Do not rely on previous questions to form the next question.
- When encountering frequently asked questions (FAQs) about the store's policies (such as privacy policy, return and cancellation policy, warranty policy, shipping policy, etc.), search the FAQ database to retrieve the relevant information for your response.
- The information about the phone products must be up-to-date.
- The up-to-date information about the phone products must be retrieved through searching the phone database.
- Before searching the phone database, you must collect and update the user's requirements and demands accurately.
- If the context provided lacks the necessary information, respond by stating that the information is not available and providing the hotline, email of your store rather than making up any details.
- If the user use the slang or abbreviations, you need to clarify and convert them to the standard form.
- Respond to the user's input based on the information in context.
- Use only the Vietnamese language in your responses.
"""

workflow_prompt = (
    "\n## WORKFLOW:\n"
    "\n1. **Receive User Input**:\n"
    "   - The user will provide information in the form of a message.\n"
    "   - Identify the user input based on this message, established rules (<RULES>) and the lastest context of the conversation.\n"
    "\n2. **Determine Tool Invocation**:\n"
    "   - **Condition Check**: Analyze the extracted user input and check if any tool can be invoked.\n"
    "       - If a tool is required, clearly identify which tool to call based on user needs.\n"
    "   - **Parameter Definition**: Dynamically define and validate the parameters for the tool invocation, ensuring they are derived from the user's most recent input.\n"
    "\n3. **Provide Response to User**:\n"
    "   - If no tools are required, or after the tool's execution, provide a concise and contextually appropriate response to the user.\n"
    "   - Incorporate the results of any tool invocations if applicable and ensure the response directly addresses the user's query or intent.\n"
)

initialization_prompt = """## INITIALIZATION
As a/an <ROLE>, you are required to adhere to the <WORKFLOW> and follow the <CONSTRAINTS> strictly. Use your expertise in <SKILLS> to generate responses to the user.

## REMINDER
1. **Role & Profile**: Always recall your current role (<ROLE>) and the user's profile (<PROFILE>) settings before proceeding.
2. **Language & CONSTRAINTS**: Communicate in the user's language (<Language>) and strictly adhere to the specified <CONSTRAINTS>.
3. **Step-by-Step Workflow**: Follow the <WORKFLOW> methodically, thinking through each step for clarity and accuracy.
4. **Output**: Ensure the final output ("<output>") is aligned with all settings and <CONSTRAINTS>.
"""


def gen_answer(
    user_id: UUID,
    thread_id: UUID,
    history: Optional[list[Message]] = None,
    limit: int = 10,
) -> Message:
    temporary_memory = dict()
    # init messages with system prompts
    formatted_messages = []
    formatted_messages.append({"role": "system", "content": role_prompt})
    formatted_messages.append({"role": "system", "content": knowledge_prompt})
    
    # format history messages
    if history:
        if len(history) > limit:
            history = history[-limit:] #limit lại {limit=10} messages cuối trong history
        for message in history:
            if message.author == "user":
                formatted_message: ChatCompletionMessageParam = {
                    "role": "user",
                    "content": message.content,
                }
            else:
                formatted_message: ChatCompletionMessageParam = {
                    "role": "assistant",
                    "content": message.content,
                }
            formatted_messages.append(formatted_message)

    formatted_messages.append({"role": "system", "content": constraints_prompt})
    formatted_messages.append({"role": "system", "content": workflow_prompt})
    formatted_messages.append({"role": "system", "content": initialization_prompt})

    try:
        response_text, temporary_memory = gen_openai_answer(
            user_id=user_id,
            thread_id=thread_id,
            messages=formatted_messages,
            tools=tools,
        )
    except Exception as e:
        response_text = f"An error occurred: {e}"
    respone_message = Message(
        content=response_text, author="model", metadata=temporary_memory
    )
    return respone_message

def gen_answer_for_messenger(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
) -> str:
    formatted_messages = []
    formatted_messages.append({"role": "system", "content": role_prompt})
    formatted_messages.append({"role": "system", "content": knowledge_prompt})
    
    for message in messages:
        formatted_messages.append(message)
    
    formatted_messages.append({"role": "system", "content": constraints_prompt})
    formatted_messages.append({"role": "system", "content": workflow_prompt})
    formatted_messages.append({"role": "system", "content": initialization_prompt})

    try:
        response_text,_ = gen_openai_answer(
            user_id=user_id,
            thread_id=thread_id,
            messages=formatted_messages,
            tools=tools,
        )
    except Exception as e:
        response_text = f"Đã xảy ra lỗi: {e}"

    return response_text

tools/utils/collect_requirement.py
from openai.types.chat import ChatCompletionToolParam
from models.user_memory import UserMemoryModel, PriceRequirement
from repositories.user_memory import update_user_memory
from models.user_memory import UserDemand
from .utils.search import PhoneFilter
from repositories.redis import set_value

tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "collect_and_update_user_requirements_tool",
        "description": """
# ROLE
Collect and update the user's requirements and demands.

## RULES
- You need to clarify the user's demand accurately.
- Base on the chat context to identify the user's demands and requirements effectively.
- The standard currency unit is VND. If the user provides the price in another currency, you need to convert it to VND.
- If the user use the slang or abbreviations for the currency unit, you need to clarify and convert them to VND.

## RETURNS
- Intructions for next actions after collecting and updating the user's requirements and demands.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "user_demand": {
                    "type": "string",
                    "enum": ["mobile phone", "another product"],
                    "description": "The user's demand for consultation or purchase.\n"
                    "Return 'mobile phone' if the user is interested in purchasing or seeking consultation regarding a mobile phone.\n"
                    "Otherwise, return 'another product'.",
                },
                "price_requirement": {
                    "type": "object",
                    "description": "The user's price requirement for the product they are interested in or want to consult.",
                    "properties": {
                        "approximate_price": {
                            "type": "number",
                            "description": "The approximate price the user can accept.",
                        },
                        "min_price": {
                            "type": "number",
                            "description": "The minimum price the user can accept.",
                        },
                        "max_price": {
                            "type": "number",
                            "description": "The maximum price the user can accept.",
                        },
                    },
                },
            },
        },
    },
}


def invoke(
    user_memory: UserMemoryModel, user_demand: str | None, price_requirement: dict
) -> str:
    if user_demand:
        user_memory.user_demand = UserDemand(user_demand)

    if price_requirement:
        old_filter = PhoneFilter(
            min_price=user_memory.min_price, max_price=user_memory.max_price
        )
        approximate_price = price_requirement.get("approximate_price")
        min_price = price_requirement.get("min_price")
        max_price = price_requirement.get("max_price")

        price_requirement_obj = PriceRequirement(
            approximate_price, min_price, max_price
        )

        user_memory.min_price = price_requirement_obj.min_price
        user_memory.max_price = price_requirement_obj.max_price
        new_filter = PhoneFilter(
            min_price=user_memory.min_price, max_price=user_memory.max_price
        )
        if not old_filter.__eq__(new_filter):
            user_memory.product_name = None
            set_value(str(user_memory.thread_id), 0)

    update_user_memory(user_memory)

    if user_memory.user_demand is None:
        return 'You should ask the user: "Which product are you interested in?"'

    if user_memory.user_demand == UserDemand.MOBILE_PHONE:
        return (
            "Collected and updated the user's requirement for a mobile phone.\n"
            "## NEXT ACTIONS\n"
            "- You should search the phone database to find the matching phones for the user."
        )

    return (
        "Your store has not supported this product yet. "
        "You must suggest the user to phone products or contact the store though hotline or email for more information."
    )
tools/utils/collect_user_contact_info.py
from openai.types.chat import ChatCompletionToolParam
from service.converter import (
    convert_to_standard_email,
    convert_to_standard_phone_number,
)
from models.user_memory import UserMemoryModel
from repositories.user_memory import update_user_memory
from rq import Queue
from db import redis
from service.email import send_message, create_message
from env import env

tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "collect_user_contact_info_tool",
        "description": """
# ROLE
Collect user's contact information such as phone number, email.

## RULES
- You need to collect the user's contact information when the user provides it.

## RETURNS
- Ask the user again if the user provides the invalid contact information.
- Thank the user for providing the contact information.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "The phone number that the user provides.",
                },
                "email": {
                    "type": "string",
                    "description": "The user's email that the user provides.",
                },
            },
        },
    },
}


def invoke(
    user_memory: UserMemoryModel, phone_number: str | None, email: str | None
) -> str:
    invalid_infos = []
    standard_phone_number = convert_to_standard_phone_number(phone_number)
    standard_email = convert_to_standard_email(email)

    if phone_number and not standard_phone_number:
        invalid_infos.append("phone number")
    else:
        user_memory.phone_number = standard_phone_number or user_memory.phone_number

    if email and not standard_email:
        invalid_infos.append("email")
    else:
        user_memory.email = standard_email or user_memory.email

    update_user_memory(user_memory)
    phone_number_is_missing = not user_memory.phone_number

    if len(invalid_infos) > 0:
        return f"The information about the {'' and ''.join(invalid_infos)} provided by the user might be invalid. You should politely ask them to provide this information again."

    if phone_number_is_missing:
        return "You must ask the user for their phone number to consult or purchase the product better."

    _send_email_cs(user_memory)
    return (
        "## Next, you should naturally thank the user for providing their contact information. The consulting and sales department will get in touch with them as soon as possible.\n"
        "For example: 'Cảm ơn bạn đã cung cấp thông tin liên hệ. Bộ phận tư vấn và bán hàng sẽ liên hệ với bạn sớm nhất có thể. Trong thời gian chờ đợi bạn có thể xem các sản phẩm khác hoặc liên hệ {hotline} để được hỗ trợ nhanh nhất.'"
    )


def _send_email_cs(user_memory: UserMemoryModel):
    email = create_message(
        sender=env.SENDER_EMAIL,
        to=env.RECEIVER_EMAIL,
        subject=f"{user_memory.phone_number} - Người dùng cần hỗ trợ",
        message_text=(
            "Người dùng cần hỗ trợ với.\n"
            f"Số điện thoại: {user_memory.phone_number}\n"
            f"Email: {user_memory.email}\n"
            f"Reference: {env.CHAINLIT_HOST}:{env.CHAINLIT_PORT}/thread/{user_memory.thread_id}\n"
        ),
    )
    queue = Queue(connection=redis)
    queue.enqueue(send_message, email)
tools/utils/faq.py
from models.faq import FAQModel
from repositories.faq import query_by_semantic
from openai.types.chat import ChatCompletionToolParam

# "Search the faq database for information regarding answers to frequently asked questions (FAQ) about the store's policies available in the database, "
#             "including privacy policy, return and refund policy, warranty policy, and shipping policy.\n"
tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "search_faq_database_tool",
        "description": """
# ROLE
Search the FAQ database.

## RULES
- Frequently asked questions (FAQs) are the questions that are commonly asked by users about the store's policies, including privacy policy, return and refund policy, warranty policy, and shipping policy.

## RETURNS
- The related set of questions and answers.
- Instructions on how to give response to the user based on the information provided.
""",
        "parameters": {
            "type": "object",
            "required": ["faq_question"],
            "properties": {
                "faq_question": {
                    "type": "string",
                    "description": "The frequently asked question (FAQ) about the store's policies that the user is asking for.",
                }
            },
        },
    },
}


def _to_text(faq: FAQModel) -> str:
    return (
        f"- Title: {faq.title}\n"
        f"  - Câu hỏi: {faq.question}\n"
        f"  - Câu trả lời: {faq.answer}\n"
    )


def invoke(question: str) -> str:
    print(f"Câu hỏi: {question}")
    faqs = query_by_semantic(question, threshold=0.3)
    faq_texts = [_to_text(faq) for faq in faqs]
    if faq_texts:
        return (
            "\n".join(faq_texts)
            + "## The above contains information about frequently asked questions and corresponding answers. "
            "Based on this information, please filter and provide responses to the user.\n"
            "## NOTE: If this information cannot answer the user's question, please respond that you do not know."
        )
    return "you have to tell the user that you don't know the answer."
tools/utils/invoke_tool.py
from uuid import UUID
from .faq import tool_json_schema as faq_tool_json_schema, invoke as invoke_faq_tool
from .collect_requirement import (
    tool_json_schema as collect_requirement_tool_json_schema,
    invoke as invoke_collect_requirement_tool,
)
from .search_phone_database import (
    tool_json_schema as search_phone_database_tool_json_schema,
    invoke as invoke_search_phone_database_tool,
)
from .collect_user_contact_info import (
    tool_json_schema as collect_user_contact_info_tool_json_schema,
    invoke as invoke_collect_user_contact_info_tool,
)
from openai.types.chat import ChatCompletionToolParam
import chainlit as cl
from repositories.user_memory import get_user_memory_by_thread_id, create_user_memory
from models.user_memory import CreateUserMemoryModel


def get_tool_name(tool_json_schema: ChatCompletionToolParam) -> str:
    return tool_json_schema["function"]["name"]


@cl.step(type="tool")
def invoke(
    user_id: UUID,
    thread_id: UUID,
    tool_name: str,
    args: dict,
    user_input: str | None = None,
) -> str:
    user_memory = get_user_memory_by_thread_id(thread_id)
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )

    print("\n\n\n")
    print("Invoking tool:", tool_name)
    print("Args:", args)
    print("\n\n\n")

    if tool_name == get_tool_name(faq_tool_json_schema):
        return invoke_faq_tool(args.get("faq_question"))  # type: ignore

    if tool_name == get_tool_name(search_phone_database_tool_json_schema):
        return invoke_search_phone_database_tool(
            user_memory,
            args.get("phone_brand"),
            args.get("phone_name"),
            args.get("user_needs_other_suggestions", False),
        )

    if tool_name == get_tool_name(collect_requirement_tool_json_schema):
        return invoke_collect_requirement_tool(
            user_memory, args.get("user_demand"), args.get("price_requirement", {})
        )

    if tool_name == get_tool_name(collect_user_contact_info_tool_json_schema):
        return invoke_collect_user_contact_info_tool(
            user_memory, args.get("phone_number"), args.get("email")
        )

    return "Tool name not found"
tools/utils/search_phone_database.py
from openai.types.chat import ChatCompletionToolParam
from models.phone import Phone, PhoneModel
from models.user_memory import UserMemoryModel
from repositories.user_memory import update_user_memory
from repositories.phone import search_phone_by_filter, search_phone_by_phone_name
from .utils.search import PhoneFilter
from service.converter import convert_band_name_to_code
from .utils.config import BRAND_DEFAULT, ASK_CONTACT_INFO_FOR_FURTHER_CONSULT_PROMPT
from repositories.redis import set_value, get_value

tool_json_schema: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "search_phone_database_tool",
        "description": """
## ROLE
Search the phone database.

## PREREQUISITES
- Collected and updated the user's requirements and identified the user's demands accurately.
- The user interested in purchasing or seeking consultation regarding information via phone.

## RETURNS
- Information about the phone product that matches the user's requirements or the other suggestions if the exact match is not found.
- Intructions to guide you respond to the user's queries effectively.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_brand": {
                    "type": "string",
                    "description": "The brand of the phone the user is interested in.",
                },
                "phone_name": {
                    "type": "string",
                    "description": "The name of the phone product the user is interested in.",
                },
                "user_needs_other_suggestions": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Return True if the user expresses a desire for consultation or suggestions about other phone products "
                        '(e.g., "Are there any other phones?", "Are there any other phones in this segment?", ...) compared to the previous suggestions.'
                        " Otherwise, return False."
                    ),
                },
            },
        },
    },
}


def invoke(
    user_memory: UserMemoryModel,
    phone_brand: str | None,
    phone_name: str | None,
    user_needs_other_suggestions: bool,
) -> str:
    if phone_name:
        user_memory.product_name = phone_name

    brand_code = convert_band_name_to_code(phone_brand)
    page = get_value(str(user_memory.thread_id))
    page = int(page) if page else 0  # type: ignore

    if user_needs_other_suggestions:
        page += 1

    if phone_brand and not brand_code:
        return f'You should tell the user: "Our store does not carry {phone_brand} phones. You can check out other brands like Samsung, iPhone, etc."'

    if brand_code and user_memory.brand not in [
        None,
        BRAND_DEFAULT,
        brand_code,
    ]:
        user_memory.product_name = None
        page = 0

    if brand_code:
        user_memory.brand = brand_code

    update_user_memory(user_memory)
    set_value(str(user_memory.thread_id), page)

    if not user_memory.brand and not user_memory.product_name:
        user_memory.brand = BRAND_DEFAULT
        update_user_memory(user_memory)
        return "You must ask the user for the brand of the phone they are interested in such as Samsung, iPhone, etc.\n"

    if user_memory.product_name:
        return (
            _search_phone_by_name(user_memory.product_name)
            + ASK_CONTACT_INFO_FOR_FURTHER_CONSULT_PROMPT
        )

    phone_filter = PhoneFilter(
        brand_code=user_memory.brand if user_memory.brand != BRAND_DEFAULT else None,
        max_price=user_memory.max_price,
        min_price=user_memory.min_price,
    )

    return (
        _search_phone_by_filter(phone_filter, page)
        + ASK_CONTACT_INFO_FOR_FURTHER_CONSULT_PROMPT
    )


def _search_phone_by_name(
    phone_name: str, threshold_1: float = 0.75, threshold_2: float = 0.6
) -> str:
    result_text = ""
    phone = search_phone_by_phone_name(phone_name, 1, threshold_1)
    if len(phone) > 0:
        result_text = f"## Below is the information of the phone product that the user is interested in:\n"
        return result_text + phone[0].to_text(
            inclue_key_selling_points=True,
            include_promotion=True,
            include_sku_variants=True,
            include_description=True,
        )
    else:
        phones = search_phone_by_phone_name(phone_name, 3, threshold_2)

        if len(phones) > 0:
            result_text = f"## The phone product that the user is interested in with name '{phone_name}' is not found. Below are some suggestions for the user:\n"
            result_text += _phones_to_text(phones)
        else:
            result_text += "You must say: 'I'm sorry, I couldn't find the phone you're looking for. You can look for other phones.'"

    return result_text


def _search_phone_by_filter(phone_filter: PhoneFilter, page: int = 0) -> str:
    result_text = None
    phones = search_phone_by_filter(phone_filter, Phone.score.expression)
    filter_json = phone_filter.model_dump(exclude_none=True)
    filter_remove_list = []

    if len(phones) > 0:
        result_text = f"## Below is the information of the phone product that matches the user's requirements:\n"
        result_text += _phones_to_text(phones)

    while len(phones) == 0 and len(list(filter_json.keys())) > 0:
        pop_item = filter_json.popitem()
        filter_remove_list.append(f"{pop_item[0]} is {pop_item[1]}")
        phones = search_phone_by_filter(
            PhoneFilter(**filter_json), Phone.score.expression
        )
        if len(phones) > 0:
            result_text = (
                f"## The phone product that matches the user's requirements ({', '.join(filter_remove_list)}) is not found. "
                "Below are some suggestions for the user:\n"
            )
            result_text += _phones_to_text(phones)
            break

    if result_text is None and page > 0:
        result_text = 'There are no more products to suggest to the user, so next, please say: "Sorry, apart from the products we just mentioned, it seems we do not have any other items that match your needs. Do you have any other requirements? We offer a wide range of products that might suit you."'

    return (
        result_text
        if result_text
        else "You must say: 'I'm sorry, I couldn't find the phone you're looking for. You can look for other phones.'"
    )


def _phones_to_text(phones: list[PhoneModel]) -> str:
    result_text = ""
    for i, phone in enumerate(phones):
        result_text += f"{i+1}. {phone.to_text(inclue_key_selling_points=True)}\n"
    return result_text
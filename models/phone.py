from datetime import datetime, timezone
from typing import Optional
from unittest import result
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ARRAY, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
from .base import Base, TimestampMixin, TableNameMixin
from env import env
from pgvector.sqlalchemy import Vector


class Phone(Base, TimestampMixin, TableNameMixin):
    #__tablename__: str = "phones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    brand_code: Mapped[str] = mapped_column(Text, nullable=False)
    '''
    brand_code: Mapped[str] = mapped_column(
        Text, 
        ForeignKey("brands.id", ondelete="CASCADE"),  # Thêm ForeignKey
        nullable=False
    )
    '''
    product_type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    promotions: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=False)
    skus: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=False)
    key_selling_points: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=False)
    price: Mapped[int] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Text, nullable=False)
    name_embedding: Mapped[list[float]] = mapped_column(Vector, nullable=False)
    '''
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    '''
    # Add relationship
    #brand: Mapped["Brand"] = relationship("Brand", back_populates="phones")


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
    '''
    - Chip A18 Pro cực mạnh
    - Viền màn hình siêu mỏng
    '''

    def _get_promotion_text(
        self, prefix: str = "- ", separator: str = "\n"
    ) -> str | None:
        promotion_texts = []

        for promotion in self.promotions:
            promotion_text = f"{prefix}{promotion['content']}"
            promotion_texts.append(promotion_text)

        return separator.join(promotion_texts) if len(promotion_texts) > 0 else None

    '''
    - Nhập mã QRFPTIP16 giảm ngay 500,000đ
    - Nhập mã ZLPIP500 giảm ngay 500,000đ
    '''

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
    ) -> str: # convert phone model to text for model to understand and response to user
        result = f"Phone: [{self.name}]({env.FPTSHOP_BASE_URL}/{self.slug})\n"

        if self.is_on_sale():
            result += f"- Price: ~~{self._get_original_price()}~~ {self._get_current_price()} (Sale)\n"
        else:
            result += f"- Price: {self._get_current_price() if self._get_current_price() > 0 else 'Liên hệ'}\n"

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
    '''
    Example: 
    Phone: [iPhone 15 Pro Max](https://fptshop.com.vn/dien-thoai/iphone-15-pro-max)
    - Price: ~~10000000~~ 9000000 (Sale)
    - Key selling points: - Chip A18 Pro cực mạnh, - Viền màn hình siêu mỏng
    - Promotions:
    - Nhập mã QRFPTIP16 giảm ngay 500,000đ
    - Nhập mã ZLPIP500 giảm ngay 500,000đ
    - Variants: 128GB - 16GB RAM, 256GB - 16GB RAM, 512GB - 16GB RAM
    - Description: [iPhone 15 Pro Max là một chiếc điện thoại siêu mạnh mẽ với chip A18 Pro cực mạnh, viền màn hình siêu mỏng và nhiều tính năng nổi bật khác.]
    '''
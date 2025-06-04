from .base import Base
from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import Vector
from env import env


class Laptop(Base):
    __tablename__: str = "laptops"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    brand_code: Mapped[str] = mapped_column(Text, nullable=False)
    """
    brand_code: Mapped[str] = mapped_column(
        Text, 
        ForeignKey("brands.id", ondelete="CASCADE"),  # Thêm ForeignKey
        nullable=False
    )
    """
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
    """
    #Ko cao duoc data nay
    cpu: Mapped[str] = mapped_column(Text, nullable=True)  # Ví dụ: "Intel Core i5-1235U"
    ram: Mapped[int] = mapped_column(Integer, nullable=True)  # Đơn vị: GB
    storage: Mapped[int] = mapped_column(Integer, nullable=True)  # Đơn vị: GB
    storage_type: Mapped[str] = mapped_column(Text, nullable=True)  # SSD hoặc HDD
    
    # Có thể thêm các trường bổ sung khác
    gpu: Mapped[str] = mapped_column(Text, nullable=True)  # Card đồ họa
    screen_size: Mapped[float] = mapped_column(Text, nullable=True)  # Kích thước màn hình
    screen_resolution: Mapped[str] = mapped_column(Text, nullable=True)  # Độ phân giải
    """


class CreateLaptopModel(BaseModel):
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
    """
    cpu: str | None = None
    ram: int | None = None
    storage: int | None = None
    storage_type: str | None = None
    gpu: str | None = None
    screen_size: float | None = None
    screen_resolution: str | None = None
    """


class LaptopModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )  # allow pydantic model to populate its fields from SQLAlchemy ORM model

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
    """
    cpu: str | None = None
    ram: int | None = None
    storage: int | None = None
    storage_type: str | None = None
    gpu: str | None = None
    screen_size: float | None = None
    screen_resolution: str | None = None
    """

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
        include_key_selling_points: bool = False,
    ) -> str:
        result = f"Laptop: [{self.name}]({env.FPTSHOP_BASE_URL}/{self.slug})\n"

        if self.is_on_sale():
            # result += f"- Price: ~~{self._get_original_price()}~~ {self._get_current_price()} (Sale)\n"
            result += f"- Original price: {self._get_original_price()}. Sale price: {self._get_current_price()}\n"
        else:
            result += f"- Price: {self._get_current_price() if self._get_current_price() > 0 else 'Liên hệ'}\n"

        if include_key_selling_points:
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

    """
    def get_specifications(self) -> str:
        specs = []
        if self.cpu:
            specs.append(f"CPU: {self.cpu}")
        if self.ram:
            specs.append(f"RAM: {self.ram}GB")
        if self.storage:
            storage_info = f"Storage: {self.storage}GB"
            if self.storage_type:
                storage_info += f" {self.storage_type}"
            specs.append(storage_info)
        if self.gpu:
            specs.append(f"GPU: {self.gpu}")
        if self.screen_size:
            screen_info = f"Screen: {self.screen_size}\""
            if self.screen_resolution:
                screen_info += f" ({self.screen_resolution})"
            specs.append(screen_info)
        return "\n".join(specs)

    def to_text(
        self,
        include_description: bool = False,
        include_promotion: bool = False,
        include_sku_variants: bool = False,
        include_key_selling_points: bool = False,
        include_specifications: bool = True,  # Thêm option mới
    ) -> str:
        result = super().to_text(
            include_description,
            include_promotion,
            include_sku_variants,
            include_key_selling_points
        )
        
        # Thêm thông số kỹ thuật vào kết quả
        if include_specifications:
            specs = self.get_specifications()
            if specs:
                result += f"\nSpecifications:\n{specs}"
        
        return result
    """

from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Select, select, true, case, func, literal
from models.accessory import Accessory, AccessoryModel  
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.operators import OperatorType, ge, le, eq
from sqlalchemy.sql.elements import ColumnElement
from typing import Any, Generic, TypeVar
from repositories.accessory import search as search_accessory  
from service.embedding import get_embedding
from pgvector.sqlalchemy import Vector

_T = TypeVar("_T")

class FilterAttribute(BaseModel, Generic[_T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    column: ColumnElement[_T]
    operator: Any
    value: _T

    @field_validator("operator")
    def validate_operator(cls, v):
        if not callable(v):
            raise ValueError("Operator must be callable")
        return v

    def condition_expression(self) -> ColumnElement[bool]:
        return self.operator(self.column, self.value)

class FilterCondition(BaseModel):
    filters: list[FilterAttribute]

    def condition_expression(self) -> ColumnElement[bool] | None:
        if not self.filters or len(self.filters) == 0:
            return None
        condition = self.filters[0].condition_expression()
        for filter in self.filters[1:]:
            condition = and_(condition, filter.condition_expression())
        return condition

'''
Code: 05014, Name: Sạc
Code: 05015, Name: Sạc dự phòng
Code: 05016, Name: Tai nghe
Code: 05021, Name: USB
Code: 06009, Name: Phụ kiện điện máy
Code: 05003, Name: Bàn phím
Code: 05019, Name: Thiết bị mạng
Code: 05005, Name: Bút cảm ứng
Code: 05011, Name: MDMH
Code: 05010, Name: Loa
Code: 05001, Name: Balo - Túi xách
Code: 05012, Name: Ổ cứng
Code: 05013, Name: Ốp lưng
Code: 05007, Name: Chuột
Code: 05017, Name: Thẻ nhớ
Code: 05009, Name: Hình ảnh và thiết bị thu âm
Code: 05004, Name: Bao da
Code: 05006, Name: Cáp
Code: 05008, Name: Phụ kiện tiện ích
Code: 05018, Name: Thiết bị chơi game

'''
class FilterType(str, Enum):
    PRICE = "price"
    BRAND = "brand"
    NAME = "name"
    PRODUCT_TYPE = "product_type"  # category phụ kiện

class Config(BaseModel):
    threshold: float = 0.75
    limit: int = 4
    offset: int = 0
    is_recommending: bool = False
    recommend_priority: list[FilterType] = [
        FilterType.PRODUCT_TYPE,
        FilterType.BRAND, 
        FilterType.PRICE
    ]



class AccessoryFilter(BaseModel):
    config: Config = Config()
    brand_code: str | None = None
    max_price: float | None = None
    min_price: int | None = None
    name: str | None = None
    product_type: str | None = None  # loại phụ kiện (tai nghe, sạc, ốp lưng...)

    def get_price_condition_expression(self) -> ColumnElement[bool]:
        filters = []
        if self.min_price:
            filters.append(
                FilterAttribute(
                    column=Accessory.price.expression,
                    operator=ge,
                    value=self.min_price,
                )
            )
        if self.max_price:
            filters.append(
                FilterAttribute(
                    column=Accessory.price.expression,
                    operator=le,
                    value=self.max_price, # type: ignore
                )
            )
        expression = FilterCondition(filters=filters).condition_expression()
        return expression or true() 

    def get_product_type_condition_expression(self) -> ColumnElement[bool]:
        if not self.product_type:
            return true()
        filter = FilterAttribute(
            column=Accessory.product_type.expression,
            operator=eq,
            value=self.product_type,
        ) # tai nghe
        return filter.condition_expression()

    def get_brand_condition_expression(self) -> ColumnElement[bool]:
        if not self.brand_code:
            return true()

        filter = FilterAttribute(
            column=Accessory.brand_code.expression,
            operator=eq,
            value=self.brand_code,
        )

        return filter.condition_expression()

    def get_name_condition_expression(self) -> ColumnElement[bool]:
        if not self.name:
            return true()

        embedding = get_embedding(self.name)
        filters = FilterAttribute(
            column=Accessory.name_embedding.cast(Vector).cosine_distance(embedding),
            operator=le,
            value=1 - self.config.threshold,
        )

        return filters.condition_expression()

    def condition_expression(self) -> ColumnElement[bool]:
        if self.config.is_recommending:
            return true()
        return (
            self.get_price_condition_expression()
            & self.get_brand_condition_expression()
            & self.get_name_condition_expression()
            & self.get_product_type_condition_expression()
        )

    def score_by_priority(self, filter_type: FilterType, priority: int) -> ColumnElement[int]:
        match filter_type:
            case FilterType.PRICE:
                return case((self.get_price_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.BRAND:
                return case((self.get_brand_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.NAME:
                return case((self.get_name_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.PRODUCT_TYPE:   
                return case((self.get_product_type_condition_expression(), func.pow(10, priority)), else_=0)
        raise ValueError(f"Unknown filter type: {filter_type}")


    def score_expression(
        self,
    ) -> ColumnElement[int]:
        recommend_priority = self.config.recommend_priority
        score = literal(0)
        len_priority = len(recommend_priority)

        for i, filter_type in enumerate(recommend_priority):
            score += self.score_by_priority(filter_type, len_priority - i)

        return score

    def order_by_expressions(self) -> list[ColumnElement]:
        is_recommending = self.config.is_recommending

        if self.name:
            return [
                Accessory.name_embedding.cast(Vector)
                .cosine_distance(get_embedding(self.name))
                .asc(),
            ] # khi cung cấp name , search accessory tương tự dựa trên consine distance

        if is_recommending: # chế độ đề xuất
            return [
                self.score_expression().desc(),
                Accessory.score.expression.desc(),
            ] # bỏ qua các điều kiện lọc thông thường , dùng expression score để tính điểm ưu tiên dựa trên recommend_priority

        return [Accessory.score.expression.desc()] # chỉ lọc theo điểm scor

    def to_statement(self) -> Select:
        stmt = (
            select(Accessory)
            .where(self.condition_expression())
            .order_by(*self.order_by_expressions())
            .limit(self.config.limit)
            .offset(self.config.offset)
        )

        return stmt

def search(filter: AccessoryFilter) -> list[AccessoryModel]:
    stmt = filter.to_statement()
    return search_accessory(stmt)
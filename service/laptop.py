from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Select, select, true, case, func, literal
from sqlalchemy.orm import contains_eager
from models.laptop import Laptop, LaptopModel
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.operators import OperatorType, ge, le, eq
from sqlalchemy.sql.elements import ColumnElement
from typing import Any, Generic, TypeVar
from models.laptop_variant import LaptopVariant
from repositories.laptop import search as search_laptop
from service.embedding import get_embedding
from pgvector.sqlalchemy import Vector
import weave

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
        if not self.filters:
            return None
        condition = self.filters[0].condition_expression()
        for filter in self.filters[1:]:
            condition = and_(condition, filter.condition_expression())
        return condition


class FilterType(str, Enum):
    PRICE = "price"
    BRAND = "brand"
    NAME = "name"
    COLOR = "color"


class Config(BaseModel):
    threshold: float = 0.75
    limit: int = 4
    offset: int = 0
    is_recommending: bool = False
    recommend_priority: list[FilterType] = [
        FilterType.BRAND,
        FilterType.PRICE,
        FilterType.COLOR,
    ]


class LaptopFilter(BaseModel):
    config: Config = Config()
    brand_code: str | None = None
    max_price: float | None = None
    min_price: int | None = None
    name: str | None = None
    color: str | None = None

    def get_price_condition_expression(self) -> ColumnElement[bool]:
        filters = []
        if self.min_price:
            filters.append(
                FilterAttribute(
                    column=Laptop.max_price.expression,
                    operator=ge,
                    value=self.min_price,
                )
            )
        if self.max_price:
            filters.append(
                FilterAttribute(
                    column=Laptop.min_price.expression,
                    operator=le,
                    value=self.max_price,  # type: ignore
                )
            )
        expression = FilterCondition(filters=filters).condition_expression()

        if expression is None:
            return true()

        return expression

    def get_color_condition_expression(self) -> ColumnElement[bool]:
        if not self.color:
            return true()

        filter = FilterAttribute(
            column=LaptopVariant.color_tsv.expression,
            operator=lambda x, y: x.op("@@")(y),
            value=func.phraseto_tsquery(
                "vietnamese_simple_unaccent", literal(self.color.lower())
            ),  # type: ignore
        )

        return filter.condition_expression()

    def get_brand_condition_expression(self) -> ColumnElement[bool]:
        if not self.brand_code:
            return true()

        filter = FilterAttribute(
            column=Laptop.brand_code.expression,
            operator=eq,
            value=self.brand_code,
        )
        return filter.condition_expression()

    def get_name_condition_expression(self) -> ColumnElement[bool]:
        if not self.name:
            return true()
        embedding = get_embedding(self.name)
        filters = FilterAttribute(
            column=Laptop.name_embedding.cast(Vector).cosine_distance(embedding),
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
            & self.get_color_condition_expression()
        )

    def score_by_priority(
        self, filter_type: FilterType, priority: int
    ) -> ColumnElement[int]:
        match filter_type:
            case FilterType.PRICE:
                return case(
                    (self.get_price_condition_expression(), func.pow(10, priority)),
                    else_=0,
                )
            case FilterType.BRAND:
                return case(
                    (self.get_brand_condition_expression(), func.pow(10, priority)),
                    else_=0,
                )
            case FilterType.NAME:
                return case(
                    (self.get_name_condition_expression(), func.pow(10, priority)),
                    else_=0,
                )
            case FilterType.COLOR:
                return case(
                    (self.get_color_condition_expression(), func.pow(10, priority)),
                    else_=0,
                )
        raise ValueError(f"Unknown filter type: {filter_type}")

    def score_expression(self) -> ColumnElement[int]:
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
                Laptop.name_embedding.cast(Vector)
                .cosine_distance(get_embedding(f"Laptop Name: {self.name}"))
                .asc(),
            ]
        if is_recommending:
            return [
                self.score_expression().desc(),
                Laptop.score.expression.desc(),
            ]
        return [Laptop.score.expression.desc()]

    def to_statement(self) -> Select:
        stmt = (
            select(Laptop)
            .join(Laptop.laptop_variants)
            .options(contains_eager(Laptop.laptop_variants))
            .where(self.condition_expression())
            .order_by(*self.order_by_expressions())
            .limit(self.config.limit)
            .offset(self.config.offset)
        )
        return stmt


@weave.op(name="search_laptop")
def search(filter: LaptopFilter) -> list[LaptopModel]:
    stmt = filter.to_statement()
    return search_laptop(stmt)

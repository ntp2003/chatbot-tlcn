from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Select, select, true
from models.phone import Phone, PhoneModel
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.operators import OperatorType, ge, le, eq
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql._typing import ColumnExpressionArgument
from typing import Any, Generic, TypeVar
from repositories.phone import search as search_phone
from service.embedding import get_embedding

_T = TypeVar("_T")


class FilterAttribute(BaseModel, Generic[_T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    column: ColumnElement[_T]
    operator: Any
    value: _T

    @field_validator("operator")
    def validate_operator(cls, v):
        if not callable(v):
            raise ValueError(
                f"Operator {v} is not callable. It must be a valid SQLAlchemy operator like `ge`, `le`, or `eq`."
            )
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


class Config(BaseModel):
    threshold: float = 0.75
    limit: int = 4
    offset: int = 0


class PhoneFilter(BaseModel):
    config: Config = Config()
    brand_code: str | None = None
    max_price: float | None = None
    min_price: int | None = None
    name: str | None = None

    def condition_expression(self) -> ColumnElement[bool]:
        filters = []

        if self.min_price:
            filters.append(
                FilterAttribute(
                    column=Phone.price.expression,
                    operator=ge,
                    value=self.min_price,
                )
            )
        if self.max_price:
            filters.append(
                FilterAttribute(
                    column=Phone.price.expression,
                    operator=le,
                    value=self.max_price,  # type: ignore
                )
            )
        if self.brand_code:
            filters.append(
                FilterAttribute(
                    column=Phone.brand_code.expression,
                    operator=eq,
                    value=self.brand_code,
                )
            )

        if self.name:
            embedding = get_embedding(self.name)
            filters.append(
                FilterAttribute(
                    column=Phone.name.expression.cosine_distance(embedding),
                    operator=le,
                    value=1 - self.config.threshold,
                )
            )

        expression = FilterCondition(filters=filters).condition_expression()

        if expression is None:
            return true()
        return expression

    def order_by_expressions(self) -> list[ColumnElement]:
        order_by = []

        order_by.append(Phone.score.expression.desc())

        if self.name:
            order_by.append(
                Phone.name.expression.cosine_distance(get_embedding(self.name)).asc()
            )

        return order_by

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PhoneFilter):
            return False

        return (
            self.min_price == value.min_price
            and self.max_price == value.max_price
            and self.brand_code == value.brand_code
        )

    def to_statement(self) -> Select:
        stmt = (
            select(Phone)
            .where(self.condition_expression())
            .order_by(*self.order_by_expressions())
            .limit(self.config.limit)
            .offset(self.config.offset)
        )

        return stmt


def search(filter: PhoneFilter) -> list[PhoneModel]:
    stmt = filter.to_statement()
    return search_phone(stmt)

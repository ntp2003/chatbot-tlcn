from pydantic import BaseModel, ConfigDict, field_validator
from models.phone import Phone
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.operators import OperatorType, ge, le, eq
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql._typing import ColumnExpressionArgument
from typing import Any, Generic, TypeVar
from .config import BRAND_DEFAULT

_T = TypeVar("_T")


class FilterAtrribute(BaseModel, Generic[_T]):
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
    filters: list[FilterAtrribute]

    def condition_expression(self) -> ColumnElement[bool] | None:
        if not self.filters or len(self.filters) == 0:
            return None

        condition = self.filters[0].condition_expression()
        for filter in self.filters[1:]:
            condition = and_(condition, filter.condition_expression())
        return condition


class PhoneFilter(BaseModel):
    brand_code: str | None = None
    max_price: float | None = None
    min_price: int | None = None

    def condition_expression(self) -> ColumnElement[bool] | None:
        filters = []

        if self.min_price:
            filters.append(
                FilterAtrribute(
                    column=Phone.price.expression,
                    operator=ge,
                    value=self.min_price,
                )
            )
        if self.max_price:
            filters.append(
                FilterAtrribute(
                    column=Phone.price.expression,
                    operator=le,
                    value=self.max_price,  # type: ignore
                )
            )
        if self.brand_code:
            filters.append(
                FilterAtrribute(
                    column=Phone.brand_code.expression,
                    operator=eq,
                    value=self.brand_code,
                )
            )

        return FilterCondition(filters=filters).condition_expression()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PhoneFilter):
            return False

        return (
            self.min_price == value.min_price
            and self.max_price == value.max_price
            and self.brand_code == value.brand_code
        )

from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Select, any_, select, text, true, case, func, literal, alias
from sqlalchemy.orm import noload, contains_eager
from models.phone import Phone, PhoneModel
from models.user_memory import NumericConfiguration
from models.phone_variant import PhoneVariant
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.operators import OperatorType, ge, le, eq, Operators
from sqlalchemy.sql.elements import ColumnElement
from typing import Any, Generic, TypeVar, Union
from repositories.phone import search as search_phone
from service.embedding import get_embedding
from pgvector.sqlalchemy import Vector
import weave

_T = TypeVar("_T")


def filter_by_variant_property(
    column: ColumnElement,
    property_name: str,
    operator: str,
    value: Union[str, int, float],
):
    if isinstance(value, str):
        condition = f"variant_json->>'value' {operator} :value"
        params = {"property_name": property_name, "value": value}
    else:
        condition = f"(variant_json->>'value')::numeric {operator} :value"
        params = {"property_name": property_name, "value": value}

    return text(
        f"""
            EXISTS (
                SELECT 1 
                FROM unnest({column}) AS variant_json
                WHERE variant_json->>'propertyName' = :property_name 
                AND {condition}
            )
        """
    ).params(**params)


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


class FilterType(str, Enum):
    PRICE = "price"
    BRAND = "brand"
    NAME = "name"
    COLOR = "color"
    ROM = "rom"


class Config(BaseModel):
    threshold: float = 0.75
    limit: int = 4
    offset: int = 0
    is_recommending: bool = False
    recommend_priority: list[FilterType] = [
        FilterType.BRAND,
        FilterType.PRICE,
        FilterType.ROM,
        FilterType.COLOR,
    ]


class PhoneFilter(BaseModel):
    config: Config = Config()
    brand_code: str | None = None
    max_price: float | None = None
    min_price: int | None = None
    rom: NumericConfiguration | None = None
    color: str | None = None
    name: str | None = None

    def get_price_condition_expression(self) -> ColumnElement[bool]:
        filters = []

        if self.min_price:
            filters.append(
                FilterAttribute(
                    column=Phone.max_price.expression,
                    operator=ge,
                    value=self.min_price,
                )
            )
        if self.max_price:
            filters.append(
                FilterAttribute(
                    column=Phone.min_price.expression,
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
            column=PhoneVariant.color_tsv.expression,
            operator=lambda x, y: x.op("@@")(y),
            value=func.phraseto_tsquery(
                "vietnamese_simple_unaccent", literal(self.color.lower())
            ),  # type: ignore
        )

        return filter.condition_expression()

    def get_rom_condition_expression(self) -> ColumnElement[bool]:
        if not self.rom:
            return true()

        filters = []

        if self.rom.min_value is not None:
            filters.append(
                FilterAttribute(
                    column=PhoneVariant.variants.expression,
                    operator=lambda x, y: filter_by_variant_property(x, "rom", ">=", y),
                    value=self.rom.min_value,  # type: ignore
                )
            )

        if self.rom.max_value is not None:
            filters.append(
                FilterAttribute(
                    column=PhoneVariant.variants.expression,
                    operator=lambda x, y: filter_by_variant_property(x, "rom", "<=", y),
                    value=self.rom.max_value,  # type: ignore
                )
            )

        expression = FilterCondition(filters=filters).condition_expression()

        if expression is None:
            return true()

        return expression

    def get_brand_condition_expression(self) -> ColumnElement[bool]:
        if not self.brand_code:
            return true()

        filter = FilterAttribute(
            column=Phone.brand_code.expression,
            operator=eq,
            value=self.brand_code,
        )

        return filter.condition_expression()

    def get_name_condition_expression(self) -> ColumnElement[bool]:
        if not self.name:
            return true()

        embedding = get_embedding(f"Phone Name: {self.name}")
        filters = FilterAttribute(
            column=Phone.name_embedding.cast(Vector).cosine_distance(embedding),
            operator=le,
            value=1 - self.config.threshold,
        )

        return filters.condition_expression()

    def condition_expression(self) -> ColumnElement[bool]:
        if self.config.is_recommending:
            return true()

        base_conditions = (
            self.get_price_condition_expression()
            & self.get_brand_condition_expression()
            & self.get_name_condition_expression()
        )

        # Add subquery conditions for PhoneVariant-related filters
        variant_conditions = []

        if self.rom:
            variant_conditions.append(self.get_rom_condition_expression())

        if self.color:
            variant_conditions.append(self.get_color_condition_expression())

        if variant_conditions:
            # Create subquery to check if phone has variants matching the conditions
            variant_condition = variant_conditions[0]
            for condition in variant_conditions[1:]:
                variant_condition = variant_condition & condition

            variant_subquery = select(PhoneVariant.phone_id).where(variant_condition)
            base_conditions = base_conditions & Phone.id.in_(variant_subquery)

        return base_conditions

    def score_by_priority(
        self, filter_type: FilterType, priority: int
    ) -> ColumnElement[int]:
        if filter_type == FilterType.PRICE:
            return case(
                (self.get_price_condition_expression(), func.pow(10, priority)),
                else_=0,
            )

        if filter_type == FilterType.BRAND:
            return case(
                (self.get_brand_condition_expression(), func.pow(10, priority)),
                else_=0,
            )

        if filter_type == FilterType.NAME:
            return case(
                (self.get_name_condition_expression(), func.pow(10, priority)),
                else_=0,
            )

        if filter_type == FilterType.COLOR:
            if not self.color:
                return literal(0)
            color_subquery = select(PhoneVariant.phone_id).where(
                self.get_color_condition_expression()
            )
            return case(
                (Phone.id.in_(color_subquery), func.pow(10, priority)),
                else_=0,
            )

        if filter_type == FilterType.ROM:
            if not self.rom:
                return literal(0)
            rom_subquery = select(PhoneVariant.phone_id).where(
                self.get_rom_condition_expression()
            )
            return case(
                (Phone.id.in_(rom_subquery), func.pow(10, priority)),
                else_=0,
            )

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
                Phone.name_embedding.cast(Vector)
                .cosine_distance(get_embedding(f"Phone name: {self.name}"))
                .asc(),
            ]

        if is_recommending:
            return [
                self.score_expression().desc(),
                Phone.score.expression.desc(),
            ]

        return [Phone.score.expression.desc()]

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


@weave.op(name="search_phone")
def search(filter: PhoneFilter) -> list[PhoneModel]:
    stmt = filter.to_statement()
    return search_phone(stmt)

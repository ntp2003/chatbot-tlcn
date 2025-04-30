from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Select, select, true, case, func, literal
from models.laptop import Laptop, LaptopModel  
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.operators import OperatorType, ge, le, eq
from sqlalchemy.sql.elements import ColumnElement
from typing import Any, Generic, TypeVar
from repositories.laptop import search as search_laptop  
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
    
    # Ko cao duoc data nay
    '''
    CPU = "cpu"
    RAM = "ram"
    STORAGE = "storage"
    '''

class Config(BaseModel):
    threshold: float = 0.75
    limit: int = 4
    offset: int = 0
    is_recommending: bool = False
    recommend_priority: list[FilterType] = [
        FilterType.BRAND, 
        FilterType.PRICE,
        #FilterType.CPU,
        #FilterType.RAM
    ]


class LaptopFilter(BaseModel):
    config: Config = Config()
    brand_code: str | None = None
    max_price: float | None = None
    min_price: int | None = None
    name: str | None = None
    '''
    # ko cao dc
    cpu: str | None = None
    ram: int | None = None
    storage: int | None = None
    '''
    def get_price_condition_expression(self) -> ColumnElement[bool]:
        filters = []
        if self.min_price:
            filters.append(
                FilterAttribute(
                    column=Laptop.price.expression,
                    operator=ge,
                    value=self.min_price,
                )
            )
        if self.max_price:
            filters.append(
                FilterAttribute(
                    column=Laptop.price.expression,
                    operator=le,
                    value=self.max_price,
                )
            )
        expression = FilterCondition(filters=filters).condition_expression()
        return expression or true()

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

    '''
    def get_cpu_condition_expression(self) -> ColumnElement[bool]:
        if not self.cpu:
            return true()
        filter = FilterAttribute(
            column=Laptop.cpu.expression,
            operator=eq,
            value=self.cpu,
        )
        return filter.condition_expression()

    def get_ram_condition_expression(self) -> ColumnElement[bool]:
        if not self.ram:
            return true()
        filter = FilterAttribute(
            column=Laptop.ram.expression,
            operator=eq,
            value=self.ram,
        )
        return filter.condition_expression()
    '''

    def condition_expression(self) -> ColumnElement[bool]:
        if self.config.is_recommending:
            return true()
        return (
            self.get_price_condition_expression()
            & self.get_brand_condition_expression()
            & self.get_name_condition_expression()
            #& self.get_cpu_condition_expression()
            #& self.get_ram_condition_expression()
        )

    '''
    def score_by_priority(self, filter_type: FilterType, priority: int) -> ColumnElement[int]:
        match filter_type:
            case FilterType.PRICE:
                return case((self.get_price_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.BRAND:
                return case((self.get_brand_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.NAME:
                return case((self.get_name_condition_expression(), func.pow(10, priority)), else_=0)
            
            case FilterType.CPU:
                return case((self.get_cpu_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.RAM:
                return case((self.get_ram_condition_expression(), func.pow(10, priority)), else_=0)
        raise ValueError(f"Unknown filter type: {filter_type}")
    '''
    def score_by_priority(self, filter_type: FilterType, priority: int) -> ColumnElement[int]:
        match filter_type:
            case FilterType.PRICE:
                return case((self.get_price_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.BRAND:
                return case((self.get_brand_condition_expression(), func.pow(10, priority)), else_=0)
            case FilterType.NAME:
                return case((self.get_name_condition_expression(), func.pow(10, priority)), else_=0)
        raise ValueError(f"Unknown filter type: {filter_type}")
    
    #dung chung
    def score_expression(self) -> ColumnElement[int]:
        recommend_priority = self.config.recommend_priority
        score = literal(0)
        len_priority = len(recommend_priority)

        for i, filter_type in enumerate(recommend_priority):
            score += self.score_by_priority(filter_type, len_priority - i)
        return score

    # dung chung
    def order_by_expressions(self) -> list[ColumnElement]:
        is_recommending = self.config.is_recommending

        if self.name:
            return [
                Laptop.name_embedding.cast(Vector)
                .cosine_distance(get_embedding(self.name))
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
            .where(self.condition_expression())
            .order_by(*self.order_by_expressions())
            .limit(self.config.limit)
            .offset(self.config.offset)
        )
        return stmt

def search(filter: LaptopFilter) -> list[LaptopModel]:
    stmt = filter.to_statement()
    return search_laptop(stmt)
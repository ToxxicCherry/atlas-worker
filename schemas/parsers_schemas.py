from pydantic import (
                    BaseModel,
                    Field,
                    model_validator,
                    ConfigDict,
                    computed_field
                    )
from pydantic.alias_generators import to_camel
from typing import List, Dict, Any, Union, Literal
from copy import copy


class Filter(BaseModel):
    params: Dict[str, str | int] = Field(default_factory=dict)
    total: int = Field(default=0)

    def __add__(self, other):
        if isinstance(other, Filter):
            self.params.update(other.params)
            return self

        if isinstance(other, dict):
            self.params.update(other)
            return self

        raise TypeError(f'Ожидается {Filter} или {dict}. Получен {type(other)}')

    def __eq__(self, other):
        if isinstance(other, Filter):
            return self.params.keys() == other.params.keys()

        if isinstance(other, dict):
            return self.params.keys() == other.keys()

        raise TypeError(f'Ожидается {Filter} или {dict}. Получен {type(other)}')

class FilterData(BaseModel):
    items: List[Filter] = Field(default_factory=list)


    @model_validator(mode='before')
    @classmethod
    def parse_json(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        filters = data.get('data', {}).get('filters', [])
        if not filters:
            return {'items': []}

        target_filter = filters[0]
        key = target_filter.get('key', 'unknown')
        items = target_filter.get('items', [])

        result = [
            Filter(params={key: item.get('id')})
            for item in items
            if item.get('id') is not None
        ]

        return {'items': result}

class TaskForWorker(BaseModel):
    filter: Filter = Field(default_factory=Filter)
    retries: int = Field(default=5)

class Size(BaseModel):

    name: str = Field(serialization_alias='Размер')
    price_basic: int = Field(serialization_alias='Цена до скидки')
    price_product: int = Field(serialization_alias='Цена со скидкой')

    @computed_field(alias='Скидка руб.')
    @property
    def discount_amount(self) -> int:
        return self.price_basic - self.price_product

    @computed_field(alias='Скидка %')
    @property
    def discount_percent(self) -> int:
        if not self.price_basic:
            return 0
        return int(self.discount_amount / self.price_basic * 100)


    @model_validator(mode='before')
    @classmethod
    def prices_to_rubles(cls, data: Any) -> dict:
        if not isinstance(data, dict):
            return data

        new_data = copy(data)
        price_info = data.get('price', {})

        new_data['price_basic'] = price_info.get('basic', 0) // 100
        new_data['price_product'] = price_info.get('product', 0) // 100

        return new_data

class Item(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: int = Field(serialization_alias='Артикул')
    name: str = Field(serialization_alias='Название')
    brand: str = Field(serialization_alias='Бренд')
    brand_id: int = Field(serialization_alias='ID бренда')
    subject_id: int = Field(description='ID категории', serialization_alias='ID категории')
    sizes: List[Size] = Field(default_factory=list, serialization_alias='Размеры')
    total_quantity: int = Field(serialization_alias='Количество на складе')
    rating: float = Field(ge=0, le=5, serialization_alias='Рейтинг товара')
    feedbacks: int = Field(serialization_alias='Количество отзывов')
    supplier: str = Field(serialization_alias='Продавец')
    supplier_id: int = Field(serialization_alias='ID продавца')
    supplier_rating: float = Field(serialization_alias='Рейтинг продавца')
    weight: float = Field(serialization_alias='Вес')
    wh: int = Field(description='ID склада', serialization_alias='ID скалада')
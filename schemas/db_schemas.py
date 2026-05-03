from pydantic import (
                    BaseModel,
                    Field,
                    model_validator,
                    ConfigDict,
                    computed_field
                    )
from pydantic.alias_generators import to_camel
from typing import List, Dict, Any, Union, Literal
import enum


class TaskType(enum.Enum):
    fetch_cards = "fetch_cards"
    track_positions = "track_positions"


class FetchCardsPayload(BaseModel):
    type: Literal['fetch_cards'] = TaskType.fetch_cards.value
    query: str

class TrackPositionPayload(BaseModel):
    type: Literal['track_positions'] = TaskType.track_positions.value
    query: str
    articles: List[int]


class MarketPlace(enum.Enum):
    wildberries = 'wildberries'
    ozon = 'ozon'

class TaskStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"



class CreateTaskSchema(BaseModel):
    source: MarketPlace = Field(default=MarketPlace.wildberries.value)
    payload: Union[FetchCardsPayload, TrackPositionPayload] = Field()

    @property
    def task_type(self) -> TaskType:
        return self.payload.type

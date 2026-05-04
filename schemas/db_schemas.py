from pydantic import (
                    BaseModel,
                    Field,
                    model_validator,
                    ConfigDict,
                    computed_field,
                    EmailStr,
                    )
from pydantic.alias_generators import to_camel
from typing import List, Dict, Any, Union, Literal
from datetime import datetime, timezone
import uuid
import enum


class TaskType(enum.Enum):
    fetch_cards = "fetch_cards"
    track_positions = "track_positions"


class FetchCardsPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: Literal[TaskType.fetch_cards] = TaskType.fetch_cards
    query: str

class TrackPositionPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: Literal[TaskType.track_positions] = TaskType.track_positions
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
    user_id: uuid.UUID = Field()
    source: MarketPlace = Field(default=MarketPlace.wildberries.value)
    payload: Union[FetchCardsPayload, TrackPositionPayload] = Field()

    @property
    def task_type(self) -> TaskType:
        return self.payload.type


class UserSchema(BaseModel):
    id: uuid.UUID = Field(default=uuid.uuid4)
    username: str = Field()
    email: EmailStr = Field()
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default=datetime.now(timezone.utc))


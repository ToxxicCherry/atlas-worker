from pydantic import BaseModel


class Position(BaseModel):
    product_id: int
    position: int

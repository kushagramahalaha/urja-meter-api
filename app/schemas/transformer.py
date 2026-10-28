
from typing import List

from pydantic import BaseModel



class TransformerRecord(BaseModel):
    code: str
    name: str
    feederCode: str
    capacityKva: int


class TransformerResponse(BaseModel):
    data: List[TransformerRecord]
    total: int
    page: int
    pageSize: int


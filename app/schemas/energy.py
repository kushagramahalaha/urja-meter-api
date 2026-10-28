from typing import List, Optional
from pydantic import BaseModel


class EnergyRecord(BaseModel):
    timestamp: str
    kwh: Optional[float] = None
    kvah: Optional[float] = None
    voltR: Optional[float] = None


class EnergyResponse(BaseModel):
    data: List[EnergyRecord]

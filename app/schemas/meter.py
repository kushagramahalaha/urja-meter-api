from typing import List
from pydantic import BaseModel


class MeterRecord(BaseModel):
    meterId: str
    serialNo: str
    make: str
    phaseType: str
    installStatus: str
    dtCode: str


class MeterSearchResponse(BaseModel):
    data: List[MeterRecord]
    total: int
    page: int
    pageSize: int


class GeoData(BaseModel):
    latitude: float
    longitude: float


class GeoResponse(BaseModel):
    data: GeoData

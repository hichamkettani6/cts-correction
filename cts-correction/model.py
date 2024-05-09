from pydantic import BaseModel
from fastapi import Query
from typing import Annotated, List
from datetime import datetime

class Dates(BaseModel):
    dtime_start: str
    dtime_end: str


class Data(BaseModel):
    timestamps: List[datetime] = list()
    dates: List[str] = list()
    displacements: List[float] = list()
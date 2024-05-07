from pydantic import BaseModel
from fastapi import Query
from typing import Annotated, List

class Dates(BaseModel):
    dtime_start: str
    dtime_end: str


class Data(BaseModel):
    dates: List[str] = list()
    displacements: List[float] = list()
from pydantic import BaseModel, AwareDatetime
from sqlmodel import Field, SQLModel
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, TIMESTAMP, TEXT, FLOAT


class Dates(BaseModel):
    dtime_start: datetime
    dtime_end: datetime
    


class DisData(SQLModel, table=True):
    #id: int = Field(primary_key=True)
    MJD_date: float = Field(FLOAT, primary_key=True)
    date_utc: AwareDatetime = Field(sa_column=Column(TEXT))
    timestamp: AwareDatetime = Field(sa_column=Column(TIMESTAMP(timezone=True), index=True))
    displacement: float
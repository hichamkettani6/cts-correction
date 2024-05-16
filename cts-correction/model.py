from pydantic import BaseModel, AwareDatetime
from sqlmodel import Field, SQLModel
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime, Float, TIMESTAMP, TEXT


class Dates(BaseModel):
    dtime_start: str
    dtime_end: str
    


class DisData(SQLModel, table=True):
    MJD_dates: float = Field(primary_key=True)
    date_utc: AwareDatetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    timestamp: AwareDatetime = Field(sa_column=Column(TIMESTAMP(timezone=True))) #Field(sa_column=TIMESTAMP(timezone=True))
    tz: str
    displacement: float

    @property
    def _timestamp(self):
        return self.timestamp.replace(tzinfo=ZoneInfo(self.tz))
    
    @_timestamp.setter
    def _timestamp(self, date: AwareDatetime):
        self.timestamp = date.astimezone(ZoneInfo(self.tz))


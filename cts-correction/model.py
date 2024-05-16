from pydantic import BaseModel, AwareDatetime
from sqlmodel import Field, SQLModel
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime, Float, TIMESTAMP


class Dates(BaseModel):
    dtime_start: str
    dtime_end: str
    


class DisData(SQLModel, table=True):
    MJD_dates: float = Field(primary_key=True)
    date_utc: AwareDatetime = Field(sa_column=Column(DateTime(timezone=True)))
    timestamp: AwareDatetime = Field(sa_column=Column(DateTime(timezone=True))) #Field(sa_column=TIMESTAMP(timezone=True))
    displacement: float

    def add_timezone_dates(self, date: str, TZ: str):
        self.date_utc = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo = ZoneInfo('UTC'))
        self.timestamp = self.date_utc.astimezone(ZoneInfo(TZ))

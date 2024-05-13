from pydantic import BaseModel
from fastapi import Query
from typing import Annotated, List
from datetime import datetime
import pendulum
from zoneinfo import ZoneInfo

class Dates(BaseModel):
    dtime_start: str
    dtime_end: str


class Data(BaseModel):
    dates: List[str] = list()
    timezoneDates: List[datetime] = list()
    displacements: List[float] = list()


    #Not efficient..It takes x3 wrt zoneinfo..
    @classmethod
    def to_datetime(cls, date: str, TZ: str):
        pendulum_dt = pendulum.from_format(date, 'YYYY-MM-DD HH:mm:ss').in_tz(TZ)

        standard_datetime = datetime(
            year=pendulum_dt.year,
            month=pendulum_dt.month,
            day=pendulum_dt.day,
            hour=pendulum_dt.hour,
            minute=pendulum_dt.minute,
            second=pendulum_dt.second,
            tzinfo=pendulum_dt.tzinfo
        )
        
        return standard_datetime 
    

    def add_timezoneDate(self, date: str, TZ: str):
        dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo = ZoneInfo('UTC'))
        self.timezoneDates.append(dt.astimezone(ZoneInfo(TZ)))

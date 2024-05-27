from pydantic import BaseModel, AwareDatetime, root_validator
from sqlmodel import Field, SQLModel
from datetime import datetime
from sqlalchemy import Column, TIMESTAMP, TEXT, FLOAT


class Range(BaseModel):
    dtime_start: datetime
    dtime_end: datetime

    @root_validator(pre=True)
    def set_dates(cls, values):
        cls.dtime_start = datetime.strptime(values.get('dtime_start'), "%Y-%m-%d %H:%M:%S")
        cls.dtime_end = datetime.strptime(values.get('dtime_end'), "%Y-%m-%d %H:%M:%S")

        return values
    
    
class DisData(SQLModel, table=True):
    MJD_date: float = Field(FLOAT, primary_key=True)
    date_utc: AwareDatetime = Field(sa_column=Column(TEXT))
    timestamp: AwareDatetime = Field(sa_column=Column(TIMESTAMP(timezone=True), index=True))
    displacement: float
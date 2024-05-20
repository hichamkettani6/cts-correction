import sqlite3
import psycopg2
from typing import List, Tuple
from datetime import datetime
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy import text
from model import DisData
from pydantic import AwareDatetime
import os
from zoneinfo import ZoneInfo

username = os.environ.get("POSTGRES_USER")
password = os.environ.get("POSTGRES_PASSWORD")
database = os.environ.get("POSTGRES_DB")
SQLALCHEMY_DATABASE_URL = f"postgresql://{username}:{password}@database/{database}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

async def createDB():
    SQLModel.metadata.create_all(engine)


async def fillDB(records: List[DisData]):
    with Session(engine) as session:
        session.add_all(records)
        session.commit()

async def queryFromDB(dtime_start: datetime, dtime_end: datetime) -> List[DisData]:
    with Session(engine) as session:
        query = text(f'''SELECT DISTINCT ON ("MJD_date") *
                    FROM disdata d
                    WHERE d.timestamp BETWEEN '{dtime_start}' AND '{dtime_end}' ''')
        result = session.execute(query).all()

    return result


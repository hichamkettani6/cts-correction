from typing import List
from datetime import datetime
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm  import sessionmaker
from sqlalchemy import text
from model import DisData
import os
import re
from zoneinfo import ZoneInfo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

username = os.environ.get("POSTGRES_USER")
password = os.environ.get("POSTGRES_PASSWORD")
database = os.environ.get("POSTGRES_DB")
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{username}:{password}@database/{database}"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def createDB():
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def fillDB(records: List[DisData]):
    async with async_session() as session:
        values = ', '.join(f"({record.MJD_date}, '{record.date_utc}', '{record.timestamp}',\
                            {record.displacement})" for record in records)    
        query = text(f'''INSERT INTO disdata
                         VALUES {values}
                         ON CONFLICT DO NOTHING;''')
        
        try: 
            await session.execute(query)
            await session.commit()
        except:
            await session.rollback()
        

async def queryFromDB(dtime_start: datetime, dtime_end: datetime) -> List[DisData]:
    async with async_session() as session:
        query = text(f'''SELECT *
                    FROM disdata d
                    WHERE d.timestamp BETWEEN '{dtime_start}' AND '{dtime_end}' ''')
        
        result = await session.execute(query)

    return result.all()


def query_pattern():
    pattern = r'^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$'
    return re.compile(pattern)
import sqlite3
import psycopg2
from typing import List, Tuple
from datetime import datetime
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy import text
from model import DisData
from pydantic import AwareDatetime
import os

username = os.environ.get("POSTGRES_USER")
password = os.environ.get("POSTGRES_PASSWORD")
database = os.environ.get("POSTGRES_DB")
SQLALCHEMY_DATABASE_URL = f"postgresql://{username}:{password}@database/{database}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

def createDB():

    SQLModel.metadata.create_all(engine)
    return


    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS disdata (
                    MJD_date FLOAT PRIMARY KEY,
                    date_utc DATETIME NOT NULL,
                    timestamp DATETIME NOT NULL,
                    displacement FLOAT);
                ''')
        # cursor.execute("CREATE INDEX index ON data(date);")
        
        connection.commit()


def fillDB(records: List[Tuple[float, datetime, datetime, float]]):
    
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()
        connection.autocommit = False

        cursor.executemany('INSERT OR IGNORE INTO disdata (MJD_date, date_utc, timestamp, displacement) VALUES (?, ?, ?, ?)', records) # OR REPLACE

        connection.commit()

def fillDB2(records: List[DisData]):
    with Session(engine) as session:
        session.add_all(records)
        session.commit()


async def queryFromDB2(dtime_start: AwareDatetime, dtime_end: AwareDatetime):
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()

        query = '''SELECT *
                    FROM DisData d
                    WHERE d.timestamp BETWEEN ? AND ?''' 

        cursor.execute(query, (dtime_start, dtime_end))
        
        result = cursor.fetchall()
        result = list(zip(*result))
        
    return {"MJD_dates": result[0], "dates": result[1] ,"timezoneDates": result[2], "tzinfo": result[3], "displacements": result[4]}

async def queryFromDB(dtime_start: datetime, dtime_end: datetime):
    with Session(engine) as session:
        #query1 = select(DisData).distinct().where(DisData.timestamp.between(dtime_start, dtime_end))
        query2 = f'''SELECT DISTINCT ON ("MJD_date") *
                    FROM disdata d
                    WHERE d.timestamp BETWEEN '{dtime_start}' AND '{dtime_end}' '''
        #result = session.execute(query1).scalars().all()
        result = session.execute(text(query2)).all()

    return result
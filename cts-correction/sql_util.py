import sqlite3
from typing import List, Tuple
from datetime import datetime


def createDB():
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS data (
                    date DATETIME PRIMARY KEY,
                    timezone_date DATETIME,
                    displacement FLOAT NOT NULL);
                ''')
        # cursor.execute("CREATE INDEX index ON data(date);")
        
        connection.commit()


def fillDB(records: List[Tuple[datetime, datetime, float]]):
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()
        connection.autocommit = False

        cursor.executemany('INSERT OR IGNORE INTO data (date, timezone_date, displacement) VALUES (?, ?, ?)', records) # OR REPLACE

        connection.commit()


def queryFromDB(dtime_start: str, dtime_end: str):
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()

        query = '''SELECT *
                    FROM data d
                    WHERE d.date BETWEEN ? AND ?''' 

        cursor.execute(query, (dtime_start, dtime_end))
        
        result = cursor.fetchall()
        result = tuple(map(list, zip(*result)))
        
    return {"dates": result[0] ,"timestamps": result[1], "displacements": result[2]}
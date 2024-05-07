import sqlite3
from typing import List, Tuple


def createDB():
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS data (
                    date TEXT PRIMARY KEY,
                    displacement FLOAT NOT NULL)
                ''')
        
        connection.commit()


def fillDB(records: List[Tuple[str, float]]):
    with sqlite3.connect('/app/data/dataDB/data.db') as connection:
        cursor = connection.cursor()
        connection.autocommit = False

        cursor.executemany('INSERT OR IGNORE INTO data (date, displacement) VALUES (?, ?)', records) # OR REPLACE

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
        
    return {"dates": result[0], "displacements": result[1]}
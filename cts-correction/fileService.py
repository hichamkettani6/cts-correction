import asyncio
import os
import shutil
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

import aiofiles
from aiofiles.os import wrap
from aiopath import AsyncPath

from sql_util import fillDB

move = wrap(shutil.move)


class FileService():

    def __init__(self, pathData: str, des_pathData):
        self.pathData = pathData
        self.des_pathData = des_pathData

    async def get_paths(self) -> List[AsyncPath]:
        paths = [path async for path in AsyncPath(self.pathData).iterdir()]
        # return sorted(paths, key=os.path.getmtime)
        return paths

    async def read_file(self, file_path: AsyncPath):
        data: str = ''

        async with aiofiles.open(file_path) as file:
            lines = await file.readlines()
            for line in lines:
                if line.startswith('#'):
                    continue

                x, y = line.strip().split()
                x = float(x)
                x_unix = (x - 40587) * 86400
                date = datetime.fromtimestamp(
                    x_unix, tz=ZoneInfo('UTC')).replace(microsecond=False)

                # data.append(DisData(MJD_date=x, date_utc=date.strftime("%Y-%m-%d %H:%M:%S%z"),
                #                timestamp=date, displacement=float(y)))

                data += f"({x}, '{date.strftime("%Y-%m-%d %H:%M:%S%z")}', '{date}', {float(y)}), "

            return data.rstrip(', ')

    async def write_file(self, file_path: AsyncPath):
        data = await self.read_file(file_path)
        await asyncio.gather(fillDB(data), move(file_path, self.des_pathData))

    async def process_existing_files(self):
        paths = await self.get_paths()
        await asyncio.gather(*[self.write_file(path) for path in paths])
        # [await self.write_file(path) for path in paths]

    @staticmethod
    async def create_dirs(dirs):
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

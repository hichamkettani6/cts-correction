import asyncio
import pyinotify
import os
import shutil
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

import aiofiles
from aiofiles.os import wrap
from aiopath import AsyncPath
import logging
from sql_util import fillDB

move = wrap(shutil.move)
logger = logging.getLogger(__name__)


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
            cnt = 0
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
                cnt += 1
                if cnt == 50:
                    cnt = 0
                    if not await fillDB(data.rstrip(', ')):
                        return False
            if cnt > 0:
                cnt = 0
                if not  await fillDB(data.rstrip(', ')):
                    return False
            return True

    async def write_file(self, file_path: AsyncPath):
        if not "working.dat" in file_path.name:
            insert = await self.read_file(file_path)
            if insert:
                logger.info("Insert Ok move file")
                await move(file_path, self.des_pathData)

    async def process_existing_files(self):
        paths = await self.get_paths()
        # await asyncio.gather(*[ ])
        for path in paths:
            logger.info(f"process file {path.name}")
            await self.write_file(path)
        # [await self.write_file(path) for path in paths]

    @staticmethod
    async def create_dirs(dirs):
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)



class DefaultSetEvent(asyncio.Event):
    def __init__(self):
        super().__init__()
        self.set() #Set the event by default


class Handler(pyinotify.ProcessEvent):

    def __init__(self, fileService: FileService):
        self.fileService = fileService
        
    def process_default(self, event):
        if event.dir:
            return
        if event.mask is pyinotify.IN_CREATE or event.mask is pyinotify.IN_MOVED_TO:
            asyncio.create_task(self.fileService.write_file(event.pathname))


class ObserverManager:
    stop_event = DefaultSetEvent()

    def __init__(self, fileService: FileService):
        self.fileService = fileService
    
    async def start_observer(self):
        await self.up()
        loop = asyncio.get_event_loop()
        wm = pyinotify.WatchManager()
        wm.add_watch(self.fileService.pathData, pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO, rec=True)
        event_handler = Handler(self.fileService)
        notifier = pyinotify.AsyncioNotifier(wm, loop, default_proc_fun=event_handler)

        try:
            await self.stop_event.wait()
        finally:
            await self.down()
            notifier.stop()

    @classmethod
    async def is_up(cls) -> bool:
        return not ObserverManager.stop_event.is_set()
    @classmethod
    async def up(cls):
        cls.stop_event.clear()
    @classmethod
    async def down(cls):
        cls.stop_event.set()
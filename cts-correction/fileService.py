import os
import shutil
import asyncio
import pyinotify
import aiofiles
from aiofiles.os import wrap
from aiopath import AsyncPath
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import List
from sql_util import fillDB


move = wrap(shutil.move)

class FileService():

    def __init__(self, pathData: str, des_pathData):
        self.pathData = pathData
        self.des_pathData = des_pathData

    async def get_paths(self) -> List[AsyncPath]:
        paths = [path async for path in AsyncPath(self.pathData).iterdir()]
        #return sorted(paths, key=os.path.getmtime)
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
                x_unix = (x-40587)*86400
                date =  datetime.fromtimestamp(x_unix, tz=ZoneInfo('UTC')).replace(microsecond=False)

                #data.append(DisData(MJD_date=x, date_utc=date.strftime("%Y-%m-%d %H:%M:%S%z"),
                #                timestamp=date, displacement=float(y)))

                data += f"({x}, '{date.strftime("%Y-%m-%d %H:%M:%S%z")}', '{date}', {float(y)}), "

            return data.rstrip(', ')
    
    async def write_file(self, file_path: AsyncPath):
        data = await self.read_file(file_path)
        await asyncio.gather(fillDB(data), move(file_path, self.des_pathData))

    async def process_existing_files(self):
        paths = await self.get_paths()
        await asyncio.gather(*[self.write_file(path) for path in paths])
        #[await self.write_file(path) for path in paths]

    @staticmethod
    async def create_dirs(dirs):
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir, exist_ok=True)
                os.chmod(dir, mode=0o757)


'''
        
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_CREATED, EVENT_TYPE_MOVED

class DefaultSetEvent(asyncio.Event):
    def __init__(self):
        super().__init__()
        self.set()  # Set the event by default

class Handler(FileSystemEventHandler):
    def __init__(self, fileService):
        self.fileService = fileService

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.event_type in {EVENT_TYPE_CREATED, EVENT_TYPE_MOVED}:
            asyncio.create_task(self.fileService.write_file(event.src_path))

class ObserverManager:
    stop_event = DefaultSetEvent()

    def __init__(self, fileService):
        self.fileService = fileService

    async def start_observer(self):
        await self.up()
        event_handler = Handler(self.fileService)
        observer = Observer()
        observer.schedule(event_handler, self.fileService.pathData, recursive=True)
        #observer.start()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, observer.start)

        try:
            await self.stop_event.wait()
        finally:
            observer.stop()
            observer.join()
            await self.down()

    @classmethod
    async def is_up(cls):
        return not cls.stop_event.is_set()

    @classmethod
    async def up(cls):
        cls.stop_event.clear()

    @classmethod
    async def down(cls):
        cls.stop_event.set()

'''








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
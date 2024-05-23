#!/usr/bin/env python
# coding: utf-8

# In[47]:


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 13:50:22 2024

@author: cts
"""

import os
from pathlib import Path
import asyncio
from aiopath import AsyncPath
import aiofiles
from aiofiles.os import wrap
#import csv
#import re
import shutil
#import time
import datetime
from datetime import datetime
import math
import numpy as np
#from sklearn.linear_model import LinearRegression
#import statsmodels.api as sm
#import matplotlib.pyplot as plt
#import matplotlib.dates as mdates

import plotly.express as px
import pandas as pd
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from typing import Annotated, List
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
#import requests
import json
from model import DisData
from compress_json import compress, decompress
from sql_util import *
from zoneinfo import ZoneInfo



# In[2]:

DATA_PATH = "/app/data/todo"
DES_DATA_PATH = "/app/data/done"
DB_PATH = "/app/data/dataDB"

#TZ = os.environ.get("TZ")

#files = sorted(os.listdir(DATA_PATH))
#print(files)


#files_basenames = []
#for file_path in files_paths:
#  files_basenames.append(os.path.basename(file_path))
#print(files_basenames)


# In[3]:

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
        await fillDB(data)

    async def process_existing_files(self):
        await createDB()
        paths = await self.get_paths()
        await asyncio.gather(*[self.write_file(path) for path in paths])

    
    async def read_data(self):
        allData: List[DisData] = list()
        paths = await self.get_paths()

        for path in paths:
            async with aiofiles.open(path) as file:
            
                lines = await file.readlines()
                for line in lines:
                    if line.startswith('#'):
                        continue

                    x, y = line.strip().split()
                    x = float(x)
                    x_unix = (x-40587)*86400
                    date =  datetime.fromtimestamp(x_unix, tz=ZoneInfo('UTC')).replace(microsecond=False)

                    data = DisData(MJD_date=x, date_utc=date.strftime("%Y-%m-%d %H:%M:%S%z"), timestamp=date, displacement=float(y))
                    allData.append(data)
                    

            await move(path, self.des_pathData)
                
        return allData
    
    async def writeToDB(self):

        [await move(p, self.pathData) for p in Path(self.des_pathData).iterdir()]

        await createDB()

        allData = await self.read_data()
        await fillDB(allData)

    


app = FastAPI()


@app.middleware('http')
async def dataToDB_handler(request: Request, call_next):
    if request.url.path == "/write_toDB":
        request.scope["fileService"] = FileService(DATA_PATH, DES_DATA_PATH)

    response = await call_next(request)
    return response


@app.get("/write_toDB")
async def write_data_toDB(request: Request):
    fileService = request.scope.get("fileService")
    await asyncio.gather(fileService.process_existing_files())
    #await fileService.writeToDB()

    return {"status": 200}


@app.get("/", response_class=HTMLResponse)
async def get_plot():

    df = pd.DataFrame({
        'time [MJD]': x[::3600],
        'date [s]': x_date[::3600],
        'utc(it) - hrog output [s]': y[::3600]
    })

    fig1 = px.line(df, x='time [MJD]', y='utc(it) - hrog output [s]', title='hrog output with cts corrections')
    fig1.update_layout(
       title={
           'x':0.5,
           'xanchor':'center',
           'yanchor':'top'},
       title_font=dict(size=24),
       plot_bgcolor='lavender')

    fig2 = px.line(df, x='date [s]', y='utc(it) - hrog output [s]', title='hrog output with cts corrections')
    fig2.update_layout(
       title={
           'x':0.5,
           'xanchor':'center',
           'yanchor':'top'},
       title_font=dict(size=24),
       plot_bgcolor='lavender')

    return fig1.to_html(full_html=False) + fig2.to_html(full_html=False)


@app.get("/graph-data")
async def get_graph_data(dtime_start: Annotated[str, Query(regex=query_pattern())],
                         dtime_end: Annotated[str, Query(regex=query_pattern())]):


    data = await queryFromDB(datetime.strptime(dtime_start, "%Y-%m-%d %H:%M:%S"),
                               datetime.strptime(dtime_end, "%Y-%m-%d %H:%M:%S"))
    
    
    try:
        timestamps, displacements = zip(*list(map(lambda d: (d.timestamp, d.displacement), data)))
    except ValueError:
        timestamps = list()
        displacements = list()
 

    df = {  
        'data':[{
           'x': timestamps,
           'y': displacements
           }],
       'layout':{
           "title": "hrog output with cts corrections",
           "xaxis": {
               "title": 'date [s]',
            },
            "yaxis": {
                "title": 'utc(it) - hrog output [s]',
            }
        }
    }
      
    return {"list": [df]}


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/graph-data-html", response_class=HTMLResponse)
async def get_graph_data_html(request: Request,
                              dtime_start: Annotated[str | None, Query(regex=query_pattern())] = None,
                              dtime_end: Annotated[str | None, Query(regex=query_pattern())] = None):
   
    if dtime_start and dtime_end:
        dateFrom, timeFrom = dtime_start.split()
        dateTo, timeTo = dtime_end.split()
        return templates.TemplateResponse(request=request, name="graph_corrections.html",
                                          context={"dateFrom": dateFrom, "timeFrom": timeFrom, 
                                                   "dateTo": dateTo, "timeTo":timeTo})
    
    return templates.TemplateResponse(request=request, name="graph_corrections.html")





# In[57]:

'''
#plt.figure(figsize=(10,6))
fig, ax = plt.subplots()
ax.plot(x[::3600],y[::3600],'.-',label='hrog trend')
plt.xlabel('time [MJD]')
plt.ylabel('utc(it) - hrog output [s]')
plt.grid()
plt.legend()
plt.title('hrog output with cts corrections')
#plt.show()
#plt.savefig(DATA_PATH+'prova.png')

fig, ax = plt.subplots()
ax.plot(x_date[::3600],y[::3600],'.-',label='hrog trend')
plt.xlabel('time [MJD]')
plt.ylabel('utc(it) - hrog output [s]')
plt.grid()
plt.legend()
plt.title('hrog output with cts corrections')
ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=(1,1)))
plt.show()

'''
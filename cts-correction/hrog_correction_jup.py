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
from aiopath import AsyncPath
import aiofiles
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
from typing import Annotated
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

TZ = os.environ.get("TZ")

#files = sorted(os.listdir(DATA_PATH))
#print(files)


#files_basenames = []
#for file_path in files_paths:
#  files_basenames.append(os.path.basename(file_path))
#print(files_basenames)


# In[3]:

class FileService():
    def __init__(self, pathData: str, des_pathData):
        self.pathData = pathData
        self.des_pathData = des_pathData

    async def get_paths(self):
        paths = [path async for path in AsyncPath(self.pathData).iterdir()]
        return sorted(paths, key=os.path.getmtime)
    
    async def read_data(self):
        allData: List[DisData] = list()

        for path in await self.get_paths():
            async with aiofiles.open(path) as file:

                lines = await file.readlines()
                for line in lines:
                    if line.startswith('#'):
                        continue

                    x, y = line.strip().split()
                    x = float(x)
                    x_unix = (x-40587)*86400
                    date =  datetime.fromtimestamp(x_unix, tz=ZoneInfo('UTC')).replace(microsecond=False)

                    data = DisData(MJD_dates=x, date_utc=date, displacement=float(y), tz=TZ)
                    data._timestamp = date
                    allData.append(data)

            shutil.move(path, self.des_pathData)
                
        return allData
    
    async def writeToDB(self):

        if len(list(Path(DB_PATH).iterdir())) != 0:
            [shutil.move(p, self.pathData) for p in Path(self.des_pathData).iterdir()]
            os.remove(f'{DB_PATH}/data.db')

        if len(list(Path(DB_PATH).iterdir())) == 0:
            createDB()

        allData = await self.read_data()
        #return list(map(lambda d: (d.date_utc, d.timestamp), allData))
        fillDB2(allData)

        return {"status": 200}
        #ToInsertData = list(map(lambda data: tuple(data.__dict__.values()), allData))
        #fillDB(ToInsertData)
    


fileService = FileService(DATA_PATH, DES_DATA_PATH)
                



app = FastAPI()



@app.get("/write_toDB")
async def write_data_toDB():

    return await fileService.writeToDB()

    '''#debug..
    [shutil.move(p, DATA_PATH) for p in Path(DES_DATA_PATH).iterdir()]
    if len(list(Path(DB_PATH).iterdir())) != 0:
        os.remove(f'{DB_PATH}/data.db')

    if len(list(Path(DB_PATH).iterdir())) == 0:
        createDB()

    data = Data()
    files_paths = await get_paths()

    for path in files_paths:
        
        with open(path) as file:
            #reader = csv.reader(filter(lambda row: row[0]!='#', file), delimiter=' ')
            #print(reader)
            lines = file.readlines()
            for line in lines:
                if line.startswith("#"):    
                    continue

                line = line.strip()
                x, y = line.split()
                x_unix = (float(x)-40587)*86400
                date =  datetime.fromtimestamp(x_unix).strftime('%Y-%m-%d %H:%M:%S')

                #data.timezoneDates.append(data.to_datetime(date, TZ))
                data.dates.append(date)
                data.add_timezoneDate(date, TZ)
                data.displacements.append(float(y))

        shutil.move(path.absolute(), DES_DATA_PATH)

    fillDB(zip(data.dates, data.timezoneDates,data.displacements))


    return {"status": "DB createad!"}'''


#using compress-json..
@app.get("/read")
async def read_data(dtime_start: str, dtime_end: str):

    start_date = dtime_start.split()[0].replace('-', '')
    end_date = dtime_end.split()[0].replace('-', '')

    unix_all = list()

    data = Data()

    for path in [p for p in files_paths if start_date <= str(int(p.name.split('_')[2])-1) <= end_date]: # use binary search?!
        with open(path) as file:
            #reader = csv.reader(filter(lambda row: row[0]!='#', file), delimiter=' ')
            #print(reader)
            lines = file.readlines()
            for line in lines:
                if line.startswith('#'):
                    continue

                line = line.strip()
                x, y = line.split()
                x_unix = (float(x)-40587)*86400
                
                date = datetime.fromtimestamp(x_unix).strftime('%Y-%m-%d %H:%M:%S')
                
                if str(int(path.name.split('_')[2])-1) == start_date and \
                        date.split()[1] < dtime_start.split()[1]:
                    continue
                
                if str(int(path.name.split('_')[2])-1) == end_date and \
                        date.split()[1] > dtime_end.split()[1]:
                    break

                data.dates.append(date)
                data.displacements.append(float(y))
                
                unix_all.append(x_unix)

    
    with open("/app/data/dates.txt", "w") as f:
        f.write(str(compress({"dates": data.dates, "disp": data.displacements})))
    with open("/app/data/unix.txt", "w") as f:
        f.write(str(compress({"dates": unix_all, "disp": data.displacements})))

    return compress(
        {"dates": data.dates,
         "disp": data.displacements}
    )

    return compress(
        {"dates": unix_all,
         "disp": data.displacements}
    )
    return {"dates": data.dates, "displacements": data.displacements}


#print(x_values)
#print(y_values)


# In[56]:


#x=[float(i) for i in x_values] # MJD
#x_unix=[(float(i)-40587)*86400 for i in x_values] # convert from MJD to unix 
#x_unix_int=[math.modf(i) for i in x_unix]
#y=[float(j) for j in y_values]


# In[54]:


#x_date=[datetime.fromtimestamp(k).strftime('%Y-%m-%d %H:%M:%S') for k in x_unix]
#x_date_TZ = ['T'.join(date.split()) + 'Z' for date in x_date]
# from linux seconds to date




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
async def get_graph_data(dtime_start: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$')],
                         dtime_end: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$')]):


    data = await queryFromDB(datetime.strptime(dtime_start, "%Y-%m-%d %H:%M:%S"), datetime.strptime(dtime_end, "%Y-%m-%d %H:%M:%S"))
    #timestamps, displacements = zip(*list(map(lambda d: (d._timestamp, d.displacement), data)))
    dates = data.get("dates")
    timezoneDates = data.get("timezoneDates")  
    displacements = data.get("displacements")
    

    df = {  
        'data':[{
           'x': timezoneDates,
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
                              dtime_start: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$')] = None,
                              dtime_end: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$')] = None):
   
    if dtime_start or dtime_end:
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
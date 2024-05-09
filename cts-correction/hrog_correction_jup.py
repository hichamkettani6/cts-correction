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
import pendulum
import json
from model import Data
from compress_json import compress, decompress
from sql_util import *





# In[2]:

DATA_PATH = "/app/data/todo"
DES_DATA_PATH = "/app/data/done"
DB_PATH = "/app/data/dataDB"

TZ = os.environ.get("TZ")

#files = sorted(os.listdir(DATA_PATH))
#print(files)


files_paths = sorted(Path(DATA_PATH).iterdir(), key=os.path.getmtime)
#files_basenames = []
#for file_path in files_paths:
#  files_basenames.append(os.path.basename(file_path))
#print(files_basenames)


# In[3]:

app = FastAPI()



@app.get("/write_toDB")
async def write_data_toDB():

    [shutil.move(p, DATA_PATH) for p in Path(DES_DATA_PATH).iterdir()]

    if len(list(Path(DB_PATH).iterdir())) == 0:
        createDB()

    data = Data()

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
                data.dates.append('T'.join(date.split()) + 'Z')
                timestamp = pendulum.from_format(date, "YYYY-MM-DD HH:mm:ss")
                data.timestamps.append(timestamp.in_tz(TZ))
                data.displacements.append(float(y))

        shutil.move(path.absolute(), DES_DATA_PATH)

        fillDB(zip(data.dates, data.timestamps,data.displacements))


    return {"status": "DB createad!"}


#using compress-json..
@app.get("/read")
async def read_data(dtime_start: str, dtime_end: str):

    start_date = dtime_start.split('T')[0].replace('-', '')
    end_date = dtime_end.split('T')[0].replace('-', '')

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
                        date.split()[1] < dtime_start.strip('Z').split('T')[1]:
                    continue
                
                if str(int(path.name.split('_')[2])-1) == end_date and \
                        date.split()[1] > dtime_end.strip('Z').split('T')[1]:
                    break

                data.dates.append('T'.join(date.split()) + 'Z')
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
async def get_graph_data(dtime_start: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1])T[0-5][0-9]:[0-5][0-9]:[0-5][0-9]Z$')],
                         dtime_end: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1])T[0-5][0-9]:[0-5][0-9]:[0-5][0-9]Z$')]):


    data = queryFromDB(dtime_start, dtime_end)

    return data.get("timestamps")

    x_date_TZ = data.get("dates")  
    y = data.get("displacements")

    df = {  
        'data':[{
           'x': x_date_TZ,
           'y': y
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
                              dtime_start: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1])T[0-5][0-9]:[0-5][0-9]:[0-5][0-9]Z$')] = None,
                              dtime_end: Annotated[str | None, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1])T[0-5][0-9]:[0-5][0-9]:[0-5][0-9]Z$')] = None):
   
    if dtime_start or dtime_end:
        dateFrom, timeFrom = dtime_start.strip('Z').split('T')
        dateTo, timeTo = dtime_end.strip('Z').split('T')
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
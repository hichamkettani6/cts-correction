#!/usr/bin/env python
# coding: utf-8

import os
import asyncio
from datetime import datetime
import numpy as np
import plotly.express as px
import pandas as pd
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from typing import Annotated
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from model import DisData, Range
from sql_util import createDB, query_pattern, queryFromDB
from fileService import FileService



DATA_PATH = "/app/data/todo"
DES_DATA_PATH = "/app/data/done"
DB_PATH = "/app/data/dataDB"
    

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await createDB()


@app.middleware('http')
async def dataToDB_handler(request: Request, call_next):
    if request.url.path == "/write_toDB":
        request.scope["fileService"] = FileService(DATA_PATH, DES_DATA_PATH)
    elif request.url.path == "/graph-data":
        request.scope["TZ"] = os.environ.get("TZ")

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
async def get_graph_data(request:Request, dtime_start: Annotated[str, Query(regex=query_pattern())],
                         dtime_end: Annotated[str, Query(regex=query_pattern())]):

    timezone = request.scope.get("TZ")
    query_dates = Range(dtime_start=dtime_start, dtime_end=dtime_end)
    data = await queryFromDB(query_dates, timezone)
    
    try:
        timestamps, displacements = zip(*list(map(lambda d: (d.timestamp, d.displacement), data)))
    except ValueError:
        timestamps = list()
        displacements = list()
 
    df = {
        'graph_id': "cts",
        'data': [{
            'x': timestamps[::30],
            'y': displacements[::30],
            "mode": "lines",
            "name": "CTS Time",}],
        'layout': {
            "title": "HROG Output with CTS Corrections",
            "xaxis": {"title": 'Time [s]',},
            "yaxis": {"title": 'Time Displacements [s]',},
            "legend": {
                "x": 1,
                "y": 1,
                "xanchor": 'left',
                "yanchor": 'middle',
                "borderwidth": 0.5
            },
            "showlegend": True
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
                                                   "dateTo": dateTo, "timeTo":timeTo,
                                                    "generator_interval_min": 5})
    
    return templates.TemplateResponse(request=request, name="graph_corrections.html",
                                       context={"generator_interval_min": 5})





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
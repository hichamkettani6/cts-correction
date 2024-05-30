#!/usr/bin/env python
# coding: utf-8

import os
import asyncio
import uvloop
import plotly.express as px
import pandas as pd
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from typing import Annotated
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from model import DisData, Range
from sql_util import createDB, query_pattern, queryFromDB
from fileService import FileService, ObserverManager


PATHS = {
    "DATA_PATH": "/app/data/todo",
    "DES_DATA_PATH": "/app/data/done"
    }
    

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    await asyncio.gather(createDB(), FileService.create_dirs(PATHS.values()))

@app.on_event("shutdown")
async def on_shutdown():
    await ObserverManager.down()


@app.middleware('http')
async def dataToDB_handler(request: Request, call_next):
    if request.url.path == "/write_toDB":
        request.scope["fileService"] = FileService(PATHS["DATA_PATH"], PATHS["DES_DATA_PATH"])
    elif request.url.path == "/graph-data":
        request.scope["TZ"] = os.environ.get("TZ")
    elif request.url.path == "/graph-data-html":
        app.mount("/static", StaticFiles(directory="static"), name="static")
        request.scope["templates"] = Jinja2Templates(directory="templates")

    response = await call_next(request)
    return response


@app.get("/write_toDB")
async def write_data_toDB(request: Request):
    if await ObserverManager.is_up():
        return {"status": 200, "detail": "Observer is already up!"}

    fileService = request.scope.get("fileService")
    asyncio.gather(ObserverManager(fileService).start_observer(), fileService.process_existing_files())

    return {"status": 200}



@app.get("/graph-data")
async def get_graph_data(request:Request, dtime_start: Annotated[str, Query(regex=query_pattern())],
                         dtime_end: Annotated[str, Query(regex=query_pattern())]):

    timezone = request.scope.get("TZ")
    query_dates = Range(dtime_start=dtime_start, dtime_end=dtime_end)
    data = await queryFromDB(query_dates, timezone)
    
    try:
        timestamps, displacements = zip(*data)
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


@app.get("/graph-data-html", response_class=HTMLResponse)
async def get_graph_data_html(request: Request,
                              dtime_start: Annotated[str | None, Query(regex=query_pattern())] = None,
                              dtime_end: Annotated[str | None, Query(regex=query_pattern())] = None):

    templates = request.scope.get("templates")

    if dtime_start and dtime_end:
        dateFrom, timeFrom = dtime_start.split()
        dateTo, timeTo = dtime_end.split()
        return templates.TemplateResponse(request=request, name="graph_corrections.html",
                                          context={"dateFrom": dateFrom, "timeFrom": timeFrom, 
                                                   "dateTo": dateTo, "timeTo":timeTo,
                                                    "generator_interval_min": 5})
    
    return templates.TemplateResponse(request=request, name="graph_corrections.html",
                                       context={"generator_interval_min": 5})

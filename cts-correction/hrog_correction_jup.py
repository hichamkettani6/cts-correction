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
#import shutil
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
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from typing import Annotated



# In[2]:


DATA_PATH="./app/data"

#files = sorted(os.listdir(DATA_PATH))
#print(files)


files_paths = sorted(Path(DATA_PATH).iterdir(), key=os.path.getmtime)
#files_basenames = []
#for file_path in files_paths:
#  files_basenames.append(os.path.basename(file_path))
#print(files_basenames)


# In[3]:


x_values = list()
y_values = list()
for name in files_paths:
    with open(name) as file:
        #reader = csv.reader(filter(lambda row: row[0]!='#', file), delimiter=' ')
        #print(reader)
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if not line.startswith("#"):
                x, y = line.split()
                x_values.append(x)
                y_values.append(y)


#print(x_values)
#print(y_values)


# In[56]:


x=[float(i) for i in x_values] # MJD
x_unix=[(float(i)-40587)*86400 for i in x_values] # convert from MJD to unix 
x_unix_int=[math.modf(i) for i in x_unix]
y=[float(j) for j in y_values]


# In[54]:


x_date=[datetime.fromtimestamp(k).strftime('%Y-%m-%d %H:%M:%S') for k in x_unix]
# from linux seconds to date



app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get_plot():
    df1 = pd.DataFrame({
        'time [MJD]': x[::3600],
        'utc(it) - hrog output [s]': y[::3600]
    })
    fig1 = px.line(df1, x='time [MJD]', y='utc(it) - hrog output [s]', title='hrog output with cts corrections')

    df2 = pd.DataFrame({
        'date [s]': x_date[::3600],
        'utc(it) - hrog output [s]': y[::3600]
    })
    fig2 = px.line(df2, x='date [s]', y='utc(it) - hrog output [s]', title='hrog output with cts corrections')

    return fig1.to_html(full_html=False) + fig2.to_html(full_html=False)


@app.get("/graph-data", response_class=HTMLResponse)
async def get_graph_data(dtime_start: Annotated[str, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$')] = x_date[0],
                          dtime_end: Annotated[str, Query(pattern='^[0-9]{4}-((0[0-9])|(1[0-2]))-(([0-2][0-9])|3[0-1]) [0-5][0-9]:[0-5][0-9]:[0-5][0-9]$')] = x_date[-1]):

    start: int = x_date.index(dtime_start)
    end: int = x_date.index(dtime_end)

    df = pd.DataFrame({
        'date [s]': x_date[start: end+1:600],
        'utc(it) - hrog output [s]': y[start: end+1:600]
    })

    fig = px.line(df, x='date [s]', y='utc(it) - hrog output [s]', title='hrog output with cts corrections', markers=True)

    return fig.to_html(full_html=False)


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
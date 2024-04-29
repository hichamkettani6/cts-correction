FROM python:3.12

ENV PYTHONPATH="/app"

RUN pip install --no-cache --upgrade fastapi
RUN pip install --no-cache --upgrade pydantic
RUN pip install --no-cache --upgrade uvicorn
RUN pip install --no-cache --upgrade aiopath
RUN pip install --no-cache --upgrade aiofiles
RUN pip install --no-cache --upgrade uvloop
RUN pip install --no-cache --upgrade plotly
RUN pip install --no-cache --upgrade pandas
RUN pip install --no-cache --upgrade matplotlib
RUN pip install --no-cache --upgrade IPython
RUN pip install --no-cache --upgrade jinja2


CMD ["uvicorn", "app.hrog_correction_jup:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
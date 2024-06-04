FROM python:3.12

ENV PYTHONPATH="/app"

RUN pip install  --upgrade fastapi
RUN pip install  --upgrade pydantic
RUN pip install  --upgrade uvicorn
RUN pip install  --upgrade aiopath
RUN pip install  --upgrade aiofiles
RUN pip install  --upgrade uvloop
RUN pip install  --upgrade plotly
RUN pip install  --upgrade pandas
RUN pip install  --upgrade matplotlib
RUN pip install  --upgrade jinja2
RUN pip install  --upgrade sqlmodel
RUN pip install  --upgrade asyncpg
RUN pip install  --upgrade pyinotify
RUN pip install  --upgrade pyasyncore

CMD ["uvicorn", "app.hrog_correction_jup:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips='*'"]
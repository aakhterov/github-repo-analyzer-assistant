FROM python:3.10-slim

MAINTAINER Alexander Akhterov "a.ahterov@gmail.com"

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY main.py /app
COPY config.json /app

RUN mkdir /app/logs
RUN mkdir /app/data
WORKDIR /app

EXPOSE 5000

CMD gunicorn -b 0.0.0.0:5000 -w 2 --log-level=info 'main:app'

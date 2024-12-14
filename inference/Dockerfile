FROM python:3.8-slim

COPY  ./sandbox .
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN apt-get update -y && apt-get install -y gcc
RUN pip install -r requirements.txt


CMD ["python3", "test.py"]
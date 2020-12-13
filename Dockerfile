FROM python:3.9.1-buster AS base

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y upgrade && apt-get install -y sqlite3 libsqlite3-dev && apt-get autoremove && apt-get clean

RUN pip install --no-cache-dir poetry==1.1.4
RUN poetry config virtualenvs.create false
COPY poetry.lock pyproject.toml ./
RUN poetry install
COPY . .

EXPOSE 8080

ENTRYPOINT ["inv", "start"]
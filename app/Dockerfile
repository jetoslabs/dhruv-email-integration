FROM python:3.8

# set env variables
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.0.0

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc \
  && apt-get clean

# package manager for python deps:
RUN pip install "poetry==$POETRY_VERSION"

# set working dir
WORKDIR usr/src/o365-manager/app

# Creating folders, and files for a project:
COPY . .

## Project initialization:
RUN poetry config virtualenvs.create false && poetry install





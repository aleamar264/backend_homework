FROM python:3.12.0-bookworm as builder

RUN pip install poetry==1.8.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml ./
RUN touch README.md

RUN poetry install  --no-dev && rm -rf $POETRY_CACHE_DIR

FROM python:3.12-slim-bookworm as runtime


WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./backend_homework/api .
COPY ./backend_homework/api/start.sh ./start
RUN sed -i 's/\r$//g' ./start
RUN chmod +x ./start
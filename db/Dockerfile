FROM python:3.11-slim AS base

ENV COMMAND="init"
ENV DB_URL="postgresql://postgres:5432/note_rags_db"

RUN pip install uv

FROM base AS package

COPY ./db/ ./

RUN uv sync

CMD uv run note-rags-db $COMMAND --database-url $DB_URL



FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

# Copy shared common library and service manifest
COPY apps/ingestion/pyproject.toml apps/ingestion/poetry.lock* ./apps/ingestion/
COPY libs/common/ ./libs/common/

WORKDIR /app/apps/ingestion
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the ingestion service code
COPY apps/ingestion/ ./

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
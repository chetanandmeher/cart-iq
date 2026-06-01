FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

# Copy shared common library and service manifest
COPY apps/analytics/pyproject.toml apps/analytics/poetry.lock* ./apps/analytics/
COPY libs/common/ ./libs/common/

WORKDIR /app/apps/analytics
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the analytics service code
COPY apps/analytics/ ./

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

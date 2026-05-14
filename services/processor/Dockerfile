FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

# Processor doesn't expose a web port, it just consumes from Kafka
CMD ["python", "-m", "app.main"]

FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY apps/simulator/pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY apps/simulator/src/ ./src/

CMD ["python", "src/simulate_events.py"]
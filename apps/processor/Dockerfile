FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

# Copy shared common library and service manifest
COPY apps/processor/pyproject.toml apps/processor/poetry.lock* ./apps/processor/
COPY libs/common/ ./libs/common/

WORKDIR /app/apps/processor
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the processor service code
COPY apps/processor/ ./

# Run the stream processor from src.main
CMD ["python", "-m", "src.main"]

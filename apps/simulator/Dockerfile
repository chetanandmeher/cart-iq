FROM python:3.11-slim

WORKDIR /app

RUN pip install requests redis

COPY simulate_events.py .

CMD ["python", "simulate_events.py"]
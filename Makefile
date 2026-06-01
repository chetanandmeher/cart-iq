# CartIQ Monorepo Management Makefile

.PHONY: dev build down logs test clean

dev:
	docker-compose up -d --remove-orphans

build:
	docker-compose build

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	@echo "Running tests..."
	poetry run pytest apps/ingestion/tests/
	poetry run pytest apps/processor/tests/
	poetry run pytest apps/analytics/tests/

clean:
	docker-compose down -v

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
	cd libs/common && poetry run pytest -c pyproject.toml ../../tests/common_test/
	cd apps/ingestion && poetry run pytest -c pyproject.toml ../../tests/ingestion_test/
	cd apps/processor && poetry run pytest -c pyproject.toml ../../tests/processor_test/
	cd apps/analytics && poetry run pytest -c pyproject.toml ../../tests/analytics_test/
	cd apps/simulator && poetry run pytest -c pyproject.toml ../../tests/simulator_test/
	cd apps/dashboard && npm test

clean:
	docker-compose down -v

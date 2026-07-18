SHELL := /bin/bash

.PHONY: dev up down logs test lint format seed backup restore smoke-routing

dev:
	docker compose --profile dev up --build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	cd backend && python -m pytest
	cd frontend && npm test -- --run

lint:
	cd backend && ruff check app tests && mypy app
	cd frontend && npm run lint

format:
	cd backend && ruff format app tests && ruff check --fix app tests
	cd frontend && npm run format

seed:
	docker compose run --rm backend python -m app.seed

backup:
	./scripts/backup_db.sh

restore:
	./scripts/restore_db.sh $(BACKUP)

smoke-routing:
	./scripts/smoke_graphhopper.sh

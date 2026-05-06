PYTHON := .venv/bin/python

.PHONY: setup validate db-up api frontend dev stop test-backend

setup:
	./scripts/setup-mac.sh

validate:
	./scripts/validate-env.sh

db-up:
	docker compose up -d postgres

api:
	$(PYTHON) -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload

frontend:
	cd frontend && npm run dev

dev:
	./scripts/start-dev.sh

stop:
	./scripts/stop-dev.sh

test-backend:
	$(PYTHON) -m pytest backend/tests --cov=backend/app --cov-report=term-missing

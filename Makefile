PYTHON := .venv/bin/python

.PHONY: setup validate db-up api dev stop

setup:
	./scripts/setup-mac.sh

validate:
	./scripts/validate-env.sh

db-up:
	docker compose up -d postgres

api:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

dev:
	./scripts/start-dev.sh

stop:
	./scripts/stop-dev.sh

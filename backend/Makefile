.PHONY: install install-dev run migrate makemigrations test coverage check lint format shell collectstatic docker-local docker-staging docker-production test-rate-limit

PY ?= python

install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/development.txt

run:
	$(PY) manage.py runserver

migrate:
	$(PY) manage.py migrate

makemigrations:
	$(PY) manage.py makemigrations

test:
	pytest

test-rate-limit:
	pytest -k "throttle or rate_limit"

coverage:
	pytest --cov=. --cov-report=term-missing

check:
	$(PY) manage.py check

lint:
	ruff check .

format:
	ruff format .

shell:
	$(PY) manage.py shell

collectstatic:
	$(PY) manage.py collectstatic --noinput

docker-local:
	docker compose --env-file .env -f docker/local/docker-compose.yml up --build

docker-staging:
	docker compose -f docker/staging/docker-compose.yml up --build -d

docker-production:
	docker compose -f docker/production/docker-compose.yml up --build -d

.PHONY: backup backup-local seed
backup:
	$(PY) manage.py backup_db

backup-local:
	$(PY) manage.py backup_db --local-only

seed:
	$(PY) manage.py seed_abo_samra

.RECIPEPREFIX := >

.PHONY: dev api frontend migrate test-api test-frontend test-e2e lint

dev:
>docker compose up --build

api:
>cd apps/api && python -m uvicorn cat_api.main:app --reload --host 127.0.0.1 --port 8000

frontend:
>cd apps/frontend && npm run dev

migrate:
>cd apps/api && alembic upgrade head

test-api:
>cd apps/api && python -m pytest

test-frontend:
>cd apps/frontend && npm run test

test-e2e:
>cd apps/frontend && npm run test:e2e

lint:
>cd apps/api && python -m ruff check . && python -m ruff format --check .
>cd apps/frontend && npm run lint

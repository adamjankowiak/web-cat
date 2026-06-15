.RECIPEPREFIX := >

.PHONY: dev api frontend migrate test-api

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

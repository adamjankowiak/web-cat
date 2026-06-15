FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/apps/api

COPY apps/api/pyproject.toml ./
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
COPY apps/api/src ./src

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "cat_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 1 — build: install all dependencies with uv
FROM python:3.14-slim AS build
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml ./
# Create a minimal uv.lock if one doesn't exist yet
RUN uv sync --no-dev
COPY . .

# Stage 2 — runtime: only built artefacts and runtime deps
FROM python:3.14-slim
WORKDIR /app
COPY --from=build /app/.venv .venv
COPY --from=build /app/src/app ./app
COPY --from=build /app/alembic ./alembic
COPY --from=build /app/alembic.ini ./alembic.ini
ENV PATH="/app/.venv/bin:$PATH"
CMD ["sh", "-c", \
  "alembic upgrade head && \
  uvicorn app.main:app --host 0.0.0.0 --port 8000"]

FROM python:3.12.13 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app


RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt
FROM python:3.12.13-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

# Must match fly.toml [http_service] internal_port. uvicorn is already in
# requirements.txt (the FastAPI CLI is not — it needs fastapi[standard]).
ENV PORT=8080 \
    ADAMSY_REQUIRE_ADMIN_TOKEN=1
EXPOSE 8080
CMD ["/app/.venv/bin/uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8080"]

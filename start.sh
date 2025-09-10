#!/bin/bash
set -e
echo "Running Alembic migrations..."
alembic upgrade head
echo "Starting the FastAPI application..."
gunicorn -k uvicorn.workers.UvicornWorker app.main:app --workers 4 --bind 0.0.0.0:8000
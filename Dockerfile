FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . .

RUN uv sync

# Set a safe fallback default just in case it's missing from the .env
ENV WORKERS=4

# Use sh -c to evaluate $WORKERS, and 'exec' to ensure proper PID 1 signal handling
CMD ["sh", "-c", "exec uv run gunicorn app.main:app --workers $WORKERS --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"]
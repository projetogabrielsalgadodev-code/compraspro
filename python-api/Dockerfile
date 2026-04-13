FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Render injects $PORT; fallback to 8000 for local
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

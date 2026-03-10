# Dockerfile
FROM python:3.11-slim

# Prevent Python from writing pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional but helpful for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend /app/backend
COPY pyproject.toml /app/pyproject.toml

# Expose API port
EXPOSE 8000

# Run API
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
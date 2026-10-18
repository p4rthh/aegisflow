# AegisFlow Production Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies (libgomp1 required for LightGBM OpenMP support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY pyproject.toml .
COPY configs/ configs/
COPY artifacts/ artifacts/
COPY data/ data/
COPY src/ src/
COPY frontend/ frontend/
COPY treasury_4tier_dataset.csv .

# Install package in editable or standard mode
RUN pip install --no-cache-dir -e .

# Expose standard port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Launch production server with Uvicorn
CMD uvicorn aegisflow.api.main:app --host 0.0.0.0 --port ${PORT}

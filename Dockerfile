# Use official Python 3.11 slim image
FROM python:3.11-slim as builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (build-essential for potential C-compilations if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM python:3.11-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DATABASE_URL="sqlite:////app/data/store_intelligence.db"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY app/ ./app/
COPY pipeline/ ./pipeline/
COPY data/ ./data-seed/
COPY dashboard/ ./dashboard/
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Health check helper
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /docker-entrypoint.sh

# Zero-setup: create data/events dirs, migrate tables, seed analytics (see app/main.py)
ENTRYPOINT ["/docker-entrypoint.sh"]

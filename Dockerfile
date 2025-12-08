# ==========================================
# Multi-Stage Dockerfile for SLD Platform
# Optimized for Azure B1 tier (~1.75GB memory)
# ==========================================

# ==========================================
# Stage 1: Build Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY web_app/core/frontend/package*.json ./

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Copy frontend source
COPY web_app/core/frontend/ ./

# Build React app
RUN npm run build

# ==========================================
# Stage 2: Python Dependencies
# ==========================================
FROM python:3.11-slim AS python-deps

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create virtual environment and install deps
RUN pip install --no-cache-dir virtualenv && \
    virtualenv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install CPU-only PyTorch first (much smaller than GPU version)
RUN pip install --no-cache-dir \
    torch==2.1.1+cpu \
    torchvision==0.16.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 3: Final Production Image
# ==========================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies only (fixed package names for Debian 12)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY web_app/ ./web_app/
COPY text_detection/ ./text_detection/
COPY component_detection/ ./component_detection/
COPY app.py .
COPY requirements.txt .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./web_app/core/frontend/build

# Create necessary directories
RUN mkdir -p /app/web_app/core/backend/static \
    && mkdir -p /app/web_app/core/backend/uploads \
    && mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PORT=8000
ENV TEXT_DETECTION_PATH=/app/text_detection

# Expose port (Azure will override with PORT env var)
EXPOSE 8000

# Health check - use PORT variable for Azure compatibility
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Ensure we're in the right directory
WORKDIR /app

# Start the application using the simplified entry point
# Gunicorn will import from app.py which exports the FastAPI app
CMD ["sh", "-c", "gunicorn --worker-class uvicorn.workers.UvicornWorker \
     --workers 1 --bind 0.0.0.0:${PORT:-8000} \
     --timeout 300 --graceful-timeout 60 \
     --access-logfile - --error-logfile - \
     app:app"]

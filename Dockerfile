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

# Install dependencies
RUN npm ci

# Copy frontend source
COPY web_app/core/frontend/ ./

# Build frontend
RUN npm run build

# ==========================================
# Stage 2: Python Dependencies
# ==========================================
FROM python:3.11-slim AS python-deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir virtualenv && \
    virtualenv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install CPU only dependencies
RUN pip install --no-cache-dir \
    torch==2.1.1+cpu \
    torchvision==0.16.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 3: Final Production Image
# ==========================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime OS libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy backend
COPY web_app/ ./web_app/
COPY component_detection/ ./component_detection/
COPY text_detection/ ./text_detection/
COPY app.py .
COPY requirements.txt .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./web_app/core/frontend/build

# Create directories
RUN mkdir -p /app/web_app/core/backend/static \
    && mkdir -p /app/web_app/core/backend/uploads \
    && mkdir -p /app/component_detection/models \
    && mkdir -p /app/logs

# Ensure model file exists - if not copied from source, download a valid one
RUN if [ ! -f /app/component_detection/models/best.pt ] || [ ! -f /app/web_app/core/backend/component_detection/models/best.pt ]; then \
        echo "Downloading YOLO11x model..."; \
        python -c "from ultralytics import YOLO; model = YOLO('yolov11x.pt'); model.save('/app/component_detection/models/best.pt')"; \
        if [ -d /app/web_app/core/backend/component_detection/models ]; then \
            cp /app/component_detection/models/best.pt /app/web_app/core/backend/component_detection/models/best.pt; \
        fi; \
    fi

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV TEXT_DETECTION_PATH=/app/text_detection
ENV PORT=8000

# Expose
EXPOSE 8000

# Note: Azure Container Apps has built-in health checking
# No HEALTHCHECK needed in Docker

# START APPLICATION  — (Azure Compatible)
# Use exec to ensure gunicorn receives signals properly
CMD exec gunicorn app:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 1 \
  --bind 0.0.0.0:$PORT \
  --timeout 600 \
  --graceful-timeout 60 \
  --access-logfile - \
  --error-logfile -

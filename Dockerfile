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
    && mkdir -p /app/web_app/core/backend/component_detection/models \
    && mkdir -p /app/logs

# Validate that a valid trained model is available (must come from Git LFS)
# This will FAIL the build if the model is missing or corrupted
RUN python -c " \
import os; \
import sys; \
import shutil; \
from pathlib import Path; \
\
model_paths = [ \
    '/app/web_app/core/backend/component_detection/models/best.pt', \
    '/app/component_detection/models/best.pt' \
]; \
\
print('Checking for valid trained model...'); \
valid_model_path = None; \
\
for path in model_paths: \
    if os.path.exists(path): \
        size = os.path.getsize(path); \
        print(f'Found model at {path} ({size} bytes)'); \
        if size > 100000000: \
            try: \
                with open(path, 'rb') as f: \
                    header = f.read(4); \
                    if header == b'PK\x03\x04': \
                        print(f'Valid PyTorch model verified at {path}'); \
                        valid_model_path = path; \
                        break; \
                    else: \
                        print(f'File is not a valid PyTorch model (wrong header)'); \
            except Exception as e: \
                print(f'Error reading model: {e}'); \
        else: \
            print(f'File too small ({size} bytes) - likely a Git LFS pointer file'); \
            print('This means git lfs pull was not run before the Docker build'); \
    else: \
        print(f'Model not found at {path}'); \
\
if valid_model_path is None: \
    print(''); \
    print('ERROR: No valid trained model found!'); \
    print('The custom 5-class electrical component model is REQUIRED.'); \
    print(''); \
    print('To fix this issue:'); \
    print('  1. Install Git LFS: git lfs install'); \
    print('  2. Pull LFS files: git lfs pull'); \
    print('  3. Rebuild the Docker image'); \
    print(''); \
    sys.exit(1); \
\
print('Copying model to all expected locations...'); \
for dest in model_paths: \
    if dest != valid_model_path: \
        if not os.path.exists(dest) or os.path.getsize(dest) < 100000000: \
            Path(dest).parent.mkdir(parents=True, exist_ok=True); \
            shutil.copy(valid_model_path, dest); \
            print(f'Copied model to {dest}'); \
\
print('Model validation complete!'); \
"

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

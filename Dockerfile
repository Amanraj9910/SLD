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

# Ensure a valid model is available - download if missing or corrupted
RUN python -c " \
    import os; \
    import urllib.request; \
    from pathlib import Path; \
    \
    model_paths = [ \
        '/app/component_detection/models/best.pt', \
        '/app/web_app/core/backend/component_detection/models/best.pt' \
    ]; \
    \
    # Check if any model is valid \
    valid_model_exists = False; \
    for path in model_paths: \
        if os.path.exists(path) and os.path.getsize(path) > 100000000: \
            try: \
                with open(path, 'rb') as f: \
                    header = f.read(4); \
                    if header == b'PK\x03\x04': \
                        print(f'✅ Valid model found at {path}'); \
                        valid_model_exists = True; \
                        break; \
            except: \
                pass; \
    \
    # If no valid model, download one \
    if not valid_model_exists: \
        print('📥 No valid model found, downloading YOLO11x...'); \
        url = 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov11x.pt'; \
        Path('/app/component_detection/models').mkdir(parents=True, exist_ok=True); \
        urllib.request.urlretrieve(url, '/app/component_detection/models/best.pt'); \
        Path('/app/web_app/core/backend/component_detection/models').mkdir(parents=True, exist_ok=True); \
        import shutil; \
        shutil.copy('/app/component_detection/models/best.pt', '/app/web_app/core/backend/component_detection/models/best.pt'); \
        print('✅ Model downloaded successfully'); \
    " || echo "⚠️ Model download attempt finished (will fallback to runtime download if needed)"

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

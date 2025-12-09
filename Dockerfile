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

# Build argument for model download URL (passed from CI/CD)
ARG MODEL_DOWNLOAD_URL=https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt
ENV MODEL_DOWNLOAD_URL=${MODEL_DOWNLOAD_URL}

# Model validation and download script
# Checks for valid model, downloads from external URL if needed
COPY <<'EOF' /app/validate_model.py
import os
import sys
import shutil
import urllib.request
from pathlib import Path

MODEL_PATHS = [
    '/app/web_app/core/backend/component_detection/models/best.pt',
    '/app/component_detection/models/best.pt'
]

# URL to download the trained model if not available locally
# UPDATE THIS URL to point to your hosted model file
MODEL_DOWNLOAD_URL = os.environ.get(
    'MODEL_DOWNLOAD_URL',
    'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt'
)

def is_valid_pytorch_model(path):
    """Check if file is a valid PyTorch model (not a Git LFS pointer)"""
    if not os.path.exists(path):
        return False
    
    size = os.path.getsize(path)
    if size < 1000000:  # Less than 1MB is likely a pointer
        print(f'  File too small ({size} bytes) - likely Git LFS pointer')
        return False
    
    try:
        with open(path, 'rb') as f:
            header = f.read(4)
            if header == b'PK\x03\x04':
                print(f'  Valid PyTorch model ({size:,} bytes)')
                return True
            else:
                print(f'  Invalid header: {header}')
                return False
    except Exception as e:
        print(f'  Error reading file: {e}')
        return False

def download_model(url, dest_path):
    """Download model from URL"""
    print(f'Downloading model from {url}...')
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        size = os.path.getsize(dest_path)
        print(f'Downloaded {size:,} bytes to {dest_path}')
        return True
    except Exception as e:
        print(f'Download failed: {e}')
        return False

def main():
    print('=' * 60)
    print('Model Validation and Setup')
    print('=' * 60)
    
    # Check for existing valid model
    valid_model_path = None
    for path in MODEL_PATHS:
        print(f'\nChecking {path}...')
        if is_valid_pytorch_model(path):
            valid_model_path = path
            print(f'  VALID')
            break
        else:
            print(f'  NOT VALID')
    
    # If no valid model found, try to download
    if valid_model_path is None:
        print('\nNo valid model found locally.')
        print(f'Attempting download from: {MODEL_DOWNLOAD_URL}')
        
        download_path = MODEL_PATHS[0]
        if download_model(MODEL_DOWNLOAD_URL, download_path):
            if is_valid_pytorch_model(download_path):
                valid_model_path = download_path
                print('Model downloaded and validated successfully!')
            else:
                print('ERROR: Downloaded file is not a valid model')
                sys.exit(1)
        else:
            print('ERROR: Failed to download model')
            print('\nTo fix this:')
            print('  1. Upload your trained model to Azure Blob Storage or GitHub Releases')
            print('  2. Set MODEL_DOWNLOAD_URL environment variable to the download URL')
            print('  3. Rebuild the Docker image')
            sys.exit(1)
    
    # Copy model to all expected locations
    print('\nSyncing model to all locations...')
    for dest in MODEL_PATHS:
        if dest != valid_model_path:
            if not os.path.exists(dest) or not is_valid_pytorch_model(dest):
                Path(dest).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(valid_model_path, dest)
                print(f'  Copied to {dest}')
    
    print('\n' + '=' * 60)
    print('Model setup complete!')
    print('=' * 60)

if __name__ == '__main__':
    main()
EOF

# Run model validation
RUN python /app/validate_model.py

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
CMD ["gunicorn", "app:app", \
  "--worker-class", "uvicorn.workers.UvicornWorker", \
  "--workers", "1", \
  "--bind", "0.0.0.0:8000", \
  "--timeout", "600", \
  "--graceful-timeout", "60", \
  "--access-logfile", "-", \
  "--error-logfile", "-"]

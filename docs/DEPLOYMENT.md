# SLD Processing Platform - Deployment Guide

Complete deployment guide for the SLD Processing Platform with component detection, text extraction, and annotation capabilities.

## 🚀 Quick Deployment

### Prerequisites

- Python 3.8+
- Node.js 16+
- Azure Document Intelligence account
- Git

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd SLD

# Copy environment template
cp .env.template .env
```

### 2. Configure Azure Credentials

Edit the `.env` file with your Azure Document Intelligence credentials:

```env
# Azure Document Intelligence Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://sld.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=8n1hs7EHtYI7nKxRvktl9VhoRg3GnKQYYcd1xqMXne2t8avsu9pgJQQJ99BEACYeBjFXJ3w3AAALACOGm7Iv

# Azure AI Foundry Configuration (if needed)
AZURE_AI_FOUNDRY_ENDPOINT=https://ai-diagramanalysis709756132870.openai.azure.com/
AZURE_AI_FOUNDRY_KEY=9oaTfptIYncr9vUe1JegGBXBXVF7VCVXi4pntMJGuUj2C84GxJexJQQJ99BEACYeBjFXJ3w3AAAAACOGvCqX
```

### 3. Backend Deployment

```bash
# Install Python dependencies
pip install -r requirements.txt

# Navigate to backend directory
cd web_app/backend

# Start the FastAPI server
python main.py
```

The backend will be available at `http://localhost:8000`

### 4. Frontend Deployment

```bash
# Navigate to frontend directory
cd web_app/frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

## 🐳 Docker Deployment

### Backend Docker

```bash
# Build backend image
cd web_app/backend
docker build -t sld-backend .

# Run backend container
docker run -d \
  --name sld-backend \
  -p 8000:8000 \
  --env-file ../../.env \
  sld-backend
```

### Frontend Docker

```bash
# Build frontend image
cd web_app/frontend
docker build -t sld-frontend .

# Run frontend container
docker run -d \
  --name sld-frontend \
  -p 3000:3000 \
  sld-frontend
```

## ☁️ Cloud Deployment

### Azure App Service

1. **Create App Service**:
   ```bash
   az webapp create \
     --resource-group myResourceGroup \
     --plan myAppServicePlan \
     --name sld-processing-app \
     --runtime "PYTHON|3.9"
   ```

2. **Deploy Backend**:
   ```bash
   cd web_app/backend
   zip -r app.zip .
   az webapp deployment source config-zip \
     --resource-group myResourceGroup \
     --name sld-processing-app \
     --src app.zip
   ```

3. **Configure Environment Variables**:
   ```bash
   az webapp config appsettings set \
     --resource-group myResourceGroup \
     --name sld-processing-app \
     --settings AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="your-endpoint" \
                AZURE_DOCUMENT_INTELLIGENCE_KEY="your-key"
   ```

### AWS EC2

1. **Launch EC2 Instance**:
   - Choose Ubuntu 20.04 LTS
   - Configure security groups (ports 22, 80, 443, 8000, 3000)

2. **Setup Environment**:
   ```bash
   # Connect to instance
   ssh -i your-key.pem ubuntu@your-instance-ip

   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python and Node.js
   sudo apt install python3 python3-pip nodejs npm -y

   # Clone repository
   git clone <repository-url>
   cd SLD
   ```

3. **Deploy Application**:
   ```bash
   # Install dependencies
   pip3 install -r requirements.txt
   cd web_app/frontend && npm install

   # Start services with PM2
   sudo npm install -g pm2
   pm2 start web_app/backend/main.py --name sld-backend
   pm2 start "npm start" --name sld-frontend
   pm2 startup
   pm2 save
   ```

## 🔧 Production Configuration

### Environment Variables

```env
# Production settings
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-production-secret-key
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance
API_WORKERS=4
WORKER_TIMEOUT=300

# File handling
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_FOLDER=/app/uploads

# Database (if using)
DATABASE_URL=postgresql://user:password@localhost/sld_db
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }

    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring and Logging

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Component detection health
curl http://localhost:8000/api/v1/components/health

# Text detection health
curl http://localhost:8000/api/v1/text/health
```

### Log Configuration

```python
# In production, configure structured logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/sld/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"],
    },
}
```

## 🔒 Security Considerations

### API Security

1. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/api/v1/components/predict")
   @limiter.limit("10/minute")
   async def predict_components():
       pass
   ```

2. **Input Validation**:
   - File type validation
   - File size limits
   - Content scanning

3. **Authentication** (if needed):
   ```python
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   
   @app.post("/api/v1/protected")
   async def protected_endpoint(token: str = Depends(security)):
       pass
   ```

### Infrastructure Security

1. **Firewall Configuration**:
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   ```

2. **Regular Updates**:
   ```bash
   # Automated security updates
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```

## 📈 Performance Optimization

### Backend Optimization

1. **Async Processing**:
   ```python
   import asyncio
   from concurrent.futures import ThreadPoolExecutor
   
   executor = ThreadPoolExecutor(max_workers=4)
   
   async def process_image_async(image_path):
       loop = asyncio.get_event_loop()
       return await loop.run_in_executor(executor, process_image, image_path)
   ```

2. **Caching**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def load_model():
       return YOLOModel("model.pt")
   ```

### Frontend Optimization

1. **Build Optimization**:
   ```bash
   # Production build
   npm run build
   
   # Serve with static server
   npm install -g serve
   serve -s build -l 3000
   ```

2. **CDN Configuration**:
   ```javascript
   // webpack.config.js
   module.exports = {
     output: {
       publicPath: 'https://cdn.yourdomain.com/',
     },
   };
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Azure Connection Failed**:
   ```bash
   # Test Azure credentials
   python -c "
   from text_detection.config.azure_config import test_azure_connection
   print('Connection:', test_azure_connection())
   "
   ```

2. **YOLO Model Not Found**:
   ```bash
   # Download default model
   mkdir -p component_detection/models
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt \
        -O component_detection/models/yolov8n.pt
   ```

3. **Port Already in Use**:
   ```bash
   # Find and kill process
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

### Log Analysis

```bash
# View application logs
tail -f /var/log/sld/app.log

# Check system resources
htop
df -h
free -h

# Monitor API requests
tail -f /var/log/nginx/access.log | grep "/api/"
```

## 📋 Deployment Checklist

- [ ] Azure Document Intelligence credentials configured
- [ ] Environment variables set for production
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Monitoring and logging setup
- [ ] Backup strategy implemented
- [ ] Health checks configured
- [ ] Performance optimization applied
- [ ] Security measures in place
- [ ] Documentation updated

## 🆘 Support

For deployment issues:
1. Check the logs for error messages
2. Verify environment configuration
3. Test individual components
4. Review the troubleshooting section
5. Create an issue with deployment details

---

**Deployment completed successfully! 🎉**

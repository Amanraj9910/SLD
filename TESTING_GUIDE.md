# Quick Testing Guide

## ⚡ Quick Local Test (Health Check)

```powershell
# 1. Start the application
cd C:\Users\admin\Downloads\Single-Line-Diagram\SLD
python app.py

# 2. In another terminal, test health check
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy", ...}`

---

## 🐳 Quick Docker Test

```bash
# Build
docker build -t sld-app:latest .

# Run
docker run -p 8000:8000 sld-app:latest

# Test (in another terminal)
curl http://localhost:8000/health
curl http://localhost:8000/api/test
```

---

## ☁️ Azure Deployment (Summary)

```bash
# 1. Build and push
docker build -t sld-app:latest .
docker tag sld-app:latest <acr-name>.azurecr.io/sld-app:latest
az acr login --name <acr-name>
docker push <acr-name>.azurecr.io/sld-app:latest

# 2. Configure App Service (Portal or CLI)
# - Set Container Image: <acr-name>.azurecr.io/sld-app:latest
# - Set Environment Variables: PORT=8000, PYTHONPATH=/app

# 3. Test
curl https://<app-name>.azurewebsites.net/health
```

---

## ✅ Success Criteria

| Test | Expected Result |
|------|----------------|
| Local health check | HTTP 200, status: "healthy" |
| Docker health check | HTTP 200, status: "healthy" |
| Azure health check | HTTP 200, status: "healthy" |
| API test endpoint | HTTP 200, message: "API is working!" |

---

## 🔴 If Health Check Fails

1. **Check logs** for errors
2. **Verify** PYTHONPATH=/app is set
3. **Ensure** app.py can import from web_app.core.backend.main
4. **Confirm** text_detection errors are info-level (not crashing)

---

## 📁 Files Changed

- ✅ `app.py` - Simplified entry point
- ✅ `web_app/core/backend/main.py` - Graceful health check
- ✅ `web_app/core/backend/init_text_detection.py` - Soft dependency
- ✅ `Dockerfile` - Updated CMD to app:app
- ✅ `docker-compose.yml` - Added env vars
- ❌ `startup` - Deleted (conflicting)

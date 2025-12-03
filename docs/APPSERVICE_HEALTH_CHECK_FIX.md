# Fix for App Service Health Check Issue

## Problem
Your SLD application deployed on Azure App Service was running as a **static Node.js site** instead of the **Python FastAPI backend**. This is why the health check was failing - it couldn't connect to the `/health` endpoint.

## Root Cause
App Service detected the `package.json` file and assumed it was a Node.js application, so it started with PM2 serving static files on port 8080 instead of running your Python FastAPI backend on port 8000.

## Solution Overview
Configure App Service to run the Python FastAPI backend instead of the Node.js frontend.

## Implementation Steps

### 1. Update App Service Configuration (Azure Portal)

1. Go to your **App Service** → **Configuration** → **General Settings**
2. Set the **Startup Command** to:
   ```
   cd /home/site/wwwroot && bash startup.sh
   ```
3. Make sure **Runtime** is set to: **Python 3.11** (or your preferred Python version)

### 2. Alternative: Using web.config (for Windows App Service)

If using Windows App Service, create a `web.config` file:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" scriptProcessor="D:\Python311\python.exe|D:\Python311\wfastcgi.py" resourceType="Unspecified" />
    </handlers>
  </system.webServer>
  
  <appSettings>
    <add key="WSGI_HANDLER" value="main.app" />
    <add key="PYTHONPATH" value="D:\home\site\wwwroot\web_app\core\backend" />
  </appSettings>
</configuration>
```

### 3. Application Startup Flow

After these changes, App Service will:

1. ✅ Run Python virtual environment setup
2. ✅ Install dependencies from `requirements.txt` files
3. ✅ Start FastAPI backend on port 8000 (or PORT env var)
4. ✅ Expose `/health` endpoint
5. ✅ Serve all API endpoints on `/api/v1/`

### 4. Files Created/Modified

The following files have been created to support proper deployment:

- **`startup.sh`** - Linux/Mac startup script (primary)
- **`startup.ps1`** - Windows PowerShell startup script
- **`startup`** - Simple startup script for App Service
- **`.deployment`** - Deployment configuration file

### 5. Testing the Health Check

Once deployed, test the endpoints:

```bash
# Health check endpoint
curl https://your-app-service.azurewebsites.net/health

# API test endpoint
curl https://your-app-service.azurewebsites.net/api/test

# API documentation
https://your-app-service.azurewebsites.net/docs
```

Expected health check response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "backend": "running",
    "component_detection": "available",
    "text_detection": "available",
    "annotation": "available"
  }
}
```

## Port Configuration

- **FastAPI Backend**: Port 8000 (or `$PORT` environment variable)
- **App Service**: Automatically maps internal port to HTTPS on `azurewebsites.net`

## Environment Variables to Set in App Service

In **Configuration** → **Application Settings**, add:

| Name | Value |
|------|-------|
| `PORT` | `8000` |
| `PYTHONPATH` | `/home/site/wwwroot` |
| `WEBSITES_PORT` | `8000` |

## Logs to Monitor

In App Service → **Log stream**, you should see:

```
Installing Python dependencies...
Starting SLD Backend on port 8000...
Uvicorn running on http://0.0.0.0:8000
```

If you see "PM2 launched" messages instead, the startup command is not being used correctly.

## Troubleshooting

### Issue: Still seeing PM2 messages
**Solution**: 
1. Delete `package.json` from root if not needed, OR
2. Rename it to `package.json.bak`
3. Verify Runtime is set to Python, not Node.js
4. Restart the App Service

### Issue: Health endpoint returns 502/503
**Solution**:
1. Check Application Insights/Log Stream for errors
2. Verify all dependencies are installed: `pip list`
3. Ensure port 8000 is not blocked
4. Check if services like Azure Document Intelligence are accessible

### Issue: Timeout errors
**Solution**:
1. Increase worker timeout in startup script
2. Use App Service Plan with more CPU/RAM
3. Reduce number of workers: `--workers 1`

## Next Steps

1. Commit these changes to your repository
2. Redeploy to App Service
3. Monitor the Application Insights logs
4. Update your frontend to use the correct backend URL
5. Test all API endpoints

## References

- [Deploying Python Apps to Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [App Service Startup Commands](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python#startup-command)

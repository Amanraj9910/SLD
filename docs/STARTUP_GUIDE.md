# SLD Platform - Unified Startup Guide

## Overview

The SLD (Single Line Diagram) Processing Platform has been streamlined with a unified startup process. This guide explains how to use the new simplified startup system.

## Quick Start

### 1. One-Click Startup (Recommended)
```bash
start_sld_unified.bat
```

This unified script will:
- ✅ Check system requirements (Python, Node.js)
- ✅ Verify and install dependencies automatically
- ✅ Configure environment variables
- ✅ Create necessary directories
- ✅ Start backend and frontend servers
- ✅ Open the application in your browser

### 2. Verify Setup (Optional)
Before running the platform, you can verify your setup:
```bash
verify_setup.bat
```

This will check all requirements without starting the servers.

### 3. Test Azure Connection (Optional)
To test Azure Document Intelligence integration:
```bash
python test_azure_connection.py
```

## System Requirements

### Required Software
- **Python 3.8+** - Download from [python.org](https://python.org)
- **Node.js 16+** - Download from [nodejs.org](https://nodejs.org)

⚠️ **Important**: During installation, make sure to check "Add to PATH" for both Python and Node.js.

### Azure Services
The platform is pre-configured with Azure Document Intelligence credentials:
- **Endpoint**: `https://sld.cognitiveservices.azure.com/`
- **API Key**: Pre-configured in environment files

## Directory Structure

```
SLD/
├── start_sld_unified.bat          # 🚀 Main startup script (NEW)
├── verify_setup.bat               # 🔍 Setup verification (NEW)
├── test_azure_connection.py       # 🧪 Azure connection test (NEW)
├── .env                          # 🔧 Environment configuration
├── web_app/
│   ├── core/
│   │   └── backend/              # 🐍 Python FastAPI backend
│   │       └── main_fixed.py     # Backend entry point
│   └── config/                   # 🟢 React frontend configuration
│       └── package.json          # Frontend dependencies
├── text_detection/
│   └── config/
│       └── azure_config.py       # 🔧 Azure configuration (FIXED)
└── scripts/                      # 📁 Legacy scripts (see below)
```

## Services and Ports

When running, the platform uses these services:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React web interface |
| Backend | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Health Check | http://localhost:8000/health | Service health status |

## Features

- 🔍 **Component Detection**: AI-powered detection of electrical components (Circuit Breakers, HRC Fuses, Isolators)
- 📝 **Text Extraction**: Azure Document Intelligence for text recognition
- 🎨 **Interactive Visualization**: Dynamic HTML visualizations of detected components
- ✏️ **Manual Annotation**: Tools for manual component annotation and training data creation
- 📊 **Batch Processing**: Process multiple diagrams simultaneously

## Troubleshooting

### Common Issues

1. **Python not found**
   - Install Python 3.8+ from python.org
   - Make sure "Add Python to PATH" is checked during installation
   - Restart your command prompt after installation

2. **Node.js not found**
   - Install Node.js 16+ from nodejs.org
   - Make sure "Add to PATH" is checked during installation
   - Restart your command prompt after installation

3. **Port already in use**
   - Close any existing instances of the platform
   - Run `stop_sld_platform.bat` to clean up processes
   - Or manually kill processes using ports 3000 and 8000

4. **Dependencies missing**
   - The unified script installs dependencies automatically
   - If issues persist, manually install:
     ```bash
     # Backend dependencies
     cd web_app/core/backend
     pip install fastapi uvicorn pydantic-settings python-multipart python-dotenv
     
     # Frontend dependencies
     cd web_app/config
     npm install
     ```

5. **Azure connection issues**
   - Run `python test_azure_connection.py` to diagnose
   - Check that .env file contains correct Azure credentials
   - Verify internet connection

### Getting Help

1. **Check logs**: Look in the `logs/` directory for error messages
2. **Run diagnostics**: Use `verify_setup.bat` to check configuration
3. **Test Azure**: Use `test_azure_connection.py` to verify Azure integration
4. **Manual startup**: Start backend and frontend separately for debugging

## Legacy Scripts (Deprecated)

The following scripts are now **deprecated** in favor of `start_sld_unified.bat`:

| Script | Status | Replacement |
|--------|--------|-------------|
| `scripts/quick_start.bat` | ⚠️ Deprecated | `start_sld_unified.bat` |
| `scripts/start_sld_platform.bat` | ⚠️ Deprecated | `start_sld_unified.bat` |
| `scripts/start_sld_advanced.bat` | ⚠️ Deprecated | `start_sld_unified.bat` |
| `scripts/setup_and_start.bat` | ⚠️ Deprecated | `start_sld_unified.bat` |

**Keep for now**:
- `scripts/stop_sld_platform.bat` - Still useful for stopping services
- `scripts/fix_all_issues.bat` - Useful for troubleshooting
- `scripts/install.bat` - Useful for manual installation

## Configuration

### Environment Variables (.env)

The platform uses these key environment variables:

```bash
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://sld.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=8n1hs7EHtYI7nKxRvktl9VhoRg3GnKQYYcd1xqMXne2t8avsu9pgJQQJ99BEACYeBjFXJ3w3AAAAACOGm7Iv

# Azure AI Foundry (Alternative)
AZURE_AI_FOUNDRY_ENDPOINT=https://ai-diagramanalysis709756132870.openai.azure.com/
AZURE_AI_FOUNDRY_KEY=9oaTfptIYncr9vUe1JegGBXBXVF7VCVXi4pntMJGuUj2C84GxJexJQQJ99BEACYeBjFXJ3w3AAAAACOGvCqX

# Application Settings
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# YOLO Model Settings
YOLO_MODEL_PATH=component_detection/models/best.pt
YOLO_CONFIDENCE_THRESHOLD=0.01
YOLO_IOU_THRESHOLD=0.3
```

## Next Steps

1. **Run the platform**: Execute `start_sld_unified.bat`
2. **Upload an SLD image**: Use the web interface to test component detection
3. **Explore features**: Try text extraction, interactive visualization, and annotation tools
4. **Check documentation**: Visit http://localhost:8000/docs for API documentation

---

**Created**: 2025-01-21  
**Version**: 1.0  
**Status**: ✅ Ready for production use

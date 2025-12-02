# 📦 Complete Dependency Installation Guide

## Current System Status
✅ **Node.js**: v22.17.1 (Installed)  
❌ **Python**: Not installed (Required)

## Step 1: Install Python

### Option A: Download from Python.org (Recommended)
1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 (latest stable)
3. **IMPORTANT**: During installation, check "Add Python to PATH"
4. Install with default settings

### Option B: Microsoft Store (Alternative)
1. Open Microsoft Store
2. Search for "Python 3.11" or "Python 3.12"
3. Install the official Python package

### Option C: Using Chocolatey (If you have it)
```powershell
choco install python
```

### Option D: Using winget (Windows Package Manager)
```powershell
winget install Python.Python.3.11
```

## Step 2: Verify Python Installation

After installing Python, open a new PowerShell/Command Prompt and run:
```powershell
python --version
# or
py --version
```

You should see something like: `Python 3.11.x` or `Python 3.12.x`

## Step 3: Install Python Dependencies

Once Python is installed, navigate to the SLD directory and run:

### Option A: Automated Installation
```powershell
# Run the installation script
python install.py
```

### Option B: Manual Installation
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir uploads, logs, results, annotation_projects, component_detection\models -Force
```

## Step 4: Install Frontend Dependencies

```powershell
# Navigate to frontend directory
cd web_app\frontend

# Install Node.js packages
npm install

# Go back to root directory
cd ..\..
```

## Step 5: Download YOLO Model (Optional)

```powershell
# Create models directory
mkdir component_detection\models -Force

# Download YOLO model (you can do this manually)
# Go to: https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt
# Save it to: component_detection\models\yolov8n.pt
```

## Complete Installation Commands

Once Python is installed, run these commands in order:

```powershell
# 1. Install Python dependencies
python -m pip install --upgrade pip
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-multipart==0.0.6
pip install python-dotenv==1.0.0
pip install pydantic==2.5.0
pip install azure-ai-documentintelligence==1.0.0b1
pip install azure-core==1.29.5
pip install ultralytics==8.0.206
pip install opencv-python==4.8.1.78
pip install torch==2.1.1
pip install torchvision==0.16.1
pip install numpy==1.24.4
pip install Pillow==10.1.0
pip install pandas==2.1.3
pip install httpx==0.25.2
pip install requests==2.31.0
pip install psutil==5.9.6

# 2. Create directories
mkdir uploads -Force
mkdir logs -Force
mkdir results -Force
mkdir annotation_projects -Force
mkdir component_detection\models -Force

# 3. Install frontend dependencies
cd web_app\frontend
npm install
cd ..\..
```

## Alternative: Install from requirements.txt

```powershell
# Install all at once from requirements file
pip install -r requirements.txt
```

## Verify Installation

### Test Python packages:
```powershell
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import ultralytics; print('YOLO: OK')"
python -c "import cv2; print('OpenCV: OK')"
python -c "import azure.ai.documentintelligence; print('Azure: OK')"
```

### Test Node.js packages:
```powershell
cd web_app\frontend
npm list react
cd ..\..
```

## Start the Application

### Terminal 1 - Backend:
```powershell
cd web_app\backend
python main.py
```

### Terminal 2 - Frontend:
```powershell
cd web_app\frontend
npm start
```

## Troubleshooting

### Python Installation Issues:
- **"python not recognized"**: Restart your terminal after installing Python
- **PATH issues**: Reinstall Python and check "Add to PATH" option
- **Permission errors**: Run PowerShell as Administrator

### Package Installation Issues:
- **pip not found**: `python -m ensurepip --upgrade`
- **SSL errors**: `pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org <package>`
- **Version conflicts**: Use virtual environment: `python -m venv venv && venv\Scripts\activate`

### Frontend Issues:
- **npm not found**: Reinstall Node.js
- **Permission errors**: Run as Administrator
- **Network issues**: `npm config set registry https://registry.npmjs.org/`

## System Requirements

### Minimum:
- Windows 10/11
- Python 3.8+
- Node.js 16+
- 4GB RAM
- 2GB free disk space

### Recommended:
- Windows 11
- Python 3.11+
- Node.js 18+
- 8GB RAM
- 5GB free disk space
- GPU (for faster YOLO inference)

## Next Steps

After successful installation:

1. **Start Backend**: `cd web_app\backend && python main.py`
2. **Start Frontend**: `cd web_app\frontend && npm start`
3. **Open Browser**: Navigate to `http://localhost:3000`
4. **Test Upload**: Try uploading an SLD diagram
5. **Check API**: Visit `http://localhost:8000/docs`

---

**Need Help?** Check the QUICK_START.md file for additional guidance!

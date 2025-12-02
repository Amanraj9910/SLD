# 🚀 Quick Start Guide - SLD Processing Platform

## Installation Options

### Option 1: Automated Installation (Recommended)

#### For Windows:
```cmd
# Double-click install.bat or run in Command Prompt:
install.bat
```

#### For Linux/Mac:
```bash
# Make executable and run:
chmod +x install.sh
./install.sh
```

#### For Python-only:
```bash
# Run the Python installation script:
python install.py
```

### Option 2: Manual Installation

#### Prerequisites
- Python 3.8+ 
- Node.js 16+
- Git

#### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Step 2: Install Frontend Dependencies
```bash
cd web_app/frontend
npm install
cd ../..
```

#### Step 3: Setup Environment
```bash
# Copy environment template
cp .env.template .env
# Edit .env with your Azure credentials (already configured)
```

## Running the Application

### Start Backend (Terminal 1)
```bash
cd web_app/backend
python main.py
```
Backend will be available at: `http://localhost:8000`

### Start Frontend (Terminal 2)
```bash
cd web_app/frontend
npm start
```
Frontend will be available at: `http://localhost:3000`

## Verify Installation

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### Check API Documentation
Open: `http://localhost:8000/docs`

### Test Azure Connection
```bash
curl -X POST http://localhost:8000/api/v1/text/test-connection
```

## First Steps

1. **Open the Application**: Navigate to `http://localhost:3000`
2. **Try Component Detection**: Upload an SLD image
3. **Test Text Extraction**: Upload a PDF or image with text
4. **Use Annotation Tool**: Create manual annotations

## Troubleshooting

### Common Issues

**Python not found:**
```bash
# Try python3 instead of python
python3 install.py
```

**Permission denied (Linux/Mac):**
```bash
chmod +x install.sh
sudo ./install.sh
```

**Port already in use:**
```bash
# Kill process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Azure connection failed:**
- Check your `.env` file has correct Azure credentials
- Verify internet connection
- Test credentials in Azure portal

### Dependencies Issues

**YOLO model not found:**
```bash
mkdir -p component_detection/models
# Download manually from: https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt
```

**OpenCV issues:**
```bash
pip install opencv-python-headless
```

**Azure SDK issues:**
```bash
pip install --upgrade azure-ai-documentintelligence
```

## What's Included

✅ **Component Detection**: AI-powered electrical component recognition  
✅ **Text Extraction**: Azure OCR with precise bounding boxes  
✅ **Annotation Tool**: Manual labeling interface  
✅ **Web Application**: Modern React frontend + FastAPI backend  
✅ **API Documentation**: Interactive Swagger/OpenAPI docs  
✅ **Azure Integration**: Pre-configured with your credentials  

## Next Steps

1. **Upload Test Images**: Try the sample SLD diagrams
2. **Explore API**: Check `/docs` for API documentation
3. **Create Annotations**: Use the annotation tool for manual labeling
4. **Export Results**: Download results in various formats

## Support

- **Documentation**: Check individual module README files
- **API Reference**: Visit `/docs` when backend is running
- **Health Check**: Visit `/health` for system status

---

**🎉 You're ready to start processing SLD diagrams!**

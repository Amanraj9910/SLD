# Single Line Diagram (SLD) Processing Application

A comprehensive, modular web application for Single Line Diagram (SLD) processing with component detection, text extraction, and manual annotation capabilities.

## 🏗️ Project Structure

```
SLD/
├── component_detection/    # YOLO-based component detection
├── text_detection/        # Azure Document Intelligence OCR
├── annotation_tool/       # Manual labeling interface
├── web_app/              # Frontend and backend integration
├── requirements.txt      # Python dependencies
├── package.json         # Node.js dependencies
├── docker-compose.yml   # Docker configuration
└── README.md           # This file
```

## 🚀 Features

### Component Detection Module
- YOLO-based electrical component detection
- Support for Circuit Breakers, HRC Fuses, Isolators, and more
- Configurable confidence thresholds
- JSON output with bounding boxes and classifications

### Text Detection Module
- Azure Document Intelligence OCR integration
- Text extraction with precise bounding boxes
- Support for JPG, PNG, and PDF files
- Structured JSON output with polygon coordinates

### Annotation Tool Module
- Canvas-based bounding box drawing
- Component category dropdown selection
- YOLO format annotation export
- Data validation and error handling

### Web Application
- **Backend**: Flask/FastAPI with RESTful APIs
- **Frontend**: React.js/Vue.js with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Features**: File upload, real-time processing, interactive visualization

## 🎨 Design Specifications

### Color Scheme
- Background: `#FFFFFF` (white)
- Primary buttons: `#E21C15` (red)
- Text: `#000000` (black)
- Font: Inter or Poppins

### UI Components
- Fixed navigation bar with Hosho logo
- Drag-and-drop file upload interface
- Split-panel results display
- Interactive annotation canvas

## 📋 Requirements

### System Requirements
- Python 3.8+
- Node.js 16+
- Azure Document Intelligence subscription
- GPU recommended for YOLO inference

### Dependencies
- **Backend**: FastAPI, OpenCV, Ultralytics YOLO, Azure AI Document Intelligence
- **Frontend**: React.js/Vue.js, TypeScript, Tailwind CSS
- **ML**: PyTorch, OpenCV, NumPy

## 🛠️ Installation

### 1. Clone and Setup
```bash
cd SLD
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd web_app/frontend
npm install
```

### 3. Environment Configuration
```bash
cp .env.template .env
# Edit .env with your Azure credentials
```

### 4. Docker Setup (Optional)
```bash
docker-compose up --build
```

## 🚀 Quick Start

### 1. Start Backend
```bash
cd web_app/backend
python main.py
```

### 2. Start Frontend
```bash
cd web_app/frontend
npm run dev
```

### 3. Access Application
Open http://localhost:3000 in your browser

## 📖 API Documentation

### Component Detection
```
POST /api/predict-components
Content-Type: multipart/form-data
Body: image file

Response: {
  "components": [
    {
      "class": "CIRCUIT_BREAKER",
      "confidence": 0.95,
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

### Text Detection
```
POST /api/predict-text
Content-Type: multipart/form-data
Body: image/PDF file

Response: {
  "text_elements": [
    {
      "text": "BOOSTER PUMP ROOM",
      "polygon": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    }
  ]
}
```

### Annotation Tool
```
POST /api/annotate
Content-Type: application/json
Body: {
  "annotations": [
    {
      "class_id": 0,
      "bbox": [x_center, y_center, width, height]
    }
  ]
}
```

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/
```

### Run Frontend Tests
```bash
cd web_app/frontend
npm test
```

## 📦 Deployment

### Production Build
```bash
# Backend
cd web_app/backend
gunicorn main:app

# Frontend
cd web_app/frontend
npm run build
```

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in each module
- Review the API documentation

## 🔄 Version History

- **v1.0.0** - Initial release with all core modules
- **v0.9.0** - Beta release with basic functionality
- **v0.1.0** - Alpha release with component detection only

#!/usr/bin/env python3
"""
Simple Flask API server for real-time SLD text detection with Azure Document Intelligence.
This server provides endpoints for the real-time text detector HTML interface.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, using system environment variables only")

# Add the text_detection module to the path
sys.path.append(str(Path(__file__).parent / "text_detection"))

try:
    from text_detection.document_ocr import extract_text_from_document
except ImportError as e:
    print(f"Error: Failed to import text detection module: {e}")
    print("Make sure the azure-ai-documentintelligence package is installed:")
    print("pip install azure-ai-documentintelligence")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main page"""
    return jsonify({
        "message": "SLD Text Detection API Server",
        "version": "1.0.0",
        "endpoints": {
            "/detect": "POST - Upload image for text detection",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "SLD Text Detection API",
        "azure_configured": bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'))
    })

@app.route('/detect', methods=['POST'])
def detect_text():
    """
    Detect text in uploaded image using Azure Document Intelligence
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        try:
            # Process the image with Azure Document Intelligence
            result = extract_text_from_document(temp_path)
            
            # Clean up temporary file
            os.remove(temp_path)
            
            # Return results
            return jsonify({
                'success': True,
                'filename': filename,
                'text_regions': result.get('text_regions', []),
                'full_text': result.get('full_text', ''),
                'processing_time': result.get('processing_time', 0),
                'total_regions': len(result.get('text_regions', []))
            })
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({
                'success': False,
                'error': f'Text detection failed: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Request processing failed: {str(e)}'
        }), 500

@app.route('/docs')
def api_docs():
    """API documentation"""
    docs = {
        "title": "SLD Text Detection API",
        "version": "1.0.0",
        "description": "API for detecting text in Single Line Diagrams using Azure Document Intelligence",
        "endpoints": {
            "POST /detect": {
                "description": "Upload an image file for text detection",
                "parameters": {
                    "file": "Image file (PNG, JPG, JPEG, GIF, BMP, TIFF)"
                },
                "response": {
                    "success": "boolean",
                    "filename": "string",
                    "text_regions": "array of text regions with coordinates",
                    "full_text": "string - all detected text",
                    "processing_time": "number - processing time in seconds",
                    "total_regions": "number - count of text regions found"
                }
            },
            "GET /health": {
                "description": "Check API health status",
                "response": {
                    "status": "string",
                    "service": "string",
                    "azure_configured": "boolean"
                }
            }
        },
        "requirements": {
            "azure_endpoint": "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable",
            "azure_key": "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variable"
        }
    }
    return jsonify(docs)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check Azure configuration
    endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
    
    if not endpoint or not key:
        print("⚠️  Warning: Azure Document Intelligence credentials not found!")
        print("   Set these environment variables:")
        print("   - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        print("   - AZURE_DOCUMENT_INTELLIGENCE_KEY")
        print()
    
    print("🚀 Starting SLD Text Detection API Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("📖 API documentation: http://localhost:5000/docs")
    print("🔍 Health check: http://localhost:5000/health")
    print()
    print("🛑 To stop the server: Press Ctrl+C")
    print()
    
    # Start the Flask development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )

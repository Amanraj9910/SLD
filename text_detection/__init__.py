"""
Text Detection Module for SLD Processing

This module provides Azure Document Intelligence OCR capabilities for extracting
text from Single Line Diagrams with precise bounding boxes and confidence scores.

Main Components:
- DocumentOCR: Main OCR class with Azure integration
- TextElement: Data class for individual text elements
- TextDetectionResult: Data class for complete results
- extract_text_from_document: Convenience function for quick text extraction

Example Usage:
    from text_detection import extract_text_from_document
    
    result = extract_text_from_document("sld_diagram.jpg")
    print(f"Found {len(result.text_elements)} text elements")
"""

from .document_ocr import (
    DocumentOCR,
    TextElement,
    TextDetectionResult,
    extract_text_from_document
)

__version__ = "1.0.0"
__author__ = "SLD Processing Team"

__all__ = [
    "DocumentOCR",
    "TextElement",
    "TextDetectionResult", 
    "extract_text_from_document"
]

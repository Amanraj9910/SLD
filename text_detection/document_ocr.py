"""
Text Detection Module for SLD Processing using Azure Document Intelligence
Provides OCR capabilities for extracting text from SLD diagrams with precise bounding boxes.
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import logging

# Import performance monitoring and caching
try:
    from .performance import get_cache, performance_monitor, PerformanceMetrics
except ImportError:
    # Fallback if performance module is not available
    def performance_monitor(operation_type: str = "text_detection"):
        def decorator(func):
            return func
        return decorator

    def get_cache():
        return None

try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import HttpResponseError
except ImportError:
    raise ImportError(
        "Azure Document Intelligence SDK is required. "
        "Install with: pip install azure-ai-documentintelligence"
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TextElement:
    """Data class for individual text elements"""
    text: str
    confidence: float
    polygon: List[Tuple[float, float]]  # List of (x, y) coordinates
    bounding_box: Dict[str, float]  # {"left": x, "top": y, "width": w, "height": h}
    page_number: int = 1

@dataclass
class TextDetectionResult:
    """Data class for complete text detection results"""
    document_path: str
    document_type: str  # "image" or "pdf"
    page_count: int
    text_elements: List[TextElement]
    processing_time: float
    total_text_length: int
    service_info: Dict[str, str]
    image_dimensions: Optional[Dict[str, int]] = None

class DocumentOCR:
    """
    Azure Document Intelligence OCR client for SLD text extraction.
    
    Supports:
    - Image formats: JPG, PNG, BMP, TIFF
    - PDF documents (single and multi-page)
    - High-precision text extraction with bounding polygons
    - Confidence scores for each text element
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: str = "prebuilt-read"
    ):
        """
        Initialize the Document OCR client.
        
        Args:
            endpoint: Azure Document Intelligence endpoint URL
            api_key: Azure Document Intelligence API key
            model_id: Model to use for analysis (default: "prebuilt-read")
        """
        # Get credentials from environment if not provided
        self.endpoint = endpoint or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        self.model_id = model_id
        
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure Document Intelligence credentials are required. "
                "Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY "
                "environment variables or pass them as parameters."
            )
        
        # Initialize client
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        
        logger.info(f"Initialized Document OCR client with endpoint: {self.endpoint}")
    
    @performance_monitor("text_detection")
    def extract_text(
        self,
        document_path: Union[str, Path],
        output_format: str = "detailed",
        save_results: bool = False,
        output_dir: Optional[str] = None,
        use_cache: bool = True
    ) -> TextDetectionResult:
        """
        Extract text from a document (image or PDF) with intelligent caching.

        Args:
            document_path: Path to the document file
            output_format: Output format ("detailed" or "simple")
            save_results: Whether to save results to JSON file
            output_dir: Directory to save results (optional)
            use_cache: Whether to use caching for repeated API calls

        Returns:
            TextDetectionResult object with extracted text and metadata
        """
        start_time = time.time()

        # Validate input
        document_path = Path(document_path)
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")

        # Check cache first if enabled
        cache = get_cache() if use_cache else None
        cache_key_params = {
            "output_format": output_format,
            "model_id": self.model_id,
            "endpoint": self.endpoint[:50]  # Partial endpoint for cache key
        }

        if cache:
            cached_result = cache.get(document_path, cache_key_params)
            if cached_result:
                logger.info(f"Using cached result for {document_path.name}")

                # Convert cached data back to TextDetectionResult
                text_elements = [
                    TextElement(
                        text=elem["text"],
                        confidence=elem["confidence"],
                        polygon=elem["polygon"],
                        bounding_box=elem["bounding_box"],
                        page_number=elem.get("page_number", 1)
                    )
                    for elem in cached_result.get("text_elements", [])
                ]

                return TextDetectionResult(
                    document_path=str(document_path),
                    document_type=cached_result.get("document_type", "image"),
                    page_count=cached_result.get("page_count", 1),
                    text_elements=text_elements,
                    processing_time=cached_result.get("processing_time", 0.0),
                    total_text_length=cached_result.get("total_text_length", 0),
                    service_info=cached_result.get("service_info", {}),
                    image_dimensions=cached_result.get("image_dimensions")
                )

        # Determine document type
        document_type = self._get_document_type(document_path)
        
        # Read document content
        with open(document_path, "rb") as document:
            document_content = document.read()
        
        try:
            # Analyze document with retry logic
            logger.info(f"Analyzing document: {document_path}")

            # Implement retry logic for Azure API calls
            max_retries = 3
            retry_delay = 1.0

            for attempt in range(max_retries):
                try:
                    logger.info(f"Azure API call attempt {attempt + 1}/{max_retries}")

                    # Use the correct API format for Azure Document Intelligence
                    # Use 'document' parameter instead of 'body' for stable SDK version
                    poller = self.client.begin_analyze_document(
                        model_id=self.model_id,
                        document=document_content,
                        content_type="image/png" if document_path.suffix.lower() == '.png' else "image/jpeg"
                    )

                    # Wait for completion with timeout
                    result = poller.result()
                    logger.info(f"Azure API call successful on attempt {attempt + 1}")
                    break

                except HttpResponseError as api_error:
                    if attempt == max_retries - 1:
                        # Last attempt failed
                        logger.error(f"Azure API failed after {max_retries} attempts: {api_error}")
                        raise RuntimeError(f"Azure Document Intelligence API failed: {api_error}")
                    else:
                        # Retry with exponential backoff
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Azure API attempt {attempt + 1} failed: {api_error}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                except Exception as unexpected_error:
                    if attempt == max_retries - 1:
                        logger.error(f"Unexpected error after {max_retries} attempts: {unexpected_error}")
                        raise RuntimeError(f"Unexpected error during document analysis: {unexpected_error}")
                    else:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Unexpected error on attempt {attempt + 1}: {unexpected_error}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
            
            # Process results
            text_elements = self._process_analysis_result(result, output_format)

            processing_time = time.time() - start_time

            # Get image dimensions
            image_dimensions = self._get_image_dimensions(document_path)

            # Create result object
            detection_result = TextDetectionResult(
                document_path=str(document_path),
                document_type=document_type,
                page_count=len(result.pages) if result.pages else 1,
                text_elements=text_elements,
                processing_time=processing_time,
                total_text_length=sum(len(elem.text) for elem in text_elements),
                service_info={
                    "endpoint": self.endpoint,
                    "model_id": self.model_id,
                    "api_version": "2024-02-29-preview"
                },
                image_dimensions=image_dimensions
            )
            
            logger.info(
                f"Text extraction completed in {processing_time:.2f}s. "
                f"Found {len(text_elements)} text elements."
            )

            # Cache the result if caching is enabled
            if cache:
                try:
                    cache_data = {
                        "document_path": str(document_path),
                        "document_type": detection_result.document_type,
                        "page_count": detection_result.page_count,
                        "processing_time": detection_result.processing_time,
                        "total_text_length": detection_result.total_text_length,
                        "service_info": detection_result.service_info,
                        "image_dimensions": detection_result.image_dimensions,
                        "text_elements": [
                            {
                                "text": elem.text,
                                "confidence": elem.confidence,
                                "polygon": elem.polygon,
                                "bounding_box": elem.bounding_box,
                                "page_number": elem.page_number
                            }
                            for elem in text_elements
                        ]
                    }
                    cache.put(document_path, cache_data, cache_key_params)
                except Exception as e:
                    logger.warning(f"Failed to cache result: {e}")

            # Save results if requested
            if save_results:
                if output_dir is None:
                    # Use the standardized outputs directory
                    text_detection_dir = Path(__file__).parent
                    output_dir = text_detection_dir / "outputs"

                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                # Generate output filename with required format: {image_name}_text_detection.json
                base_name = Path(document_path).stem
                json_path = output_dir / f"{base_name}_text_detection.json"

                # Export results
                self.export_results(detection_result, json_path, "json")

                logger.info(f"Text detection results saved to: {json_path}")

            return detection_result
            
        except HttpResponseError as e:
            logger.error(f"Azure Document Intelligence API error: {e}")
            raise RuntimeError(f"Failed to analyze document: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during text extraction: {e}")
            raise RuntimeError(f"Text extraction failed: {e}")
    
    def _get_document_type(self, document_path: Path) -> str:
        """Determine document type based on file extension"""
        extension = document_path.suffix.lower()
        
        if extension == ".pdf":
            return "pdf"
        elif extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]:
            return "image"
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _process_analysis_result(
        self,
        result,
        output_format: str
    ) -> List[TextElement]:
        """
        Process Azure Document Intelligence analysis result with optimized duplicate handling.

        OPTIMIZATION: This method now processes text elements more efficiently by prioritizing
        higher-level elements (paragraphs > lines > words) and avoiding duplicate processing.
        For SLD diagrams, this provides better performance while maintaining comprehensive
        text detection for labels, component names, values, etc.

        Args:
            result: Azure Document Intelligence analysis result
            output_format: Output format (detailed or simple)

        Returns:
            List of TextElement objects
        """
        text_elements = []

        if not result.pages:
            return text_elements

        for page_idx, page in enumerate(result.pages, 1):
            # OPTIMIZATION: Process in priority order and track covered areas to avoid duplicates
            processed_areas = []

            # Priority 1: Process paragraphs (highest level, most structured)
            if hasattr(page, 'paragraphs') and page.paragraphs:
                for paragraph in page.paragraphs:
                    if not paragraph.content or not paragraph.content.strip():
                        continue

                    polygon = self._extract_polygon_coordinates(paragraph)
                    bounding_box = self._polygon_to_bbox(polygon)
                    confidence = getattr(paragraph, 'confidence', 1.0)

                    text_element = TextElement(
                        text=paragraph.content.strip(),
                        confidence=confidence,
                        polygon=polygon,
                        bounding_box=bounding_box,
                        page_number=page_idx
                    )

                    text_elements.append(text_element)
                    processed_areas.append(bounding_box)

            # Priority 2: Process lines not already covered by paragraphs
            if hasattr(page, 'lines') and page.lines and output_format == "detailed":
                for line in page.lines:
                    if not line.content or not line.content.strip():
                        continue

                    polygon = self._extract_polygon_coordinates(line)
                    bounding_box = self._polygon_to_bbox(polygon)

                    # Skip if this line is already covered by a paragraph
                    if self._is_area_covered(bounding_box, processed_areas):
                        continue

                    confidence = getattr(line, 'confidence', 1.0)

                    text_element = TextElement(
                        text=line.content.strip(),
                        confidence=confidence,
                        polygon=polygon,
                        bounding_box=bounding_box,
                        page_number=page_idx
                    )

                    text_elements.append(text_element)
                    processed_areas.append(bounding_box)

            # Priority 3: Process individual words only if no higher-level elements exist
            has_paragraphs = hasattr(page, 'paragraphs') and page.paragraphs
            has_lines = hasattr(page, 'lines') and page.lines
            if page.words and output_format == "detailed" and not has_paragraphs and not has_lines:
                for word in page.words:
                    if not word.content or not word.content.strip():
                        continue

                    polygon = self._extract_polygon_coordinates(word)
                    bounding_box = self._polygon_to_bbox(polygon)
                    confidence = getattr(word, 'confidence', 1.0)

                    text_element = TextElement(
                        text=word.content.strip(),
                        confidence=confidence,
                        polygon=polygon,
                        bounding_box=bounding_box,
                        page_number=page_idx
                    )

                    text_elements.append(text_element)

        return text_elements

    def _extract_polygon_coordinates(self, element) -> List[Tuple[float, float]]:
        """Extract polygon coordinates from Azure Document Intelligence element"""
        polygon = []
        if hasattr(element, 'polygon') and element.polygon:
            for i in range(0, len(element.polygon), 2):
                if i + 1 < len(element.polygon):
                    x = float(element.polygon[i])
                    y = float(element.polygon[i + 1])
                    polygon.append((x, y))
        return polygon

    def _is_area_covered(self, bbox: Dict[str, float], processed_areas: List[Dict[str, float]], overlap_threshold: float = 0.8) -> bool:
        """Check if a bounding box area is already covered by processed areas"""
        if not processed_areas:
            return False

        bbox_area = bbox["width"] * bbox["height"]
        if bbox_area == 0:
            return False

        for processed_bbox in processed_areas:
            # Calculate intersection
            x_overlap = max(0, min(bbox["left"] + bbox["width"], processed_bbox["left"] + processed_bbox["width"]) -
                          max(bbox["left"], processed_bbox["left"]))
            y_overlap = max(0, min(bbox["top"] + bbox["height"], processed_bbox["top"] + processed_bbox["height"]) -
                          max(bbox["top"], processed_bbox["top"]))

            intersection_area = x_overlap * y_overlap
            overlap_ratio = intersection_area / bbox_area

            if overlap_ratio > overlap_threshold:
                return True

        return False

    def _polygon_to_bbox(self, polygon: List[Tuple[float, float]]) -> Dict[str, float]:
        """Convert polygon coordinates to bounding box"""
        if not polygon:
            return {"left": 0, "top": 0, "width": 0, "height": 0}
        
        x_coords = [point[0] for point in polygon]
        y_coords = [point[1] for point in polygon]
        
        left = min(x_coords)
        top = min(y_coords)
        right = max(x_coords)
        bottom = max(y_coords)
        
        return {
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top
        }

    def _remove_duplicate_text_elements(self, text_elements: List[TextElement]) -> List[TextElement]:
        """
        Remove duplicate text elements where words are already contained in lines.

        This method removes word-level elements that are already part of line-level elements
        to avoid duplication in the final results.

        Args:
            text_elements: List of all text elements (lines and words)

        Returns:
            List of unique text elements
        """
        if not text_elements:
            return text_elements

        # Separate lines and words based on text length and content
        lines = []
        words = []

        for element in text_elements:
            # Heuristic: lines typically contain multiple words or are longer
            if len(element.text.split()) > 1 or len(element.text) > 15:
                lines.append(element)
            else:
                words.append(element)

        # Keep all lines
        unique_elements = lines.copy()

        # Only keep words that are not contained in any line
        for word in words:
            is_contained = False
            for line in lines:
                if word.text.lower() in line.text.lower():
                    # Check if the word's bounding box is roughly within the line's bounding box
                    word_bbox = word.bounding_box
                    line_bbox = line.bounding_box

                    # Allow some tolerance for bounding box containment
                    tolerance = 5
                    if (word_bbox["left"] >= line_bbox["left"] - tolerance and
                        word_bbox["top"] >= line_bbox["top"] - tolerance and
                        word_bbox["left"] + word_bbox["width"] <= line_bbox["left"] + line_bbox["width"] + tolerance and
                        word_bbox["top"] + word_bbox["height"] <= line_bbox["top"] + line_bbox["height"] + tolerance):
                        is_contained = True
                        break

            if not is_contained:
                unique_elements.append(word)

        return unique_elements

    def _get_image_dimensions(self, document_path: Union[str, Path]) -> Dict[str, int]:
        """
        Get image dimensions from document.

        Args:
            document_path: Path to the document

        Returns:
            Dictionary with width and height
        """
        try:
            from PIL import Image

            document_path = Path(document_path)

            # Handle different file types
            if document_path.suffix.lower() == '.pdf':
                # For PDF, we'll use a default size since we can't easily get dimensions
                # without converting to image first
                return {"width": 1000, "height": 800}
            else:
                # For images, get actual dimensions
                with Image.open(document_path) as img:
                    return {"width": img.width, "height": img.height}

        except Exception as e:
            logger.warning(f"Could not get image dimensions: {e}")
            # Return default dimensions
            return {"width": 1000, "height": 800}

    def export_results(
        self,
        result: TextDetectionResult,
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """
        Export text detection results to file.

        Args:
            result: TextDetectionResult object
            output_path: Path to save the results
            format: Export format ("json" or "csv")
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            self._export_json(result, output_path)
        elif format.lower() == "csv":
            self._export_csv(result, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Text detection results exported to: {output_path}")

    def _export_json(self, result: TextDetectionResult, output_path: Path):
        """Export results as JSON with comprehensive metadata for interactive visualization"""
        import time

        data = {
            "document_path": result.document_path,
            "document_type": result.document_type,
            "page_count": result.page_count,
            "processing_time": result.processing_time,
            "total_text_length": result.total_text_length,
            "image_dimensions": result.image_dimensions,
            "service_info": result.service_info,
            "metadata": {
                "processing_timestamp": time.time(),
                "processing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "api_version": result.service_info.get("api_version", "2024-02-29-preview"),
                "total_elements": len(result.text_elements),
                "confidence_stats": self._calculate_confidence_stats(result.text_elements)
            },
            "text_elements": [
                {
                    "text": elem.text,
                    "confidence": elem.confidence,
                    "polygon": elem.polygon,  # Required format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    "bounding_box": {
                        "left": elem.bounding_box["left"],
                        "top": elem.bounding_box["top"],
                        "width": elem.bounding_box["width"],
                        "height": elem.bounding_box["height"],
                        # Additional formats for compatibility
                        "x1": elem.bounding_box["left"],
                        "y1": elem.bounding_box["top"],
                        "x2": elem.bounding_box["left"] + elem.bounding_box["width"],
                        "y2": elem.bounding_box["top"] + elem.bounding_box["height"]
                    },
                    "page": elem.page_number,
                    "line_number": getattr(elem, 'line_number', 1),
                    "word_index": getattr(elem, 'word_index', 1),
                    "center": {
                        "x": elem.bounding_box["left"] + elem.bounding_box["width"] / 2,
                        "y": elem.bounding_box["top"] + elem.bounding_box["height"] / 2
                    },
                    "area": elem.bounding_box["width"] * elem.bounding_box["height"],
                    "text_length": len(elem.text),
                    "word_count": len(elem.text.split())
                }
                for elem in result.text_elements
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _calculate_confidence_stats(self, text_elements: List[TextElement]) -> Dict[str, float]:
        """Calculate confidence statistics for text elements"""
        if not text_elements:
            return {"min": 0.0, "max": 0.0, "average": 0.0, "median": 0.0}

        confidences = [elem.confidence for elem in text_elements]
        confidences.sort()

        n = len(confidences)
        median = confidences[n // 2] if n % 2 == 1 else (confidences[n // 2 - 1] + confidences[n // 2]) / 2

        return {
            "min": min(confidences),
            "max": max(confidences),
            "average": sum(confidences) / len(confidences),
            "median": median
        }

    def _export_csv(self, result: TextDetectionResult, output_path: Path):
        """Export results as CSV"""
        import csv

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'text', 'confidence', 'page_number',
                'bbox_left', 'bbox_top', 'bbox_width', 'bbox_height',
                'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2',
                'center_x', 'center_y', 'area'
            ])

            # Write data
            for elem in result.text_elements:
                bbox = elem.bounding_box
                writer.writerow([
                    elem.text,
                    elem.confidence,
                    elem.page_number,
                    bbox["left"],
                    bbox["top"],
                    bbox["width"],
                    bbox["height"],
                    bbox["left"],  # x1
                    bbox["top"],   # y1
                    bbox["left"] + bbox["width"],   # x2
                    bbox["top"] + bbox["height"],   # y2
                    bbox["left"] + bbox["width"] / 2,   # center_x
                    bbox["top"] + bbox["height"] / 2,   # center_y
                    bbox["width"] * bbox["height"]      # area
                ])

    def extract_text_batch(
        self,
        document_paths: List[Union[str, Path]],
        output_dir: Optional[str] = None
    ) -> List[TextDetectionResult]:
        """
        Extract text from multiple documents.
        
        Args:
            document_paths: List of document paths
            output_dir: Directory to save individual results
            
        Returns:
            List of TextDetectionResult objects
        """
        results = []
        
        for document_path in document_paths:
            try:
                result = self.extract_text(document_path)
                results.append(result)
                
                # Save individual result if output directory specified
                if output_dir:
                    output_path = Path(output_dir) / f"{Path(document_path).stem}_text.json"
                    self.export_result(result, output_path, format="json")
                    
            except Exception as e:
                logger.error(f"Failed to process {document_path}: {e}")
                continue
        
        return results
    
    def export_result(
        self,
        result: TextDetectionResult,
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """
        Export text detection results to file.
        
        Args:
            result: TextDetectionResult object
            output_path: Path to save results
            format: Export format ("json", "txt", "csv")
        """
        output_path = Path(output_path)
        
        if format.lower() == "json":
            self._export_json(result, output_path)
        elif format.lower() == "txt":
            self._export_txt(result, output_path)
        elif format.lower() == "csv":
            self._export_csv(result, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, result: TextDetectionResult, output_path: Path):
        """Export results as JSON"""
        data = {
            "document_path": result.document_path,
            "document_type": result.document_type,
            "page_count": result.page_count,
            "processing_time": result.processing_time,
            "total_text_length": result.total_text_length,
            "service_info": result.service_info,
            "text_elements": [
                {
                    "text": elem.text,
                    "confidence": elem.confidence,
                    "polygon": elem.polygon,
                    "bounding_box": elem.bounding_box,
                    "page_number": elem.page_number
                }
                for elem in result.text_elements
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON results exported to: {output_path}")
    
    def _export_txt(self, result: TextDetectionResult, output_path: Path):
        """Export results as plain text"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Document: {result.document_path}\n")
            f.write(f"Processing time: {result.processing_time:.2f}s\n")
            f.write(f"Total text elements: {len(result.text_elements)}\n")
            f.write("-" * 50 + "\n\n")
            
            for i, elem in enumerate(result.text_elements, 1):
                f.write(f"{i:3d}. {elem.text}\n")
                f.write(f"     Confidence: {elem.confidence:.3f}\n")
                f.write(f"     Page: {elem.page_number}\n")
                f.write(f"     Bbox: {elem.bounding_box}\n\n")
        
        logger.info(f"Text results exported to: {output_path}")
    
    def _export_csv(self, result: TextDetectionResult, output_path: Path):
        """Export results as CSV"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'text', 'confidence', 'page_number',
                'bbox_left', 'bbox_top', 'bbox_width', 'bbox_height',
                'polygon_points'
            ])
            
            for elem in result.text_elements:
                polygon_str = ';'.join([f"{x},{y}" for x, y in elem.polygon])
                writer.writerow([
                    elem.text,
                    elem.confidence,
                    elem.page_number,
                    elem.bounding_box['left'],
                    elem.bounding_box['top'],
                    elem.bounding_box['width'],
                    elem.bounding_box['height'],
                    polygon_str
                ])
        
        logger.info(f"CSV results exported to: {output_path}")

# Convenience function for quick usage
def extract_text_from_document(
    document_path: Union[str, Path],
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None
) -> TextDetectionResult:
    """
    Quick function to extract text from a document.
    
    Args:
        document_path: Path to document
        endpoint: Azure endpoint (optional)
        api_key: Azure API key (optional)
        
    Returns:
        TextDetectionResult object
    """
    ocr = DocumentOCR(endpoint=endpoint, api_key=api_key)
    return ocr.extract_text(document_path)

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python document_ocr.py <document_path> [output_format]")
        sys.exit(1)
    
    document_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "json"
    
    # Extract text
    result = extract_text_from_document(document_path)
    
    # Print summary
    print(f"\nText Extraction Results for: {result.document_path}")
    print(f"Document type: {result.document_type}")
    print(f"Pages: {result.page_count}")
    print(f"Processing time: {result.processing_time:.2f}s")
    print(f"Text elements found: {len(result.text_elements)}")
    print(f"Total text length: {result.total_text_length} characters")
    
    # Show first few text elements
    print("\nFirst 5 text elements:")
    for i, elem in enumerate(result.text_elements[:5], 1):
        print(f"  {i}. '{elem.text}' (confidence: {elem.confidence:.3f})")
    
    # Export results
    output_path = Path(document_path).with_suffix(f'.{output_format}')
    ocr = DocumentOCR()
    ocr.export_result(result, output_path, format=output_format)
    print(f"\nResults saved to: {output_path}")

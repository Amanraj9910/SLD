"""
Text Detection Integration API
Provides a clean API for downstream modules to consume text detection results.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass

try:
    from .utils import TextDetectionIntegration, TextSearchEngine, CoordinateUtils
    from .document_ocr import DocumentOCR, TextDetectionResult
    from .performance import get_cache
except ImportError:
    from utils import TextDetectionIntegration, TextSearchEngine, CoordinateUtils
    from document_ocr import DocumentOCR, TextDetectionResult
    from performance import get_cache

logger = logging.getLogger(__name__)

@dataclass
class TextRegion:
    """Represents a text region with enhanced metadata"""
    text: str
    confidence: float
    bbox: Dict[str, float]
    polygon: List[List[float]]
    page: int
    area: float
    center: Tuple[float, float]
    word_count: int
    char_count: int
    
    @classmethod
    def from_element(cls, element: Dict[str, Any]) -> 'TextRegion':
        """Create TextRegion from text element dictionary"""
        bbox = element.get("bounding_box", {})
        center = element.get("center", {})
        
        return cls(
            text=element.get("text", ""),
            confidence=element.get("confidence", 0.0),
            bbox=bbox,
            polygon=element.get("polygon", []),
            page=element.get("page", 1),
            area=element.get("area", 0.0),
            center=(center.get("x", 0.0), center.get("y", 0.0)),
            word_count=element.get("word_count", len(element.get("text", "").split())),
            char_count=element.get("text_length", len(element.get("text", "")))
        )

class TextDetectionAPI:
    """Main API class for text detection integration"""
    
    def __init__(self, azure_endpoint: Optional[str] = None, 
                 azure_api_key: Optional[str] = None):
        """
        Initialize the Text Detection API.
        
        Args:
            azure_endpoint: Azure Document Intelligence endpoint
            azure_api_key: Azure Document Intelligence API key
        """
        self.ocr = None
        if azure_endpoint and azure_api_key:
            self.ocr = DocumentOCR(endpoint=azure_endpoint, api_key=azure_api_key)
        
        self.cache = get_cache()
    
    def process_image(self, image_path: Union[str, Path], 
                     use_cache: bool = True,
                     save_results: bool = True) -> Dict[str, Any]:
        """
        Process an SLD image and extract text with full metadata.
        
        Args:
            image_path: Path to the SLD image
            use_cache: Whether to use caching
            save_results: Whether to save results to JSON
            
        Returns:
            Dictionary with text detection results and metadata
        """
        if not self.ocr:
            raise RuntimeError("Azure Document Intelligence not configured")
        
        try:
            result = self.ocr.extract_text(
                document_path=image_path,
                output_format="detailed",
                save_results=save_results,
                use_cache=use_cache
            )
            
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            raise
    
    def load_results(self, json_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load text detection results from JSON file.
        
        Args:
            json_path: Path to JSON results file
            
        Returns:
            Dictionary with text detection results
        """
        data = TextDetectionIntegration.load_detection_results(json_path)
        if not data:
            raise ValueError(f"Failed to load results from {json_path}")
        
        return data
    
    def get_text_regions(self, results: Dict[str, Any], 
                        confidence_threshold: float = 0.0) -> List[TextRegion]:
        """
        Get text regions from detection results.
        
        Args:
            results: Text detection results dictionary
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of TextRegion objects
        """
        text_elements = results.get("text_elements", [])
        regions = []
        
        for element in text_elements:
            if element.get("confidence", 0.0) >= confidence_threshold:
                regions.append(TextRegion.from_element(element))
        
        return regions
    
    def search_text(self, results: Dict[str, Any], query: str,
                   case_sensitive: bool = False,
                   fuzzy: bool = False,
                   confidence_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for text in detection results.
        
        Args:
            results: Text detection results dictionary
            query: Search query
            case_sensitive: Whether search is case sensitive
            fuzzy: Whether to use fuzzy matching
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of search results with match scores
        """
        search_engine = TextDetectionIntegration.create_search_index(results)
        search_results = search_engine.search_text(
            query=query,
            case_sensitive=case_sensitive,
            fuzzy=fuzzy,
            confidence_threshold=confidence_threshold
        )
        
        return [
            {
                "element_index": result.element_index,
                "text_element": result.text_element,
                "match_score": result.match_score,
                "match_type": result.match_type
            }
            for result in search_results
        ]
    
    def find_text_at_position(self, results: Dict[str, Any], 
                             x: float, y: float,
                             tolerance: float = 5.0) -> List[Dict[str, Any]]:
        """
        Find text elements at a specific position.
        
        Args:
            results: Text detection results dictionary
            x: X coordinate
            y: Y coordinate
            tolerance: Position tolerance in pixels
            
        Returns:
            List of text elements at the position
        """
        search_engine = TextDetectionIntegration.create_search_index(results)
        search_results = search_engine.search_by_position(x, y, tolerance)
        
        return [
            {
                "element_index": result.element_index,
                "text_element": result.text_element,
                "distance_score": result.match_score
            }
            for result in search_results
        ]
    
    def get_text_in_region(self, results: Dict[str, Any],
                          region_bbox: Dict[str, float],
                          overlap_threshold: float = 0.5) -> List[TextRegion]:
        """
        Get text elements that overlap with a specific region.
        
        Args:
            results: Text detection results dictionary
            region_bbox: Region bounding box {"left", "top", "width", "height"}
            overlap_threshold: Minimum overlap ratio (0.0 to 1.0)
            
        Returns:
            List of TextRegion objects in the region
        """
        region_elements = TextDetectionIntegration.get_text_by_region(
            results, region_bbox, overlap_threshold
        )
        
        return [TextRegion.from_element(element) for element in region_elements]
    
    def extract_component_labels(self, results: Dict[str, Any],
                                component_regions: List[Dict[str, float]]) -> Dict[int, List[str]]:
        """
        Extract text labels for detected components.
        
        Args:
            results: Text detection results dictionary
            component_regions: List of component bounding boxes
            
        Returns:
            Dictionary mapping component index to list of associated text labels
        """
        component_labels = {}
        
        for i, component_bbox in enumerate(component_regions):
            # Expand component region slightly to catch nearby labels
            expanded_bbox = {
                "left": component_bbox["left"] - 20,
                "top": component_bbox["top"] - 20,
                "width": component_bbox["width"] + 40,
                "height": component_bbox["height"] + 40
            }
            
            # Find text in expanded region
            text_regions = self.get_text_in_region(results, expanded_bbox, 0.1)
            
            # Extract text labels
            labels = [region.text for region in text_regions if region.confidence > 0.7]
            component_labels[i] = labels
        
        return component_labels
    
    def get_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about text detection results.
        
        Args:
            results: Text detection results dictionary
            
        Returns:
            Dictionary with various statistics
        """
        text_elements = results.get("text_elements", [])
        
        if not text_elements:
            return {"message": "No text elements found"}
        
        confidences = [elem.get("confidence", 0.0) for elem in text_elements]
        areas = [elem.get("area", 0.0) for elem in text_elements]
        word_counts = [elem.get("word_count", len(elem.get("text", "").split())) for elem in text_elements]
        
        return {
            "total_elements": len(text_elements),
            "total_characters": results.get("total_text_length", 0),
            "total_words": sum(word_counts),
            "average_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "high_confidence_elements": len([c for c in confidences if c > 0.9]),
            "low_confidence_elements": len([c for c in confidences if c < 0.7]),
            "average_text_area": sum(areas) / len(areas) if areas else 0,
            "processing_time": results.get("processing_time", 0.0),
            "image_dimensions": results.get("image_dimensions", {}),
            "confidence_distribution": {
                "90-100%": len([c for c in confidences if c >= 0.9]),
                "80-90%": len([c for c in confidences if 0.8 <= c < 0.9]),
                "70-80%": len([c for c in confidences if 0.7 <= c < 0.8]),
                "60-70%": len([c for c in confidences if 0.6 <= c < 0.7]),
                "below_60%": len([c for c in confidences if c < 0.6])
            }
        }
    
    def transform_coordinates(self, results: Dict[str, Any],
                            scale_x: float, scale_y: float,
                            offset_x: float = 0.0, offset_y: float = 0.0) -> Dict[str, Any]:
        """
        Transform coordinates in text detection results.
        
        Args:
            results: Text detection results dictionary
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor
            offset_x: X-axis offset
            offset_y: Y-axis offset
            
        Returns:
            Results with transformed coordinates
        """
        transformed_results = results.copy()
        transformed_elements = []
        
        for element in results.get("text_elements", []):
            transformed_element = element.copy()
            
            # Transform polygon
            if "polygon" in element:
                transformed_polygon = CoordinateUtils.scale_coordinates(
                    element["polygon"], scale_x, scale_y
                )
                transformed_polygon = CoordinateUtils.translate_coordinates(
                    transformed_polygon, offset_x, offset_y
                )
                transformed_element["polygon"] = transformed_polygon
            
            # Transform bounding box
            if "bounding_box" in element:
                transformed_bbox = CoordinateUtils.scale_coordinates(
                    element["bounding_box"], scale_x, scale_y
                )
                transformed_bbox = CoordinateUtils.translate_coordinates(
                    transformed_bbox, offset_x, offset_y
                )
                transformed_element["bounding_box"] = transformed_bbox
                
                # Update center and area
                transformed_element["center"] = {
                    "x": transformed_bbox["left"] + transformed_bbox["width"] / 2,
                    "y": transformed_bbox["top"] + transformed_bbox["height"] / 2
                }
                transformed_element["area"] = transformed_bbox["width"] * transformed_bbox["height"]
            
            transformed_elements.append(transformed_element)
        
        transformed_results["text_elements"] = transformed_elements
        
        # Transform image dimensions if present
        if "image_dimensions" in results:
            dims = results["image_dimensions"]
            transformed_results["image_dimensions"] = {
                "width": int(dims.get("width", 0) * scale_x),
                "height": int(dims.get("height", 0) * scale_y)
            }
        
        return transformed_results
    
    def export_for_annotation(self, results: Dict[str, Any], 
                             output_path: Union[str, Path]) -> bool:
        """
        Export results for annotation tools.
        
        Args:
            results: Text detection results dictionary
            output_path: Path to save annotation data
            
        Returns:
            True if export was successful
        """
        return TextDetectionIntegration.export_for_annotation_tool(results, output_path)
    
    def _format_result(self, result: TextDetectionResult) -> Dict[str, Any]:
        """Format TextDetectionResult as dictionary"""
        return {
            "document_path": result.document_path,
            "document_type": result.document_type,
            "page_count": result.page_count,
            "processing_time": result.processing_time,
            "total_text_length": result.total_text_length,
            "image_dimensions": result.image_dimensions,
            "service_info": result.service_info,
            "text_elements": [
                {
                    "text": elem.text,
                    "confidence": elem.confidence,
                    "polygon": elem.polygon,
                    "bounding_box": elem.bounding_box,
                    "page": elem.page_number,
                    "center": {
                        "x": elem.bounding_box["left"] + elem.bounding_box["width"] / 2,
                        "y": elem.bounding_box["top"] + elem.bounding_box["height"] / 2
                    },
                    "area": elem.bounding_box["width"] * elem.bounding_box["height"],
                    "word_count": len(elem.text.split()),
                    "text_length": len(elem.text)
                }
                for elem in result.text_elements
            ]
        }

# Convenience functions for quick access
def process_sld_image(image_path: Union[str, Path], 
                     azure_endpoint: Optional[str] = None,
                     azure_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Quick function to process an SLD image"""
    api = TextDetectionAPI(azure_endpoint, azure_api_key)
    return api.process_image(image_path)

def load_text_results(json_path: Union[str, Path]) -> Dict[str, Any]:
    """Quick function to load text detection results"""
    api = TextDetectionAPI()
    return api.load_results(json_path)

def search_sld_text(results: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Quick function to search text in SLD results"""
    api = TextDetectionAPI()
    return api.search_text(results, query)

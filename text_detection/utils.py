"""
Text Detection Utilities
Provides coordinate transformation utilities and integration helpers for downstream modules.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

@dataclass
class TextSearchResult:
    """Result of text search operation"""
    element_index: int
    text_element: Dict[str, Any]
    match_score: float
    match_type: str  # "exact", "partial", "fuzzy"

class CoordinateUtils:
    """Utility functions for coordinate transformations and calculations"""
    
    @staticmethod
    def polygon_to_bbox(polygon: List[List[float]]) -> Dict[str, float]:
        """Convert polygon coordinates to bounding box"""
        if not polygon:
            return {"left": 0, "top": 0, "width": 0, "height": 0}
        
        x_coords = [point[0] for point in polygon if len(point) >= 2]
        y_coords = [point[1] for point in polygon if len(point) >= 2]
        
        if not x_coords or not y_coords:
            return {"left": 0, "top": 0, "width": 0, "height": 0}
        
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
    
    @staticmethod
    def bbox_to_polygon(bbox: Dict[str, float]) -> List[List[float]]:
        """Convert bounding box to polygon coordinates (rectangle)"""
        left = bbox.get("left", 0)
        top = bbox.get("top", 0)
        width = bbox.get("width", 0)
        height = bbox.get("height", 0)
        
        return [
            [left, top],
            [left + width, top],
            [left + width, top + height],
            [left, top + height]
        ]
    
    @staticmethod
    def scale_coordinates(coords: Union[List[List[float]], Dict[str, float]], 
                         scale_x: float, scale_y: float) -> Union[List[List[float]], Dict[str, float]]:
        """Scale coordinates by given factors"""
        if isinstance(coords, list):  # Polygon
            return [[point[0] * scale_x, point[1] * scale_y] for point in coords if len(point) >= 2]
        elif isinstance(coords, dict):  # Bounding box
            return {
                "left": coords.get("left", 0) * scale_x,
                "top": coords.get("top", 0) * scale_y,
                "width": coords.get("width", 0) * scale_x,
                "height": coords.get("height", 0) * scale_y
            }
        else:
            raise ValueError("Coordinates must be polygon (list) or bounding box (dict)")
    
    @staticmethod
    def translate_coordinates(coords: Union[List[List[float]], Dict[str, float]], 
                            offset_x: float, offset_y: float) -> Union[List[List[float]], Dict[str, float]]:
        """Translate coordinates by given offset"""
        if isinstance(coords, list):  # Polygon
            return [[point[0] + offset_x, point[1] + offset_y] for point in coords if len(point) >= 2]
        elif isinstance(coords, dict):  # Bounding box
            return {
                "left": coords.get("left", 0) + offset_x,
                "top": coords.get("top", 0) + offset_y,
                "width": coords.get("width", 0),
                "height": coords.get("height", 0)
            }
        else:
            raise ValueError("Coordinates must be polygon (list) or bounding box (dict)")
    
    @staticmethod
    def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    @staticmethod
    def calculate_polygon_area(polygon: List[List[float]]) -> float:
        """Calculate the area of a polygon using the shoelace formula"""
        if len(polygon) < 3:
            return 0.0
        
        area = 0.0
        n = len(polygon)
        
        for i in range(n):
            j = (i + 1) % n
            area += polygon[i][0] * polygon[j][1]
            area -= polygon[j][0] * polygon[i][1]
        
        return abs(area) / 2.0
    
    @staticmethod
    def calculate_polygon_centroid(polygon: List[List[float]]) -> Tuple[float, float]:
        """Calculate the centroid of a polygon"""
        if not polygon:
            return (0.0, 0.0)
        
        x_sum = sum(point[0] for point in polygon if len(point) >= 2)
        y_sum = sum(point[1] for point in polygon if len(point) >= 2)
        count = len([point for point in polygon if len(point) >= 2])
        
        if count == 0:
            return (0.0, 0.0)
        
        return (x_sum / count, y_sum / count)

class TextSearchEngine:
    """Search engine for text detection results"""
    
    def __init__(self, text_elements: List[Dict[str, Any]]):
        self.text_elements = text_elements
    
    def search_text(self, query: str, case_sensitive: bool = False, 
                   fuzzy: bool = False, confidence_threshold: float = 0.0) -> List[TextSearchResult]:
        """Search for text in detection results"""
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for i, element in enumerate(self.text_elements):
            text = element.get("text", "")
            confidence = element.get("confidence", 0.0)
            
            # Skip low confidence elements if threshold is set
            if confidence < confidence_threshold:
                continue
            
            if not case_sensitive:
                text = text.lower()
            
            # Exact match
            if query == text:
                results.append(TextSearchResult(i, element, 1.0, "exact"))
            # Partial match
            elif query in text:
                score = len(query) / len(text)
                results.append(TextSearchResult(i, element, score, "partial"))
            # Fuzzy match (if enabled)
            elif fuzzy:
                score = self._calculate_fuzzy_score(query, text)
                if score > 0.6:  # Threshold for fuzzy matching
                    results.append(TextSearchResult(i, element, score, "fuzzy"))
        
        # Sort by match score (descending)
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
    
    def search_by_position(self, x: float, y: float, tolerance: float = 5.0) -> List[TextSearchResult]:
        """Search for text elements at a specific position"""
        results = []
        
        for i, element in enumerate(self.text_elements):
            bbox = element.get("bounding_box", {})
            polygon = element.get("polygon", [])
            
            # Check if point is within bounding box (with tolerance)
            if (bbox.get("left", 0) - tolerance <= x <= bbox.get("left", 0) + bbox.get("width", 0) + tolerance and
                bbox.get("top", 0) - tolerance <= y <= bbox.get("top", 0) + bbox.get("height", 0) + tolerance):
                
                # More precise check using polygon if available
                if polygon and CoordinateUtils.point_in_polygon((x, y), polygon):
                    results.append(TextSearchResult(i, element, 1.0, "exact"))
                else:
                    # Calculate distance from center for scoring
                    center_x = bbox.get("left", 0) + bbox.get("width", 0) / 2
                    center_y = bbox.get("top", 0) + bbox.get("height", 0) / 2
                    distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                    max_distance = max(bbox.get("width", 0), bbox.get("height", 0)) / 2
                    score = max(0, 1 - (distance / max_distance)) if max_distance > 0 else 0
                    results.append(TextSearchResult(i, element, score, "partial"))
        
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
    
    def search_by_confidence_range(self, min_confidence: float, max_confidence: float = 1.0) -> List[TextSearchResult]:
        """Search for text elements within a confidence range"""
        results = []
        
        for i, element in enumerate(self.text_elements):
            confidence = element.get("confidence", 0.0)
            
            if min_confidence <= confidence <= max_confidence:
                results.append(TextSearchResult(i, element, confidence, "exact"))
        
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
    
    def _calculate_fuzzy_score(self, query: str, text: str) -> float:
        """Calculate fuzzy matching score using simple edit distance"""
        if not query or not text:
            return 0.0
        
        # Simple Levenshtein distance implementation
        m, n = len(query), len(text)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if query[i - 1] == text[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
        
        edit_distance = dp[m][n]
        max_len = max(m, n)
        return 1 - (edit_distance / max_len) if max_len > 0 else 0.0

class TextDetectionIntegration:
    """Integration utilities for downstream modules"""
    
    @staticmethod
    def load_detection_results(json_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load text detection results from JSON file"""
        try:
            json_path = Path(json_path)
            if not json_path.exists():
                logger.error(f"Text detection results file not found: {json_path}")
                return None
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ["text_elements"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field in JSON: {field}")
                    return None
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load text detection results: {e}")
            return None
    
    @staticmethod
    def extract_text_content(detection_results: Dict[str, Any], 
                           confidence_threshold: float = 0.0) -> List[str]:
        """Extract just the text content from detection results"""
        text_elements = detection_results.get("text_elements", [])
        return [
            element.get("text", "")
            for element in text_elements
            if element.get("confidence", 0.0) >= confidence_threshold
        ]
    
    @staticmethod
    def get_text_by_region(detection_results: Dict[str, Any], 
                          region_bbox: Dict[str, float],
                          overlap_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Get text elements that overlap with a specific region"""
        text_elements = detection_results.get("text_elements", [])
        region_elements = []
        
        for element in text_elements:
            element_bbox = element.get("bounding_box", {})
            overlap_ratio = TextDetectionIntegration._calculate_bbox_overlap(element_bbox, region_bbox)
            
            if overlap_ratio >= overlap_threshold:
                region_elements.append(element)
        
        return region_elements
    
    @staticmethod
    def _calculate_bbox_overlap(bbox1: Dict[str, float], bbox2: Dict[str, float]) -> float:
        """Calculate overlap ratio between two bounding boxes"""
        # Calculate intersection
        x1 = max(bbox1.get("left", 0), bbox2.get("left", 0))
        y1 = max(bbox1.get("top", 0), bbox2.get("top", 0))
        x2 = min(bbox1.get("left", 0) + bbox1.get("width", 0), 
                bbox2.get("left", 0) + bbox2.get("width", 0))
        y2 = min(bbox1.get("top", 0) + bbox1.get("height", 0), 
                bbox2.get("top", 0) + bbox2.get("height", 0))
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection_area = (x2 - x1) * (y2 - y1)
        bbox1_area = bbox1.get("width", 0) * bbox1.get("height", 0)
        
        return intersection_area / bbox1_area if bbox1_area > 0 else 0.0
    
    @staticmethod
    def create_search_index(detection_results: Dict[str, Any]) -> TextSearchEngine:
        """Create a search index for text detection results"""
        text_elements = detection_results.get("text_elements", [])
        return TextSearchEngine(text_elements)
    
    @staticmethod
    def export_for_annotation_tool(detection_results: Dict[str, Any], 
                                  output_path: Union[str, Path]) -> bool:
        """Export results in format suitable for annotation tools"""
        try:
            annotation_data = {
                "image_path": detection_results.get("document_path", ""),
                "image_dimensions": detection_results.get("image_dimensions", {}),
                "annotations": []
            }
            
            for i, element in enumerate(detection_results.get("text_elements", [])):
                annotation = {
                    "id": i,
                    "type": "text",
                    "text": element.get("text", ""),
                    "confidence": element.get("confidence", 0.0),
                    "coordinates": {
                        "polygon": element.get("polygon", []),
                        "bounding_box": element.get("bounding_box", {})
                    },
                    "metadata": {
                        "page": element.get("page", 1),
                        "area": element.get("area", 0),
                        "word_count": element.get("word_count", 0)
                    }
                }
                annotation_data["annotations"].append(annotation)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(annotation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Annotation data exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export annotation data: {e}")
            return False

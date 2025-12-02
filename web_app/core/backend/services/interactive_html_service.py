"""
Interactive HTML Generation Service
Creates interactive HTML visualizations for SLD component detection results.
"""

import json
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class InteractiveHTMLService:
    """Service for generating interactive HTML visualizations of SLD detection results"""
    
    def __init__(self):
        self.template_path = Path(__file__).parent / "templates" / "interactive_template.html"
    
    def generate_interactive_html(
        self,
        image_path: str,
        detections: List[Dict[str, Any]],
        output_path: str,
        image_dimensions: Dict[str, int],
        model_info: Dict[str, Any]
    ) -> str:
        """
        Generate interactive HTML visualization for SLD detection results.
        
        Args:
            image_path: Path to the original image
            detections: List of detection results
            output_path: Path where to save the HTML file
            image_dimensions: Image width and height
            model_info: Information about the model used
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Convert image to base64 for embedding
            image_base64 = self._image_to_base64(image_path)
            
            # Process detections for HTML
            processed_detections = self._process_detections(detections)
            
            # Generate component statistics
            stats = self._generate_statistics(processed_detections)
            
            # Create HTML content
            html_content = self._create_html_content(
                image_base64=image_base64,
                detections=processed_detections,
                stats=stats,
                image_dimensions=image_dimensions,
                model_info=model_info,
                original_image_name=Path(image_path).name
            )
            
            # Save HTML file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Interactive HTML generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate interactive HTML: {e}")
            raise
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string for embedding in HTML"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Determine image format
            image_format = Path(image_path).suffix.lower()
            if image_format == '.jpg' or image_format == '.jpeg':
                mime_type = 'image/jpeg'
            elif image_format == '.png':
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'  # Default
            
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return f"data:{mime_type};base64,{base64_string}"
            
        except Exception as e:
            logger.error(f"Failed to convert image to base64: {e}")
            return ""
    
    def _process_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process detection results for HTML display"""
        processed = []
        
        for i, detection in enumerate(detections):
            processed_detection = {
                'id': i + 1,
                'class_name': detection.get('class_name', 'Unknown'),
                'confidence': detection.get('confidence', 0.0),
                'bbox': detection.get('bbox', {}),
                'center': detection.get('center', {}),
                'area': detection.get('area', 0)
            }
            processed.append(processed_detection)
        
        # Sort by confidence (highest first)
        processed.sort(key=lambda x: x['confidence'], reverse=True)
        
        return processed
    
    def _generate_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics for the detections"""
        stats = {
            'total_components': len(detections),
            'by_type': {},
            'confidence_stats': {
                'average': 0.0,
                'min': 0.0,
                'max': 0.0
            }
        }
        
        if not detections:
            return stats
        
        # Count by type
        for detection in detections:
            class_name = detection['class_name']
            stats['by_type'][class_name] = stats['by_type'].get(class_name, 0) + 1
        
        # Confidence statistics
        confidences = [d['confidence'] for d in detections]
        stats['confidence_stats'] = {
            'average': sum(confidences) / len(confidences),
            'min': min(confidences),
            'max': max(confidences)
        }
        
        return stats
    
    def _create_html_content(
        self,
        image_base64: str,
        detections: List[Dict[str, Any]],
        stats: Dict[str, Any],
        image_dimensions: Dict[str, int],
        model_info: Dict[str, Any],
        original_image_name: str
    ) -> str:
        """Create the complete HTML content"""
        
        # Generate CSS for overlays
        overlay_css = self._generate_overlay_css(detections, image_dimensions)
        
        # Generate JavaScript data
        js_data = {
            'detections': detections,
            'stats': stats,
            'imageDimensions': image_dimensions
        }
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SLD Component Detection Visualization - {original_image_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            background-color: #f5f5f5;
        }}
        .sidebar {{
            width: 300px;
            padding: 20px;
            background: white;
            height: calc(100vh - 40px);
            position: fixed;
            overflow-y: auto;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .main-content {{
            margin-left: 340px;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .container {{
            position: relative;
            display: inline-block;
        }}
        .image {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .overlay {{
            position: absolute;
            border: 3px solid transparent;
            cursor: pointer;
            transition: all 0.3s;
            border-radius: 4px;
        }}
        .overlay:hover, .overlay.highlight {{
            border-color: #00ff00;
            background: rgba(0, 255, 0, 0.1);
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            white-space: nowrap;
        }}
        .stats {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .stats h2 {{
            margin: 0 0 15px 0;
            color: #333;
            font-size: 18px;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 4px 0;
        }}
        .stat-label {{
            font-weight: 500;
            color: #666;
        }}
        .stat-value {{
            font-weight: bold;
            color: #333;
        }}
        .component-list {{
            margin-top: 20px;
        }}
        .component-list h2 {{
            margin: 0 0 15px 0;
            color: #333;
            font-size: 18px;
        }}
        .component-item {{
            margin-bottom: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 4px solid #007bff;
        }}
        .component-item:hover {{
            background: #e9ecef;
            transform: translateX(2px);
        }}
        .component-item.highlight {{
            background: #d4edda;
            border-left-color: #28a745;
        }}
        .component-name {{
            font-weight: bold;
            color: #333;
            margin-bottom: 4px;
        }}
        .component-confidence {{
            font-size: 12px;
            color: #666;
        }}
        .confidence-bar {{
            width: 100%;
            height: 4px;
            background: #e9ecef;
            border-radius: 2px;
            margin-top: 4px;
            overflow: hidden;
        }}
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #dc3545, #ffc107, #28a745);
            border-radius: 2px;
            transition: width 0.3s;
        }}
        .filter-section {{
            margin-bottom: 15px;
        }}
        .search-input {{
            width: 100%;
            padding: 8px 12px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .sort-select {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            font-size: 14px;
        }}
        {overlay_css}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="stats">
            <h2>Component Summary</h2>
            <div id="statsContent"></div>
        </div>
        <div class="component-list">
            <h2>Component List</h2>
            <div class="filter-section">
                <input type="text" class="search-input" placeholder="Search components..." onkeyup="filterComponents(this.value)">
                <select class="sort-select" onchange="sortComponents(this.value)">
                    <option value="confidence">Sort by Confidence</option>
                    <option value="type">Sort by Type</option>
                </select>
            </div>
            <div id="componentList"></div>
        </div>
    </div>
    <div class="main-content">
        <div class="container">
            <img src="{image_base64}" class="image" id="mainImage">
            {self._generate_overlay_html(detections)}
        </div>
    </div>

    <script>
        const data = {json.dumps(js_data, indent=2)};
        
        function initializeVisualization() {{
            updateStats();
            updateComponentList();
            setupEventListeners();
        }}
        
        function updateStats() {{
            const statsContent = document.getElementById('statsContent');
            const stats = data.stats;
            
            let html = `
                <div class="stat-item">
                    <span class="stat-label">Total Components:</span>
                    <span class="stat-value">${{stats.total_components}}</span>
                </div>
            `;
            
            for (const [type, count] of Object.entries(stats.by_type)) {{
                html += `
                    <div class="stat-item">
                        <span class="stat-label">${{type}}:</span>
                        <span class="stat-value">${{count}}</span>
                    </div>
                `;
            }}
            
            if (stats.total_components > 0) {{
                html += `
                    <div class="stat-item">
                        <span class="stat-label">Avg Confidence:</span>
                        <span class="stat-value">${{(stats.confidence_stats.average * 100).toFixed(1)}}%</span>
                    </div>
                `;
            }}
            
            statsContent.innerHTML = html;
        }}
        
        function updateComponentList() {{
            const componentList = document.getElementById('componentList');
            let html = '';
            
            data.detections.forEach(detection => {{
                const confidencePercent = (detection.confidence * 100).toFixed(1);
                html += `
                    <div class="component-item" data-id="${{detection.id}}" onclick="highlightComponent(${{detection.id}})">
                        <div class="component-name">${{detection.class_name}} #${{detection.id}}</div>
                        <div class="component-confidence">Confidence: ${{confidencePercent}}%</div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${{confidencePercent}}%"></div>
                        </div>
                    </div>
                `;
            }});
            
            componentList.innerHTML = html;
        }}
        
        function highlightComponent(id) {{
            // Remove previous highlights
            document.querySelectorAll('.overlay, .component-item').forEach(el => {{
                el.classList.remove('highlight');
            }});
            
            // Add highlight to selected component
            const overlay = document.querySelector(`[data-detection-id="${{id}}"]`);
            const listItem = document.querySelector(`[data-id="${{id}}"]`);
            
            if (overlay) overlay.classList.add('highlight');
            if (listItem) listItem.classList.add('highlight');
        }}
        
        function filterComponents(searchTerm) {{
            const items = document.querySelectorAll('.component-item');
            items.forEach(item => {{
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm.toLowerCase())) {{
                    item.style.display = 'block';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }}
        
        function sortComponents(sortBy) {{
            const container = document.getElementById('componentList');
            const items = Array.from(container.children);
            
            items.sort((a, b) => {{
                if (sortBy === 'confidence') {{
                    const aConf = parseFloat(a.querySelector('.component-confidence').textContent.match(/([0-9.]+)%/)[1]);
                    const bConf = parseFloat(b.querySelector('.component-confidence').textContent.match(/([0-9.]+)%/)[1]);
                    return bConf - aConf;
                }} else if (sortBy === 'type') {{
                    const aType = a.querySelector('.component-name').textContent;
                    const bType = b.querySelector('.component-name').textContent;
                    return aType.localeCompare(bType);
                }}
                return 0;
            }});
            
            items.forEach(item => container.appendChild(item));
        }}
        
        function setupEventListeners() {{
            // Tooltip functionality
            const overlays = document.querySelectorAll('.overlay');
            overlays.forEach(overlay => {{
                overlay.addEventListener('mouseenter', showTooltip);
                overlay.addEventListener('mouseleave', hideTooltip);
                overlay.addEventListener('mousemove', moveTooltip);
            }});
        }}
        
        function showTooltip(event) {{
            const overlay = event.target;
            const id = overlay.getAttribute('data-detection-id');
            const detection = data.detections.find(d => d.id == id);
            
            if (detection) {{
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.id = 'tooltip';
                tooltip.innerHTML = `
                    <strong>${{detection.class_name}} #${{detection.id}}</strong><br>
                    Confidence: ${{(detection.confidence * 100).toFixed(1)}}%<br>
                    Area: ${{detection.area}} px²
                `;
                document.body.appendChild(tooltip);
            }}
        }}
        
        function hideTooltip() {{
            const tooltip = document.getElementById('tooltip');
            if (tooltip) {{
                tooltip.remove();
            }}
        }}
        
        function moveTooltip(event) {{
            const tooltip = document.getElementById('tooltip');
            if (tooltip) {{
                tooltip.style.left = (event.pageX + 10) + 'px';
                tooltip.style.top = (event.pageY - 10) + 'px';
            }}
        }}
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', initializeVisualization);
    </script>
</body>
</html>
        """
        
        return html_template

    def _generate_overlay_css(self, detections: List[Dict[str, Any]], image_dimensions: Dict[str, int]) -> str:
        """Generate CSS for detection overlays"""
        css = ""

        for detection in detections:
            detection_id = detection['id']
            bbox = detection['bbox']

            # Calculate percentages for responsive positioning
            if isinstance(bbox, dict):
                x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
            else:
                x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

            width_percent = ((x2 - x1) / image_dimensions['width']) * 100
            height_percent = ((y2 - y1) / image_dimensions['height']) * 100
            left_percent = (x1 / image_dimensions['width']) * 100
            top_percent = (y1 / image_dimensions['height']) * 100

            css += f"""
        .overlay-{detection_id} {{
            left: {left_percent:.2f}%;
            top: {top_percent:.2f}%;
            width: {width_percent:.2f}%;
            height: {height_percent:.2f}%;
        }}
            """

        return css

    def _generate_overlay_html(self, detections: List[Dict[str, Any]]) -> str:
        """Generate HTML for detection overlays"""
        html = ""

        for detection in detections:
            detection_id = detection['id']
            class_name = detection['class_name']
            confidence = detection['confidence']

            html += f"""
            <div class="overlay overlay-{detection_id}"
                 data-detection-id="{detection_id}"
                 onclick="highlightComponent({detection_id})">
            </div>
            """

        return html

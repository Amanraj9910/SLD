"""
Interactive Text Detection Viewer
Provides interactive visualization for text detection results.
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class InteractiveTextViewer:
    """Interactive viewer for text detection results."""
    
    def __init__(self, output_dir: str = "text_detection/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_interactive_html(self, 
                              image_path: str, 
                              detection_results: Dict[str, Any],
                              output_filename: Optional[str] = None) -> str:
        """Create interactive HTML visualization."""
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"text_detection_interactive_{timestamp}.html"
        
        output_path = self.output_dir / output_filename
        
        # Read and encode image
        image_data = self._encode_image(image_path)
        
        # Generate HTML
        html_content = self._generate_html_template(image_data, detection_results)
        
        # Save HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image as base64 for embedding in HTML."""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Determine image type
            ext = Path(image_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif ext == '.png':
                mime_type = 'image/png'
            else:
                mime_type = 'image/png'  # Default
            
            encoded = base64.b64encode(image_data).decode('utf-8')
            return f"data:{mime_type};base64,{encoded}"
            
        except Exception as e:
            print(f"Error encoding image: {e}")
            return ""
    
    def _generate_html_template(self, image_data: str, results: Dict[str, Any]) -> str:
        """Generate HTML template with interactive features."""
        
        # Extract text blocks
        text_blocks = results.get('text_blocks', [])
        full_text = results.get('text', '')
        metadata = results.get('metadata', {})
        
        # Generate text block overlays
        overlays_html = ""
        for i, block in enumerate(text_blocks):
            bbox = block.get('bbox', [0, 0, 100, 100])
            text = block.get('text', '').replace('"', '&quot;').replace("'", "&#39;")
            confidence = block.get('confidence', 0)
            
            overlays_html += f"""
            <div class="text-overlay" 
                 style="left: {bbox[0]}px; top: {bbox[1]}px; 
                        width: {bbox[2] - bbox[0]}px; height: {bbox[3] - bbox[1]}px;"
                 data-text="{text}"
                 data-confidence="{confidence:.2f}"
                 data-block-id="{i}">
            </div>
            """
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Text Detection Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: #2563eb;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .content {{
            display: flex;
            min-height: 600px;
        }}
        
        .image-panel {{
            flex: 1;
            position: relative;
            background: #f8f9fa;
            overflow: auto;
            border-right: 1px solid #e5e7eb;
        }}
        
        .image-container {{
            position: relative;
            display: inline-block;
            margin: 20px;
        }}
        
        .main-image {{
            max-width: 100%;
            height: auto;
            border: 1px solid #d1d5db;
            border-radius: 4px;
        }}
        
        .text-overlay {{
            position: absolute;
            border: 2px solid #ef4444;
            background: rgba(239, 68, 68, 0.1);
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .text-overlay:hover {{
            background: rgba(239, 68, 68, 0.3);
            border-color: #dc2626;
            z-index: 10;
        }}
        
        .text-overlay.selected {{
            background: rgba(34, 197, 94, 0.3);
            border-color: #16a34a;
            z-index: 10;
        }}
        
        .text-panel {{
            width: 400px;
            background: white;
            display: flex;
            flex-direction: column;
        }}
        
        .tabs {{
            display: flex;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .tab {{
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }}
        
        .tab.active {{
            border-bottom-color: #2563eb;
            color: #2563eb;
            font-weight: 600;
        }}
        
        .tab-content {{
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }}
        
        .tab-panel {{
            display: none;
        }}
        
        .tab-panel.active {{
            display: block;
        }}
        
        .text-block {{
            margin-bottom: 15px;
            padding: 10px;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .text-block:hover {{
            border-color: #2563eb;
            background: #f8fafc;
        }}
        
        .text-block.selected {{
            border-color: #16a34a;
            background: #f0fdf4;
        }}
        
        .block-text {{
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .block-info {{
            font-size: 12px;
            color: #6b7280;
        }}
        
        .full-text {{
            line-height: 1.6;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
        }}
        
        .metadata {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
        }}
        
        .metadata-item {{
            margin-bottom: 8px;
        }}
        
        .metadata-label {{
            font-weight: 600;
            color: #374151;
        }}
        
        .controls {{
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
            background: #f8f9fa;
        }}
        
        .control-group {{
            margin-bottom: 10px;
        }}
        
        .control-label {{
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 5px;
        }}
        
        .control-input {{
            width: 100%;
            padding: 5px;
            border: 1px solid #d1d5db;
            border-radius: 3px;
        }}
        
        .btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        .btn:hover {{
            background: #1d4ed8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 Interactive Text Detection Results</h1>
            <p>Click on text regions to highlight them. Use the panel on the right to explore detected text.</p>
        </div>
        
        <div class="content">
            <div class="image-panel">
                <div class="image-container">
                    <img src="{image_data}" alt="Analyzed Document" class="main-image" id="mainImage">
                    {overlays_html}
                </div>
            </div>
            
            <div class="text-panel">
                <div class="controls">
                    <div class="control-group">
                        <label class="control-label">Confidence Threshold</label>
                        <input type="range" class="control-input" id="confidenceSlider" 
                               min="0" max="1" step="0.1" value="0.5">
                        <span id="confidenceValue">0.5</span>
                    </div>
                    <button class="btn" onclick="exportResults()">Export Results</button>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('blocks')">Text Blocks</div>
                    <div class="tab" onclick="switchTab('full')">Full Text</div>
                    <div class="tab" onclick="switchTab('metadata')">Metadata</div>
                </div>
                
                <div class="tab-content">
                    <div class="tab-panel active" id="blocks-panel">
                        <div id="textBlocks">
                            {self._generate_text_blocks_html(text_blocks)}
                        </div>
                    </div>
                    
                    <div class="tab-panel" id="full-panel">
                        <div class="full-text">{full_text}</div>
                    </div>
                    
                    <div class="tab-panel" id="metadata-panel">
                        <div class="metadata">
                            {self._generate_metadata_html(metadata)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedBlock = null;
        
        // Tab switching
        function switchTab(tabName) {{
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName + '-panel').classList.add('active');
        }}
        
        // Block selection
        document.querySelectorAll('.text-overlay').forEach(overlay => {{
            overlay.addEventListener('click', function() {{
                selectBlock(this.dataset.blockId);
            }});
        }});
        
        document.querySelectorAll('.text-block').forEach(block => {{
            block.addEventListener('click', function() {{
                selectBlock(this.dataset.blockId);
            }});
        }});
        
        function selectBlock(blockId) {{
            // Clear previous selection
            document.querySelectorAll('.text-overlay.selected').forEach(el => 
                el.classList.remove('selected'));
            document.querySelectorAll('.text-block.selected').forEach(el => 
                el.classList.remove('selected'));
            
            // Select new block
            const overlay = document.querySelector(`[data-block-id="${{blockId}}"]`);
            const textBlock = document.querySelector(`.text-block[data-block-id="${{blockId}}"]`);
            
            if (overlay) overlay.classList.add('selected');
            if (textBlock) {{
                textBlock.classList.add('selected');
                textBlock.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
            
            selectedBlock = blockId;
        }}
        
        // Confidence filtering
        document.getElementById('confidenceSlider').addEventListener('input', function() {{
            const threshold = parseFloat(this.value);
            document.getElementById('confidenceValue').textContent = threshold.toFixed(1);
            
            document.querySelectorAll('.text-overlay').forEach(overlay => {{
                const confidence = parseFloat(overlay.dataset.confidence);
                overlay.style.display = confidence >= threshold ? 'block' : 'none';
            }});
            
            document.querySelectorAll('.text-block').forEach(block => {{
                const confidence = parseFloat(block.dataset.confidence);
                block.style.display = confidence >= threshold ? 'block' : 'none';
            }});
        }});
        
        // Export functionality
        function exportResults() {{
            const results = {{
                timestamp: new Date().toISOString(),
                selectedBlock: selectedBlock,
                confidenceThreshold: document.getElementById('confidenceSlider').value,
                textBlocks: {json.dumps(text_blocks)},
                fullText: {json.dumps(full_text)},
                metadata: {json.dumps(metadata)}
            }};
            
            const blob = new Blob([JSON.stringify(results, null, 2)], 
                                {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'text_detection_results.json';
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _generate_text_blocks_html(self, text_blocks: List[Dict[str, Any]]) -> str:
        """Generate HTML for text blocks list."""
        html = ""
        for i, block in enumerate(text_blocks):
            text = block.get('text', '').replace('<', '&lt;').replace('>', '&gt;')
            confidence = block.get('confidence', 0)
            bbox = block.get('bbox', [0, 0, 0, 0])
            
            html += f"""
            <div class="text-block" data-block-id="{i}" data-confidence="{confidence:.2f}">
                <div class="block-text">{text}</div>
                <div class="block-info">
                    Confidence: {confidence:.2f} | 
                    Position: ({bbox[0]}, {bbox[1]}) | 
                    Size: {bbox[2] - bbox[0]}×{bbox[3] - bbox[1]}
                </div>
            </div>
            """
        
        return html
    
    def _generate_metadata_html(self, metadata: Dict[str, Any]) -> str:
        """Generate HTML for metadata display."""
        html = ""
        for key, value in metadata.items():
            html += f"""
            <div class="metadata-item">
                <span class="metadata-label">{key}:</span> {value}
            </div>
            """
        
        return html

def create_interactive_viewer(image_path: str, 
                            detection_results: Dict[str, Any],
                            output_dir: str = "text_detection/outputs") -> str:
    """Convenience function to create interactive viewer."""
    viewer = InteractiveTextViewer(output_dir)
    return viewer.create_interactive_html(image_path, detection_results)

if __name__ == "__main__":
    # Example usage
    sample_results = {
        "text": "Sample detected text\\nMultiple lines\\nWith various content",
        "text_blocks": [
            {
                "text": "Sample detected text",
                "confidence": 0.95,
                "bbox": [100, 50, 300, 80]
            },
            {
                "text": "Multiple lines",
                "confidence": 0.87,
                "bbox": [100, 90, 250, 120]
            }
        ],
        "metadata": {
            "processing_time": "2.3s",
            "total_blocks": 2,
            "average_confidence": 0.91
        }
    }
    
    # This would create an interactive viewer
    # viewer_path = create_interactive_viewer("sample_image.png", sample_results)
    # print(f"Interactive viewer created: {viewer_path}")

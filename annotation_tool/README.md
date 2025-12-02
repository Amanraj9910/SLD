# Annotation Tool Module

Manual labeling interface for Single Line Diagram (SLD) component annotation.

## 🎯 Overview

This module provides a comprehensive web-based annotation tool for manually labeling electrical components in SLD diagrams. It features canvas-based bounding box drawing, component category management, and YOLO format export capabilities.

## 🔧 Features

### Interactive Canvas
- **Canvas-based Drawing**: Click and drag to create bounding boxes
- **Real-time Editing**: Resize and move existing annotations
- **Visual Feedback**: Color-coded boxes with class labels
- **Zoom Controls**: Zoom in/out for precise annotation

### Component Management
- **10 Component Classes**: Circuit breakers, fuses, isolators, etc.
- **Dropdown Selection**: Easy class assignment and modification
- **Visual Statistics**: Real-time annotation counts
- **Validation**: Automatic coordinate and size validation

### Project Management
- **Save/Load Projects**: JSON-based project persistence
- **YOLO Export**: Direct export to YOLO training format
- **Batch Operations**: Clear all, import/export functionality
- **File Upload**: Drag-and-drop image loading

## 📁 Module Structure

```
annotation_tool/
├── annotator.py                    # Backend annotation manager
├── static/                         # Frontend assets
│   └── annotation_canvas.js       # Canvas drawing logic
├── templates/                      # HTML templates
│   └── annotation_interface.html  # Main annotation interface
├── tests/                          # Unit tests
│   └── test_annotator.py
└── README.md                      # This file
```

## 🚀 Quick Start

### Backend Usage

```python
from annotation_tool.annotator import AnnotationManager

# Initialize annotation manager
manager = AnnotationManager()

# Create new project
project = manager.create_project(
    image_path="sld_diagram.jpg",
    project_name="my_sld_project",
    created_by="user"
)

# Add annotations
manager.add_annotation(
    class_id=0,  # CIRCUIT_BREAKER
    bbox=(0.5, 0.3, 0.1, 0.15),  # (x_center, y_center, width, height) normalized
    confidence=1.0
)

# Save project
manager.save_project()

# Export to YOLO format
manager.export_yolo_format("output_dir/")
```

### Web Interface Usage

1. **Open Interface**: Open `templates/annotation_interface.html` in browser
2. **Upload Image**: Drag and drop or click to upload SLD image
3. **Create Annotations**: Click and drag on image to draw bounding boxes
4. **Select Class**: Choose component type from dropdown
5. **Edit Annotations**: Click to select, drag to move, use handles to resize
6. **Save Project**: Export project as JSON file
7. **Export YOLO**: Export annotations in YOLO training format

### Coordinate System

The annotation tool uses normalized YOLO coordinates:
- **x_center**: Horizontal center (0.0 to 1.0)
- **y_center**: Vertical center (0.0 to 1.0)  
- **width**: Box width (0.0 to 1.0)
- **height**: Box height (0.0 to 1.0)

## 🎨 Component Classes

| ID | Class Name | Description |
|----|------------|-------------|
| 0 | CIRCUIT_BREAKER | Main protection devices |
| 1 | HRC_FUSE | High Rupturing Capacity fuses |
| 2 | ISOLATOR | Switching devices for isolation |
| 3 | CABLE_TERMINATION_BOX | Cable connection points |
| 4 | SINGLE_PHASE_TAP_OFF_UNIT | Distribution components |
| 5 | TRANSFORMER | Voltage transformation devices |
| 6 | MOTOR | Electric motors |
| 7 | GENERATOR | Power generation devices |
| 8 | SWITCH | General switching devices |
| 9 | RELAY | Protection and control relays |

## 📊 File Formats

### Project Format (JSON)
```json
{
  "project_name": "my_sld_project",
  "image_path": "sld_diagram.jpg",
  "image_dimensions": [1280, 720],
  "annotations": [
    {
      "class_id": 0,
      "class_name": "CIRCUIT_BREAKER",
      "bbox": [0.5, 0.3, 0.1, 0.15],
      "confidence": 1.0,
      "annotator": "manual"
    }
  ],
  "class_names": {
    "0": "CIRCUIT_BREAKER",
    "1": "HRC_FUSE"
  },
  "created_by": "user",
  "last_modified": "2024-07-16T10:30:00Z"
}
```

### YOLO Format Export
```
# annotations.txt
0 0.5 0.3 0.1 0.15
1 0.7 0.6 0.08 0.12

# classes.txt
CIRCUIT_BREAKER
HRC_FUSE
ISOLATOR
```

## 🧪 Testing

### Run Unit Tests
```bash
cd annotation_tool
python -m pytest tests/ -v
```

### Test Web Interface
```bash
# Open in browser
open templates/annotation_interface.html

# Or serve with Python
python -m http.server 8080
# Then visit http://localhost:8080/templates/annotation_interface.html
```

### Manual Testing Checklist
- [ ] Image upload (drag & drop and file picker)
- [ ] Bounding box creation (click and drag)
- [ ] Box selection and editing
- [ ] Class assignment and modification
- [ ] Project save/load functionality
- [ ] YOLO format export
- [ ] Zoom and pan controls
- [ ] Keyboard shortcuts (Delete, Escape)

## 🔧 Advanced Usage

### Custom Class Names
```python
# Define custom component classes
custom_classes = {
    0: "CUSTOM_BREAKER",
    1: "CUSTOM_FUSE",
    2: "CUSTOM_SWITCH"
}

manager = AnnotationManager(class_names=custom_classes)
```

### Batch Import from YOLO
```python
# Import existing YOLO annotations
project = manager.import_yolo_format(
    annotations_file="labels.txt",
    image_path="image.jpg",
    classes_file="classes.txt",
    project_name="imported_project"
)
```

### Validation and Quality Control
```python
# Validate annotations
issues = manager.validate_annotations()

print("Errors:", issues["errors"])
print("Warnings:", issues["warnings"])
print("Info:", issues["info"])

# Get statistics
stats = manager.get_annotation_statistics()
print(f"Total annotations: {stats['total']}")
print(f"Classes used: {stats['classes_used']}")
print(f"Average confidence: {stats['avg_confidence']:.3f}")
```

### Coordinate Conversion Utilities
```python
from annotation_tool.annotator import yolo_to_pixel, pixel_to_yolo

# Convert YOLO to pixel coordinates
pixel_coords = yolo_to_pixel(
    bbox=(0.5, 0.3, 0.1, 0.15),
    image_width=1280,
    image_height=720
)
# Returns: (576, 162, 704, 270)

# Convert pixel to YOLO coordinates  
yolo_coords = pixel_to_yolo(
    bbox=(576, 162, 704, 270),
    image_width=1280,
    image_height=720
)
# Returns: (0.5, 0.3, 0.1, 0.15)
```

## 🎮 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Delete** | Delete selected annotation |
| **Escape** | Deselect current annotation |
| **Click** | Select annotation |
| **Drag** | Create new annotation |
| **Drag handles** | Resize selected annotation |
| **Drag box** | Move selected annotation |

## 🔧 Troubleshooting

### Common Issues

**Canvas not responding**
- Check if image is loaded properly
- Verify canvas initialization
- Check browser console for JavaScript errors

**Annotations not saving**
- Ensure project name is set
- Check file permissions for save location
- Verify JSON format validity

**Coordinate conversion errors**
- Ensure image dimensions are correct
- Check for normalized coordinate ranges (0-1)
- Validate bounding box format

**Import/export issues**
- Verify file format compatibility
- Check class ID mappings
- Ensure proper file encoding (UTF-8)

### Performance Optimization

**Large Images**
- Use image resizing for display
- Implement canvas virtualization for very large images
- Consider tiling for extremely high-resolution images

**Many Annotations**
- Implement pagination for annotation list
- Use spatial indexing for selection
- Optimize redraw operations

## 📋 Requirements

- Python 3.8+ (backend)
- Modern web browser with Canvas support
- JavaScript enabled
- File system access for save/load operations

## 🤝 Integration

This module integrates with:
- **Component Detection**: Import predicted annotations for verification
- **Text Detection**: Overlay text results for context
- **Web App Backend**: REST API for annotation management
- **Training Pipeline**: Direct YOLO format export for model training

## 📄 API Reference

### Classes

#### `AnnotationManager`
Main class for managing annotation projects and operations.

#### `Annotation`
Data class representing individual component annotations.

#### `AnnotationProject`
Data class representing complete annotation projects.

### Methods

#### `create_project()`
Create new annotation project from image.

#### `load_project()`
Load existing project from JSON file.

#### `save_project()`
Save project to JSON file.

#### `add_annotation()`
Add new annotation to current project.

#### `export_yolo_format()`
Export annotations in YOLO training format.

#### `import_yolo_format()`
Import annotations from YOLO format files.

#### `validate_annotations()`
Validate annotation data and return issues.

### Utility Functions

#### `yolo_to_pixel()`
Convert YOLO coordinates to pixel coordinates.

#### `pixel_to_yolo()`
Convert pixel coordinates to YOLO format.

## 📊 Performance Metrics

- **Annotation Speed**: ~30-60 seconds per component (manual)
- **File Size**: ~1-5KB per 100 annotations (JSON)
- **Browser Support**: Chrome 80+, Firefox 75+, Safari 13+
- **Image Support**: JPG, PNG, BMP, TIFF up to 50MB

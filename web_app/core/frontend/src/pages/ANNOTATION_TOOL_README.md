# Interactive SLD Annotation Tool

## Overview
The Interactive SLD Annotation Tool allows users to create manual annotations for Single Line Diagram (SLD) images. This tool provides a comprehensive interface for drawing bounding boxes around electrical components and exporting the annotation data.

## Features

### Main Gallery View
- **Left Sidebar Gallery**: Displays all previously annotated images with thumbnails
- **Download Options**: For each project, download both the annotated image and JSON annotation file
- **Project Management**: View project details, creation dates, and annotation counts

### Interactive Annotation Interface
When working on a project, the interface provides:

#### Left Control Panel (Collapsible)
- **Add New Box Button**: Switch to rectangle drawing mode
- **Component Naming Interface**:
  - Dropdown menu for selecting existing component types
  - "Add New Component" functionality for custom component names
  - Dynamic component list that updates with new additions
- **Tool Selection**:
  - Select: Click to select existing annotations
  - Rectangle: Draw new annotation boxes
  - Move: Pan around the image
- **Coordinate Display**: Shows position and dimensions of selected annotations
- **Export Functionality**: Download annotation data as JSON
- **Collapsible Design**: Hide/show panel for full-screen annotation

#### Right Image Canvas
- **Interactive Canvas**: Main workspace for annotation
- **Zoom Controls**: Zoom in/out while maintaining annotation integrity
- **Annotation Boxes**:
  - Draggable and resizable
  - Thin, light-colored borders that scale with zoom
  - Visual feedback for selected annotations
  - Component labels displayed above boxes

## How to Use

### Creating a New Project
1. Enter a project name
2. Upload an SLD image file
3. Click "Create Project" to start annotating

### Adding Annotations
1. Click "Add New Box" in the left panel
2. Select or add a component type from the dropdown
3. Draw rectangles around components by clicking and dragging on the image
4. Use the Select tool to modify existing annotations

### Managing Annotations
- Click on any annotation to select it
- View coordinates and dimensions in the left panel
- Delete selected annotations using the Delete button
- Modify component types by selecting and changing the dropdown

### Exporting Data
- **Save Project**: Saves current annotations to the gallery
- **Export JSON**: Downloads annotation data including:
  - Project metadata
  - Image dimensions
  - All annotation coordinates and component information
  - Timestamp information

### Navigation
- Use zoom controls to get detailed views
- Pan around large images using the Move tool
- Collapse the left panel for maximum canvas space
- Return to gallery view to access other projects

## Technical Features

### Responsive Design
- Adapts to different screen sizes
- Touch-friendly interface for tablet use
- Keyboard shortcuts for common actions

### Data Format
Exported JSON includes:
```json
{
  "projectName": "Project Name",
  "imagePath": "/path/to/image",
  "imageDimensions": { "width": 1920, "height": 1080 },
  "annotations": [
    {
      "id": "annotation_123456789",
      "componentName": "Circuit Breaker",
      "componentType": "Circuit Breaker",
      "coordinates": {
        "x": 100,
        "y": 150,
        "width": 80,
        "height": 60
      }
    }
  ],
  "exportedAt": "2024-01-01T12:00:00.000Z"
}
```

### Component Types
Default component types include:
- Circuit Breaker
- HRC Fuse
- Isolator
- Contactor
- Relay
- Transformer
- Motor
- Generator
- Capacitor
- Resistor

Custom component types can be added dynamically during annotation.

## Tips for Best Results

1. **Zoom In**: Use zoom for precise annotation of small components
2. **Consistent Naming**: Use the dropdown to maintain consistent component naming
3. **Regular Saving**: Save your work frequently to prevent data loss
4. **Logical Grouping**: Group similar components with consistent naming
5. **Quality Control**: Review annotations before final export

## Keyboard Shortcuts
- **Escape**: Deselect current annotation
- **Delete**: Remove selected annotation
- **Enter**: Confirm new component name input

## Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge

## File Format Support
- **Input**: JPG, PNG, GIF, BMP, WebP
- **Output**: JSON annotation files, original image format

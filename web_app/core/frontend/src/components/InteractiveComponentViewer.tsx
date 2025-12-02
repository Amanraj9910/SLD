import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Search, ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff, Download, Menu, X, Home, ChevronRight, Zap } from 'lucide-react';

interface ComponentDetection {
  class_name: string;
  confidence: number;
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  center: {
    x: number;
    y: number;
  };
  area: number;
}

interface InteractiveComponentViewerProps {
  imageUrl: string;
  detections: ComponentDetection[];
  imageDimensions?: {
    width: number;
    height: number;
  };
  onClose?: () => void;
}

const InteractiveComponentViewer: React.FC<InteractiveComponentViewerProps> = ({
  imageUrl,
  detections,
  imageDimensions,
  onClose
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedElement, setSelectedElement] = useState<number | null>(null);
  const [hoveredElement, setHoveredElement] = useState<number | null>(null);
  const [showOverlays, setShowOverlays] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Confidence threshold for filtering (25%)
  const CONFIDENCE_THRESHOLD = 0.25;

  // Filter detections based on confidence threshold and search term
  const filteredDetections = detections.filter(detection =>
    detection &&
    detection.class_name &&
    detection.bbox &&
    detection.confidence >= CONFIDENCE_THRESHOLD &&
    detection.class_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    const conf = confidence || 0;
    if (conf >= 0.9) return '#10B981'; // Green
    if (conf >= 0.7) return '#F59E0B'; // Yellow
    if (conf >= 0.5) return '#EF4444'; // Red
    return '#6B7280'; // Gray
  };

  // Find element at coordinates (only consider filtered detections)
  const findElementAtCoordinates = (x: number, y: number) => {
    for (let i = detections.length - 1; i >= 0; i--) {
      const detection = detections[i];
      if (!detection.bbox || detection.confidence < CONFIDENCE_THRESHOLD) continue;

      const bbox = detection.bbox;
      if (x >= bbox.x1 && x <= bbox.x2 && y >= bbox.y1 && y <= bbox.y2) {
        return i;
      }
    }
    return null;
  };

  // Draw overlays on canvas
  const drawOverlays = useCallback(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // If overlays are hidden, only draw subtle hover/selection indicators
    if (!showOverlays) {
      // Only draw indicators for hovered or selected elements (with confidence filtering)
      detections.forEach((detection, index) => {
        const isSelected = selectedElement === index;
        const isHovered = hoveredElement === index;

        if (!isSelected && !isHovered) return;
        if (detection.confidence < CONFIDENCE_THRESHOLD) return;

        const bbox = detection.bbox;
        if (!bbox) return;

        const x = bbox.x1;
        const y = bbox.y1;
        const width = bbox.x2 - bbox.x1;
        const height = bbox.y2 - bbox.y1;

        // Draw subtle outline for interaction feedback - GREEN for selected
        ctx.strokeStyle = isSelected ? '#10B981' : '#6b7280'; // Green for selected, gray for hovered
        ctx.lineWidth = isSelected ? 3 : 1;
        ctx.setLineDash(isSelected ? [] : [5, 5]);
        ctx.strokeRect(x, y, width, height);
        ctx.setLineDash([]); // Reset line dash

        // Draw label for selected/hovered elements
        if (isSelected || isHovered) {
          const label = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;

          ctx.font = '12px Arial';
          const textMetrics = ctx.measureText(label);
          const textWidth = textMetrics.width;
          const textHeight = 16;

          // Semi-transparent background for text
          ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
          ctx.fillRect(x, y - textHeight - 2, textWidth + 8, textHeight + 4);

          // Text
          ctx.fillStyle = '#fff';
          ctx.fillText(label, x + 4, y - 4);
        }
      });
      return;
    }

    detections.forEach((detection, index) => {
      const isSelected = selectedElement === index;
      const isHovered = hoveredElement === index;
      const isFiltered = filteredDetections.includes(detection);

      // Skip if below confidence threshold
      if (detection.confidence < CONFIDENCE_THRESHOLD) return;

      // Skip if not matching search filter
      if (!isFiltered && searchTerm) return;

      const color = getConfidenceColor(detection.confidence);

      // Set style based on state - GREEN for selected components
      ctx.strokeStyle = isSelected ? '#10B981' : color; // Green for selected, confidence color for others
      ctx.lineWidth = isSelected ? 4 : isHovered ? 2 : 1; // Thicker border for selected
      ctx.fillStyle = isSelected ? '#10B98120' : isHovered ? `${color}20` : `${color}10`;

      // Draw bounding box
      const bbox = detection.bbox;
      if (!bbox) return;

      const x = bbox.x1;
      const y = bbox.y1;
      const width = bbox.x2 - bbox.x1;
      const height = bbox.y2 - bbox.y1;

      // Fill rectangle
      ctx.fillRect(x, y, width, height);
      
      // Stroke rectangle
      ctx.strokeRect(x, y, width, height);

      // Draw label
      if (isSelected || isHovered) {
        const label = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;
        
        ctx.font = '12px Arial';
        ctx.fillStyle = '#000';
        const textMetrics = ctx.measureText(label);
        const textWidth = textMetrics.width;
        const textHeight = 16;

        // Background for text
        ctx.fillStyle = color;
        ctx.fillRect(x, y - textHeight - 2, textWidth + 8, textHeight + 4);

        // Text
        ctx.fillStyle = '#fff';
        ctx.fillText(label, x + 4, y - 4);
      }
    });
  }, [detections, selectedElement, hoveredElement, showOverlays, searchTerm, filteredDetections]);

  // Handle image load
  const handleImageLoad = () => {
    const image = imageRef.current;
    const canvas = canvasRef.current;
    if (!image || !canvas) return;

    // Set canvas size to match image
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    canvas.style.width = `${image.offsetWidth}px`;
    canvas.style.height = `${image.offsetHeight}px`;

    drawOverlays();
  };

  // Redraw overlays when dependencies change
  useEffect(() => {
    drawOverlays();
  }, [drawOverlays]);

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    event.stopPropagation();
    event.preventDefault();

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) * (canvas.width / rect.width);
    const y = (event.clientY - rect.top) * (canvas.height / rect.height);

    const elementIndex = findElementAtCoordinates(x, y);

    if (elementIndex !== null) {
      setSelectedElement(elementIndex);
      // Scroll to element in sidebar
      const elementDiv = document.getElementById(`component-element-${elementIndex}`);
      if (elementDiv) {
        elementDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      setSelectedElement(null);
    }
  };

  // Handle canvas mouse leave
  const handleCanvasMouseLeave = () => {
    setHoveredElement(null);
  };

  // Mouse event handlers for pan/zoom
  const handleMouseDown = (event: React.MouseEvent) => {
    if (event.button === 0) { // Left mouse button
      setIsDragging(true);
      setDragStart({ x: event.clientX - pan.x, y: event.clientY - pan.y });
    }
  };

  const handleMouseMoveGlobal = useCallback((event: MouseEvent) => {
    if (isDragging) {
      setPan({
        x: event.clientX - dragStart.x,
        y: event.clientY - dragStart.y
      });
    }
  }, [isDragging, dragStart]);

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleContainerMouseMove = (event: React.MouseEvent) => {
    if (!isDragging) {
      // Handle hover detection
      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      const x = (event.clientX - rect.left) * (canvas.width / rect.width);
      const y = (event.clientY - rect.top) * (canvas.height / rect.height);

      const elementIndex = findElementAtCoordinates(x, y);
      setHoveredElement(elementIndex);
    }
  };

  // Add global mouse move listeners for dragging
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMoveGlobal);
      document.addEventListener('mouseup', handleMouseUp);
    } else {
      document.removeEventListener('mousemove', handleMouseMoveGlobal);
      document.removeEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMoveGlobal);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMoveGlobal]);

  // Zoom functions
  const zoomIn = () => setZoom(prev => Math.min(prev * 1.2, 5));
  const zoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.1));
  const resetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Export functionality
  const exportResults = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      detection_type: 'component',
      total_components: detections.length,
      image_dimensions: imageDimensions,
      detections: detections.map((detection, index) => ({
        id: index + 1,
        component: detection.class_name,
        confidence: Math.round(detection.confidence * 100),
        position: {
          x: detection.bbox.x1,
          y: detection.bbox.y1,
          width: detection.bbox.x2 - detection.bbox.x1,
          height: detection.bbox.y2 - detection.bbox.y1
        },
        center: detection.center,
        area: detection.area
      }))
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `component_detection_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-7xl max-h-[95vh] flex flex-col relative">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-blue-600" />
              Interactive Component Viewer
            </h2>
            
            {/* Breadcrumb */}
            <div className="hidden md:flex items-center text-sm text-gray-500">
              <Home className="w-4 h-4" />
              <ChevronRight className="w-4 h-4 mx-1" />
              <span>Component Detection</span>
              <ChevronRight className="w-4 h-4 mx-1" />
              <span className="text-gray-900">Interactive Viewer</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Desktop controls */}
            <div className="hidden md:flex items-center space-x-2">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
                title="Toggle Sidebar"
              >
                <Menu className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => setShowOverlays(!showOverlays)}
                className={`p-2 rounded-lg transition-colors ${
                  showOverlays
                    ? 'text-blue-600 bg-blue-50 hover:bg-blue-100'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title={showOverlays ? 'Switch to Clean View (hide overlays)' : 'Switch to Full View (show overlays)'}
              >
                {showOverlays ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </button>
              
              <button
                onClick={exportResults}
                className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
                title="Export Results"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-b border-gray-200 p-4 space-y-2">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="w-full flex items-center justify-between p-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              <span>Toggle Sidebar</span>
              <Menu className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowOverlays(!showOverlays)}
              className={`w-full flex items-center justify-between p-2 rounded-lg transition-colors ${
                showOverlays
                  ? 'text-blue-700 bg-blue-50 hover:bg-blue-100'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span>{showOverlays ? 'Switch to Clean View' : 'Switch to Full View'}</span>
              {showOverlays ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>
            <button
              onClick={exportResults}
              className="w-full flex items-center justify-between p-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              <span>Export Results</span>
              <Download className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          {showSidebar && (
            <div className="w-full md:w-80 lg:w-96 border-r border-gray-200 flex flex-col bg-gray-50">
              {/* Controls */}
              <div className="p-4 border-b border-gray-200 bg-white">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Controls</h3>
                  <div className="flex space-x-1">
                    <button
                      onClick={zoomIn}
                      className="p-1 text-gray-600 hover:text-gray-900 rounded"
                      title="Zoom In"
                    >
                      <ZoomIn className="w-4 h-4" />
                    </button>
                    <button
                      onClick={zoomOut}
                      className="p-1 text-gray-600 hover:text-gray-900 rounded"
                      title="Zoom Out"
                    >
                      <ZoomOut className="w-4 h-4" />
                    </button>
                    <button
                      onClick={resetZoom}
                      className="p-1 text-gray-600 hover:text-gray-900 rounded"
                      title="Reset View"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search components..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Component List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0">
                {filteredDetections.map((detection) => {
                  const originalIndex = detections.indexOf(detection);
                  const isSelected = selectedElement === originalIndex;
                  
                  return (
                    <div
                      key={originalIndex}
                      id={`component-element-${originalIndex}`}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedElement(originalIndex)}
                      onMouseEnter={() => setHoveredElement(originalIndex)}
                      onMouseLeave={() => setHoveredElement(null)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900 flex-1">
                          {detection.class_name}
                        </span>
                        <span
                          className="text-xs px-2 py-1 rounded-full text-white ml-2"
                          style={{ backgroundColor: getConfidenceColor(detection.confidence) }}
                        >
                          {(detection.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      
                      <div className="text-xs text-gray-600 space-y-1">
                        <div>Position: ({detection.bbox.x1.toFixed(0)}, {detection.bbox.y1.toFixed(0)})</div>
                        <div>Size: {(detection.bbox.x2 - detection.bbox.x1).toFixed(0)}×{(detection.bbox.y2 - detection.bbox.y1).toFixed(0)}px</div>
                        <div>Area: {detection.area?.toFixed(0) || 'N/A'}px²</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Image Container */}
          <div
            ref={containerRef}
            className="flex-1 overflow-hidden relative cursor-move"
            onMouseDown={handleMouseDown}
            onMouseMove={handleContainerMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <div
              className="relative"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: 'center center',
                transition: isDragging ? 'none' : 'transform 0.1s ease-out'
              }}
            >
              <img
                ref={imageRef}
                src={imageUrl}
                alt="SLD Diagram"
                className="max-w-full max-h-full object-contain"
                onLoad={handleImageLoad}
                draggable={false}
              />
              <canvas
                ref={canvasRef}
                className="absolute top-0 left-0 pointer-events-auto"
                onClick={handleCanvasClick}
                onMouseLeave={handleCanvasMouseLeave}
                style={{
                  cursor: hoveredElement !== null ? 'pointer' : showOverlays ? 'crosshair' : 'default',
                  opacity: showOverlays ? 1 : 0.8
                }}
              />
            </div>
          </div>
        </div>

        {/* Component Name Display - Bottom Right (Desktop) / Bottom Center (Mobile) */}
        {selectedElement !== null && detections[selectedElement] && detections[selectedElement].confidence >= CONFIDENCE_THRESHOLD && (
          <div className="absolute bottom-16 right-4 md:bottom-4 md:right-4 left-4 md:left-auto bg-gray-900 text-white px-4 py-3 rounded-lg shadow-lg border border-gray-700 max-w-xs md:max-w-sm z-10">
            <div className="text-sm font-medium">
              {detections[selectedElement].class_name}
            </div>
            <div className="text-xs text-gray-300 mt-1">
              Confidence: {(detections[selectedElement].confidence * 100).toFixed(1)}%
            </div>
          </div>
        )}

        {/* Status Bar */}
        <div className="p-2 bg-gray-800 text-white text-sm flex justify-between">
          <span>
            {selectedElement !== null
              ? `Selected component displayed in bottom-right corner`
              : showOverlays
                ? 'Click on components to select'
                : 'Clean view mode - hover/click to interact with components'
            }
          </span>
          <span className="flex items-center space-x-4">
            <span className={`px-2 py-1 rounded text-xs ${showOverlays ? 'bg-blue-600' : 'bg-gray-600'}`}>
              {showOverlays ? 'Full View' : 'Clean View'}
            </span>
            <span>
              Showing: {filteredDetections.length} components (≥25% confidence)
            </span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default InteractiveComponentViewer;

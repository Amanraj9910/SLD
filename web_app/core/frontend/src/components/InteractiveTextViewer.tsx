import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Search, ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff, Download, Menu, X, Home, ChevronRight, FileText } from 'lucide-react';

interface TextElement {
  text: string;
  confidence: number;
  polygon: number[][];
  bounding_box: {
    left: number;
    top: number;
    width: number;
    height: number;
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  page_number: number;
  center?: {
    x: number;
    y: number;
  };
  area?: number;
}

interface InteractiveTextViewerProps {
  imageUrl: string;
  textElements: TextElement[];
  imageDimensions?: {
    width: number;
    height: number;
  };
  onClose?: () => void;
}

const InteractiveTextViewer: React.FC<InteractiveTextViewerProps> = ({
  imageUrl,
  textElements,
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

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(320); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);

  // Simple tooltip state
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    text: string;
    confidence: number;
  } | null>(null);


  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Filter text elements based on search term and ensure they have required properties
  const filteredElements = textElements.filter(element =>
    element &&
    element.text &&
    element.bounding_box &&
    element.text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    const conf = confidence || 0;
    if (conf >= 0.9) return '#10B981'; // Green
    if (conf >= 0.7) return '#F59E0B'; // Yellow
    if (conf >= 0.5) return '#EF4444'; // Red
    return '#6B7280'; // Gray
  };

  // Draw overlays on canvas
  const drawOverlays = useCallback(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match image
    canvas.width = image.offsetWidth;
    canvas.height = image.offsetHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // If overlays are hidden, just clear and return
    if (!showOverlays) return;

    // Determine if coordinates are normalized (0-1) or pixel-based
    const referenceWidth = imageDimensions?.width || image.naturalWidth;
    const referenceHeight = imageDimensions?.height || image.naturalHeight;

    // Check if coordinates appear to be normalized by looking at first element
    const firstElement = textElements[0];
    const isNormalized = firstElement?.bounding_box &&
      (firstElement.bounding_box.left <= 1 && firstElement.bounding_box.top <= 1 &&
        firstElement.bounding_box.width <= 1 && firstElement.bounding_box.height <= 1);

    console.log('Coordinate system detection:', {
      referenceWidth,
      referenceHeight,
      isNormalized,
      firstElementBbox: firstElement?.bounding_box,
      imageDisplaySize: { width: image.offsetWidth, height: image.offsetHeight },
      imageNaturalSize: { width: image.naturalWidth, height: image.naturalHeight }
    });

    // Calculate scale factors - if normalized, scale to display size; otherwise scale from reference to display
    const scaleX = isNormalized ? image.offsetWidth : image.offsetWidth / referenceWidth;
    const scaleY = isNormalized ? image.offsetHeight : image.offsetHeight / referenceHeight;

    console.log('Drawing overlays:', {
      imageOffsetWidth: image.offsetWidth,
      imageOffsetHeight: image.offsetHeight,
      imageNaturalWidth: image.naturalWidth,
      imageNaturalHeight: image.naturalHeight,
      imageDimensions,
      scaleX,
      scaleY,
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      totalElements: textElements.length
    });

    textElements.forEach((element, index) => {
      const isSelected = selectedElement === index;
      const isHovered = hoveredElement === index;
      const isFiltered = filteredElements.includes(element);

      if (!isFiltered && searchTerm) return;

      const color = getConfidenceColor(element.confidence);

      // Set style based on state
      ctx.strokeStyle = color;
      ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;
      ctx.fillStyle = isSelected || isHovered ? `${color}20` : `${color}10`;

      // Draw bounding box
      const bbox = element.bounding_box;
      if (!bbox) {
        console.warn(`Element ${index} has no bounding box:`, element);
        return; // Skip if no bounding box
      }

      // Use x1, y1, x2, y2 coordinates for more accurate positioning
      const x1 = (bbox.x1 || bbox.left || 0) * scaleX;
      const y1 = (bbox.y1 || bbox.top || 0) * scaleY;
      const x2 = (bbox.x2 || (bbox.left + bbox.width) || 0) * scaleX;
      const y2 = (bbox.y2 || (bbox.top + bbox.height) || 0) * scaleY;

      const x = x1;
      const y = y1;
      const width = x2 - x1;
      const height = y2 - y1;

      // Validate coordinates
      if (width <= 0 || height <= 0) {
        console.warn(`Element ${index} has invalid dimensions:`, { width, height, bbox });
        return;
      }

      // Debug first few elements
      if (index < 3) {
        console.log(`Element ${index} (${element.text}):`, {
          originalBbox: bbox,
          scaledCoords: { x, y, width, height },
          scaleFactors: { scaleX, scaleY },
          isNormalized
        });
      }

      ctx.fillRect(x, y, width, height);
      ctx.strokeRect(x, y, width, height);

      // Draw polygon if available
      if (element.polygon && element.polygon.length > 0) {
        ctx.beginPath();
        element.polygon.forEach((point, i) => {
          const px = point[0] * scaleX;
          const py = point[1] * scaleY;
          if (i === 0) {
            ctx.moveTo(px, py);
          } else {
            ctx.lineTo(px, py);
          }
        });
        ctx.closePath();
        ctx.stroke();
      }

      // Draw confidence score for selected/hovered elements
      if (isSelected || isHovered) {
        ctx.fillStyle = color;
        ctx.font = '12px Arial';
        ctx.fillText(
          `${((element.confidence || 0) * 100).toFixed(1)}%`,
          x,
          y - 5
        );
      }
    });
  }, [textElements, selectedElement, hoveredElement, showOverlays, searchTerm, filteredElements, imageDimensions]);

  // Handle image load
  const handleImageLoad = () => {
    drawOverlays();
  };

  // Find element at coordinates
  const findElementAtCoordinates = (x: number, y: number) => {
    const image = imageRef.current;
    if (!image) return null;

    // Use same coordinate system detection as drawOverlays
    const referenceWidth = imageDimensions?.width || image.naturalWidth;
    const referenceHeight = imageDimensions?.height || image.naturalHeight;

    const firstElement = textElements[0];
    const isNormalized = firstElement?.bounding_box &&
      (firstElement.bounding_box.left <= 1 && firstElement.bounding_box.top <= 1 &&
        firstElement.bounding_box.width <= 1 && firstElement.bounding_box.height <= 1);

    const scaleX = isNormalized ? image.offsetWidth : image.offsetWidth / referenceWidth;
    const scaleY = isNormalized ? image.offsetHeight : image.offsetHeight / referenceHeight;

    // Find element at coordinates
    for (let i = 0; i < textElements.length; i++) {
      const element = textElements[i];
      const bbox = element.bounding_box;

      if (!bbox) continue; // Skip if no bounding box

      // Use x1, y1, x2, y2 coordinates for more accurate hit detection
      const x1 = (bbox.x1 || bbox.left || 0) * scaleX;
      const y1 = (bbox.y1 || bbox.top || 0) * scaleY;
      const x2 = (bbox.x2 || (bbox.left + bbox.width) || 0) * scaleX;
      const y2 = (bbox.y2 || (bbox.top + bbox.height) || 0) * scaleY;

      const elementX = x1;
      const elementY = y1;
      const elementWidth = x2 - x1;
      const elementHeight = y2 - y1;

      // Debug first few elements
      if (i < 3) {
        console.log(`Checking element ${i} (${element.text}):`, {
          clickCoords: { x, y },
          elementBounds: { elementX, elementY, elementWidth, elementHeight },
          isInside: x >= elementX && x <= elementX + elementWidth && y >= elementY && y <= elementY + elementHeight
        });
      }

      if (x >= elementX && x <= elementX + elementWidth &&
        y >= elementY && y <= elementY + elementHeight) {
        console.log(`Found element ${i}: ${element.text}`);
        return i;
      }
    }
    return null;
  };

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    // Stop event propagation to prevent conflicts with pan/zoom
    event.stopPropagation();
    event.preventDefault();

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    // Get canvas coordinates (these are already in the transformed space)
    const x = (event.clientX - rect.left) * (canvas.width / rect.width);
    const y = (event.clientY - rect.top) * (canvas.height / rect.height);

    console.log('Canvas click:', {
      x,
      y,
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      rectWidth: rect.width,
      rectHeight: rect.height
    });

    const elementIndex = findElementAtCoordinates(x, y);
    console.log('Found element index:', elementIndex);

    if (elementIndex !== null) {
      setSelectedElement(elementIndex);
      console.log('Selected element:', textElements[elementIndex]);
      // Scroll to element in sidebar
      const elementDiv = document.getElementById(`text-element-${elementIndex}`);
      if (elementDiv) {
        elementDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      // Clear selection if no element clicked
      setSelectedElement(null);
    }
  };

  // Simple container-level hover handler
  const handleContainerMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const canvas = canvasRef.current;
    const image = imageRef.current;

    if (!canvas || !image || textElements.length === 0) {
      setTooltip(null);
      setHoveredElement(null);
      return;
    }

    const canvasRect = canvas.getBoundingClientRect();

    // Check if mouse is over the canvas area
    if (event.clientX >= canvasRect.left && event.clientX <= canvasRect.right &&
      event.clientY >= canvasRect.top && event.clientY <= canvasRect.bottom) {

      // Convert viewport coordinates to canvas coordinates
      const canvasX = (event.clientX - canvasRect.left) * (canvas.width / canvasRect.width);
      const canvasY = (event.clientY - canvasRect.top) * (canvas.height / canvasRect.height);

      const elementIndex = findElementAtCoordinates(canvasX, canvasY);
      setHoveredElement(elementIndex);

      if (elementIndex !== null && textElements[elementIndex]) {
        const element = textElements[elementIndex];

        // Set tooltip with viewport coordinates (should work correctly)
        setTooltip({
          visible: true,
          x: event.clientX,
          y: event.clientY,
          text: element.text,
          confidence: element.confidence || 0
        });

        console.log('NEW TOOLTIP SET:', {
          element: element.text,
          viewportX: event.clientX,
          viewportY: event.clientY,
          canvasX,
          canvasY
        });
      } else {
        setTooltip(null);
      }
    } else {
      // Mouse is outside canvas
      setTooltip(null);
      setHoveredElement(null);
    }
  };

  // Handle canvas mouse leave
  const handleCanvasMouseLeave = (event: React.MouseEvent<HTMLCanvasElement>) => {
    event.stopPropagation();
    setHoveredElement(null);
    setTooltip(null);
  };

  // Handle sidebar resize
  const handleResizeStart = (event: React.MouseEvent) => {
    event.preventDefault();
    setIsResizing(true);
  };

  const handleResizeMove = useCallback((event: MouseEvent) => {
    if (!isResizing) return;

    const newWidth = Math.max(200, Math.min(600, event.clientX));
    setSidebarWidth(newWidth);
  }, [isResizing]);

  const handleResizeEnd = useCallback(() => {
    setIsResizing(false);
  }, []);

  // Add global mouse event listeners for resize
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, handleResizeMove, handleResizeEnd]);



  // Handle mouse events for dragging
  const handleMouseDown = (event: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: event.clientX - pan.x, y: event.clientY - pan.y });
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

  // Update overlays when dependencies change
  useEffect(() => {
    drawOverlays();
  }, [drawOverlays]);

  // Debug text elements on mount
  useEffect(() => {
    console.log('InteractiveTextViewer mounted with:', {
      textElementsCount: textElements.length,
      imageDimensions,
      imageUrl,
      firstFewElements: textElements.slice(0, 3).map(el => ({
        text: el.text,
        bounding_box: el.bounding_box,
        confidence: el.confidence
      }))
    });
  }, [textElements, imageDimensions, imageUrl]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex flex-col">
      {/* Navigation Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Breadcrumb */}
          <nav className="flex items-center space-x-2 text-sm text-gray-600">
            <Home className="w-4 h-4" />
            <span>SLD Processing Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span>Text Detection</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-blue-600 font-medium flex items-center">
              <FileText className="w-4 h-4 mr-1" />
              Interactive Viewer
            </span>
          </nav>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-1"
            title="Close Viewer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex h-full">
        {/* Left Sidebar - Text Elements Gallery */}
        <div
          className={`${sidebarCollapsed ? 'w-0' : ''} bg-white flex flex-col transition-all duration-300 ${sidebarCollapsed ? 'overflow-hidden' : ''} h-full`}
          style={{
            width: sidebarCollapsed ? 0 : `${sidebarWidth}px`,
            minWidth: sidebarCollapsed ? 0 : '200px',
            maxWidth: sidebarCollapsed ? 0 : '600px'
          }}
        >
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Text Elements ({filteredElements.length})
              </h2>
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="text-gray-500 hover:text-gray-700 sm:hidden"
                title={sidebarCollapsed ? 'Show Sidebar' : 'Hide Sidebar'}
              >
                {sidebarCollapsed ? <Menu className="w-5 h-5" /> : <X className="w-5 h-5" />}
              </button>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search text elements..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Text Elements List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0">
            {filteredElements.map((element) => {
              const originalIndex = textElements.indexOf(element);
              const isSelected = selectedElement === originalIndex;

              return (
                <div
                  key={originalIndex}
                  id={`text-element-${originalIndex}`}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  onClick={() => setSelectedElement(originalIndex)}
                  onMouseEnter={() => setHoveredElement(originalIndex)}
                  onMouseLeave={() => setHoveredElement(null)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900 flex-1">
                      {element.text}
                    </span>
                    <span
                      className="text-xs px-2 py-1 rounded-full text-white ml-2"
                      style={{ backgroundColor: getConfidenceColor(element.confidence) }}
                    >
                      {((element.confidence || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    Position: ({(element.bounding_box?.left || 0).toFixed(0)}, {(element.bounding_box?.top || 0).toFixed(0)})
                    <br />
                    Size: {(element.bounding_box?.width || 0).toFixed(0)} × {(element.bounding_box?.height || 0).toFixed(0)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Resize Handle */}
        {!sidebarCollapsed && (
          <div
            className="w-1 bg-gray-300 hover:bg-blue-500 cursor-col-resize transition-colors duration-200 relative group"
            onMouseDown={handleResizeStart}
          >
            <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-blue-500 group-hover:bg-opacity-20"></div>
          </div>
        )}

        {/* Floating Sidebar Toggle (when collapsed) */}
        {sidebarCollapsed && (
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="fixed top-4 left-4 z-10 bg-white bg-opacity-90 hover:bg-opacity-100 text-gray-700 p-2 rounded-lg shadow-lg transition-all"
            title="Show Text Elements"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* Right Side - Image Display */}
        <div className="flex-1 flex flex-col bg-gray-900">
          {/* Toolbar */}
          <div className="p-4 bg-gray-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <button
                onClick={zoomIn}
                className="p-2 text-white hover:bg-gray-700 rounded"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={zoomOut}
                className="p-2 text-white hover:bg-gray-700 rounded"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                onClick={resetZoom}
                className="p-2 text-white hover:bg-gray-700 rounded"
                title="Reset Zoom"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <span className="text-white text-sm">
                {(zoom * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowOverlays(!showOverlays)}
                className={`p-2 rounded ${showOverlays ? 'bg-blue-600 text-white' : 'text-white hover:bg-gray-700'
                  }`}
                title={showOverlays ? 'Hide Overlays' : 'Show Overlays'}
              >
                {showOverlays ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </button>
              <button
                onClick={exportResults}
                className="p-2 text-white hover:bg-gray-700 rounded"
                title="Export Results"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

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
                style={{ cursor: hoveredElement !== null ? 'pointer' : 'crosshair' }}
              />
            </div>
          </div>

          {/* Status Bar */}
          <div className="p-2 bg-gray-800 text-white text-sm flex justify-between">
            <span>
              {selectedElement !== null
                ? `Selected: "${textElements[selectedElement]?.text || 'Unknown'}" (${((textElements[selectedElement]?.confidence || 0) * 100).toFixed(1)}%)`
                : 'Click on text elements to select'
              }
            </span>
            <span>
              Total: {textElements.length} elements
            </span>
          </div>
        </div>

        {/* Simple Tooltip */}
        {tooltip && tooltip.visible && (
          <div
            className="fixed z-50 bg-black bg-opacity-90 text-white px-3 py-2 rounded-lg text-sm pointer-events-none"
            style={{
              left: tooltip.x + 10,
              top: tooltip.y - 40,
            }}
          >
            <div className="font-medium">{tooltip.text}</div>
            <div className="text-xs text-gray-300">
              Confidence: {(tooltip.confidence * 100).toFixed(1)}%
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default InteractiveTextViewer;

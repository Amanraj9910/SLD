import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Download, Search, Filter, Eye, EyeOff } from 'lucide-react';

interface Detection {
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

interface InteractiveVisualizationProps {
  imageFile: File;
  detections: Detection[];
  imageDimensions: {
    width: number;
    height: number;
  };
}

const InteractiveVisualization: React.FC<InteractiveVisualizationProps> = ({
  imageFile,
  detections,
  imageDimensions
}) => {
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);
  const [hoveredDetection, setHoveredDetection] = useState<Detection | null>(null);
  const [zoom, setZoom] = useState(1);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [searchText, setSearchText] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<string>('');
  const [showInfoBoxes, setShowInfoBoxes] = useState(true);
  const [sortBy, setSortBy] = useState<'confidence' | 'type' | 'area'>('confidence');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Component colors for different electrical components (Modern color palette with red accents)
  const getComponentColor = (className: string): string => {
    const colorMap: { [key: string]: string } = {
      'CIRCUIT BREAKER': '#DC2626',      // Red for primary protection
      'HRC FUSE': '#EF4444',            // Bright red for fuses
      'ISOLATOR': '#F97316',            // Orange for isolation
      'CONTACTOR': '#8B5CF6',           // Purple for control
      'VOLTMETER': '#06B6D4',           // Cyan for measurement
      'AMMETER': '#10B981',             // Green for measurement
      'CURRENT TRANSFORMER': '#6366F1', // Indigo for transformers
      'PUB kWh METER': '#84CC16',       // Lime for meters
      'EARTH FAULT RELAY': '#DC2626',   // Red for protection
      'TIME DELAY RELAY': '#F59E0B',    // Amber for timing
      'PHASE SELECTOR SWITCH': '#8B5CF6', // Purple for switching
      'CABLE TERMINATION BOX': '#64748B', // Gray for infrastructure
      'THREE PHASE FUSED TAP-OFF UNIT': '#EF4444', // Red for protection
      'SINGLE PHASE TAP-OFF UNIT': '#F97316',      // Orange for distribution
      'EARTH ELECTRODE': '#22C55E',     // Green for earthing
      'PHASE INDICATOR LIGHTS': '#FBBF24', // Yellow for indication
      'HOUSE SERVICE/METER BOARD': '#6B7280', // Gray for boards
      'MAXIMUM DEMAND AMMETER': '#10B981',     // Green for measurement
      'SINGLE PHASE UNFUSED TAP-OFF UNIT': '#F97316', // Orange
      'RIPPLE CONTROL RECEIVER RELAY': '#8B5CF6',     // Purple for control
      'INVERSE DEFINITE MINIMUM TIME LAG OVERCURRENT RELAY': '#DC2626', // Red for protection
      'OVER CURRENT RELAY': '#EF4444',  // Red for protection
      'KEY INTERLOCK BETWEEN COUPLER': '#64748B' // Gray for mechanical
    };
    return colorMap[className] || '#DC2626';
  };

  // Get component statistics
  const getComponentStats = () => {
    const stats: { [key: string]: number } = {};
    detections.forEach(detection => {
      stats[detection.class_name] = (stats[detection.class_name] || 0) + 1;
    });
    return stats;
  };

  // Filter and sort detections
  const getFilteredAndSortedDetections = () => {
    let filtered = detections.filter(detection => {
      const matchesSearch = !searchText ||
        detection.class_name.toLowerCase().includes(searchText.toLowerCase());
      const matchesFilter = !selectedFilter || detection.class_name === selectedFilter;
      return matchesSearch && matchesFilter;
    });

    // Sort detections
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return b.confidence - a.confidence;
        case 'type':
          return a.class_name.localeCompare(b.class_name);
        case 'area':
          return b.area - a.area;
        default:
          return 0;
      }
    });

    return filtered;
  };

  // Removed unused function getUniqueComponentTypes

  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [imageFile]);

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image || !imageUrl) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const containerWidth = canvas.parentElement?.clientWidth || 800;
    const aspectRatio = imageDimensions.height / imageDimensions.width;
    const canvasWidth = Math.min(containerWidth, imageDimensions.width * zoom);
    const canvasHeight = canvasWidth * aspectRatio;

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // Draw image
    ctx.drawImage(image, 0, 0, canvasWidth, canvasHeight);

    // Draw bounding boxes
    detections.forEach((detection, index) => {
      const scaleX = canvasWidth / imageDimensions.width;
      const scaleY = canvasHeight / imageDimensions.height;

      const x1 = detection.bbox.x1 * scaleX;
      const y1 = detection.bbox.y1 * scaleY;
      const x2 = detection.bbox.x2 * scaleX;
      const y2 = detection.bbox.y2 * scaleY;

      const width = x2 - x1;
      const height = y2 - y1;

      const color = getComponentColor(detection.class_name);
      const isSelected = selectedDetection === detection;
      const isHovered = hoveredDetection === detection;

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = isSelected ? 4 : isHovered ? 3 : 2;
      ctx.setLineDash(isSelected ? [8, 4] : isHovered ? [4, 2] : []);
      ctx.strokeRect(x1, y1, width, height);

      // Draw filled background for selected/hovered
      if (isSelected) {
        ctx.fillStyle = color + '30';
        ctx.fillRect(x1, y1, width, height);
      } else if (isHovered) {
        ctx.fillStyle = color + '15';
        ctx.fillRect(x1, y1, width, height);
      }

      // Draw labels only if info boxes are enabled
      if (showInfoBoxes) {
        // Draw label background
        const label = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;
        ctx.font = '11px Inter, Arial, sans-serif';
        const textMetrics = ctx.measureText(label);
        const labelWidth = textMetrics.width + 12;
        const labelHeight = 22;

        // Position label above or below based on space
        const labelY = y1 > labelHeight ? y1 - labelHeight : y2;

        ctx.fillStyle = color;
        ctx.fillRect(x1, labelY, labelWidth, labelHeight);

        // Draw label text
        ctx.fillStyle = 'white';
        ctx.font = '11px Inter, Arial, sans-serif';
        ctx.fillText(label, x1 + 6, labelY + 15);
      }

      // Draw component number
      ctx.fillStyle = color;
      ctx.fillRect(x1 + width - 28, y1, 28, 22);
      ctx.fillStyle = 'white';
      ctx.font = 'bold 12px Inter, Arial, sans-serif';
      const numberText = (index + 1).toString();
      const numberWidth = ctx.measureText(numberText).width;
      ctx.fillText(numberText, x1 + width - 14 - numberWidth/2, y1 + 15);
    });
  }, [imageUrl, detections, selectedDetection, hoveredDetection, zoom, imageDimensions, showInfoBoxes]);

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  const getDetectionAtPosition = (x: number, y: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const scaleX = imageDimensions.width / canvas.width;
    const scaleY = imageDimensions.height / canvas.height;

    const imageX = x * scaleX;
    const imageY = y * scaleY;

    return detections.find(detection => {
      return imageX >= detection.bbox.x1 && imageX <= detection.bbox.x2 &&
             imageY >= detection.bbox.y1 && imageY <= detection.bbox.y2;
    });
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const clickedDetection = getDetectionAtPosition(x, y);
    setSelectedDetection(clickedDetection || null);
  };

  const handleCanvasMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const tooltip = tooltipRef.current;
    if (!canvas || !tooltip) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const hoveredDetection = getDetectionAtPosition(x, y);
    setHoveredDetection(hoveredDetection || null);

    if (hoveredDetection) {
      // Position tooltip
      tooltip.style.display = 'block';
      tooltip.style.left = `${event.clientX + 10}px`;
      tooltip.style.top = `${event.clientY - 10}px`;

      // Update tooltip content
      tooltip.innerHTML = `
        <div class="font-semibold">${hoveredDetection.class_name}</div>
        <div class="text-sm">Confidence: ${(hoveredDetection.confidence * 100).toFixed(1)}%</div>
        <div class="text-sm">Area: ${hoveredDetection.area.toLocaleString()} px²</div>
      `;

      canvas.style.cursor = 'pointer';
    } else {
      tooltip.style.display = 'none';
      canvas.style.cursor = 'default';
    }
  };

  const handleCanvasMouseLeave = () => {
    const tooltip = tooltipRef.current;
    const canvas = canvasRef.current;
    if (tooltip) tooltip.style.display = 'none';
    if (canvas) canvas.style.cursor = 'default';
    setHoveredDetection(null);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.5));
  const handleResetZoom = () => setZoom(1);

  const downloadVisualization = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = 'sld_detection_results.png';
    link.href = canvas.toDataURL();
    link.click();
  };

  const componentStats = getComponentStats();
  const filteredDetections = getFilteredAndSortedDetections();

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-8 bg-red-500 rounded-full"></div>
            <h3 className="text-lg sm:text-xl font-semibold text-gray-800">
              Interactive SLD Visualization
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setShowInfoBoxes(!showInfoBoxes)}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title={showInfoBoxes ? "Hide Info Boxes" : "Show Info Boxes"}
            >
              {showInfoBoxes ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomIn}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Reset Zoom"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={downloadVisualization}
              className="p-2 text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors shadow-sm"
              title="Download Visualization"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-col lg:flex-row min-h-[calc(100vh-200px)]">
        {/* Sidebar - Responsive width and collapsible on mobile */}
        <div className="w-full lg:w-64 bg-gray-50 border-b lg:border-b-0 lg:border-r border-gray-200 flex flex-col max-h-96 lg:max-h-none">
          {/* Component Summary */}
          <div className="p-3 lg:p-4 bg-white border-b border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3 text-sm lg:text-base">Component Summary</h4>
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-2 lg:space-y-2 lg:gap-0">
              {Object.entries(componentStats).map(([component, count]) => (
                <div
                  key={component}
                  onClick={() => setSelectedFilter(selectedFilter === component ? '' : component)}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                    selectedFilter === component ? 'bg-blue-100 border border-blue-300' : 'hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center min-w-0 flex-1">
                    <div
                      className="w-2.5 h-2.5 rounded-full mr-2 flex-shrink-0"
                      style={{ backgroundColor: getComponentColor(component) }}
                    />
                    <span className="text-xs font-medium text-gray-700 truncate">{component}</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-900 ml-1">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Search and Filter Controls */}
          <div className="p-3 bg-white border-b border-gray-200">
            <div className="grid grid-cols-1 lg:grid-cols-1 gap-2 lg:space-y-2 lg:gap-0">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 w-3 h-3" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="w-full pl-7 pr-2 py-1.5 border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-xs"
                />
              </div>
              <div className="relative">
                <Filter className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 w-3 h-3" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'confidence' | 'type' | 'area')}
                  className="w-full pl-7 pr-2 py-1.5 border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-xs"
                >
                  <option value="confidence">By Confidence</option>
                  <option value="type">By Type</option>
                  <option value="area">By Area</option>
                </select>
              </div>
            </div>
          </div>

          {/* Component List */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-3">
              <h4 className="font-medium text-gray-900 mb-2 text-sm">
                Components ({filteredDetections.length})
              </h4>
              <div className="grid grid-cols-1 lg:grid-cols-1 gap-1">
                {filteredDetections.map((detection, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedDetection(detection)}
                    className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                      selectedDetection === detection
                        ? 'bg-blue-100 border border-blue-300'
                        : hoveredDetection === detection
                        ? 'bg-gray-100'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div
                      className="w-3 h-3 rounded-full mr-2 flex-shrink-0"
                      style={{ backgroundColor: getComponentColor(detection.class_name) }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-gray-900 truncate">
                        {detections.indexOf(detection) + 1}. {detection.class_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {(detection.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 p-2 lg:p-4">
            <div className="relative h-full rounded-lg overflow-hidden bg-gray-50 border border-gray-200">
              <img
                ref={imageRef}
                src={imageUrl}
                alt="SLD"
                className="hidden"
                onLoad={drawCanvas}
              />
              <div className="w-full h-full overflow-auto">
                <canvas
                  ref={canvasRef}
                  onClick={handleCanvasClick}
                  onMouseMove={handleCanvasMouseMove}
                  onMouseLeave={handleCanvasMouseLeave}
                  className="cursor-pointer min-w-full min-h-full object-contain"
                  style={{ display: 'block' }}
                />
              </div>
            </div>
          </div>
          <div className="px-2 lg:px-4 pb-2 lg:pb-4">
            <p className="text-xs lg:text-sm text-gray-500 text-center lg:text-left">
              Click on detected components to view details • Hover for quick info • Zoom: {(zoom * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 bg-gray-900 text-white text-xs rounded-lg p-2 shadow-lg pointer-events-none"
        style={{ display: 'none' }}
      />

      {/* Selected Component Details Modal/Panel */}
      {selectedDetection && (
        <div className="fixed bottom-4 left-4 right-4 lg:left-auto lg:right-4 lg:w-80 bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-40">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <div
                className="w-4 h-4 rounded-full mr-2"
                style={{ backgroundColor: getComponentColor(selectedDetection.class_name) }}
              />
              <h4 className="font-semibold text-gray-900">Component Details</h4>
            </div>
            <button
              onClick={() => setSelectedDetection(null)}
              className="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
              title="Close"
            >
              ×
            </button>
          </div>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-gray-700">Type:</span>
              <span className="ml-1">{selectedDetection.class_name}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Confidence:</span>
              <span className="ml-1">{(selectedDetection.confidence * 100).toFixed(1)}%</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Position:</span>
              <span className="ml-1">({selectedDetection.bbox.x1}, {selectedDetection.bbox.y1})</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Size:</span>
              <span className="ml-1">{selectedDetection.bbox.x2 - selectedDetection.bbox.x1} × {selectedDetection.bbox.y2 - selectedDetection.bbox.y1} px</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Area:</span>
              <span className="ml-1">{selectedDetection.area.toLocaleString()} px²</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveVisualization;

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  X,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Eye,
  EyeOff,
  ChevronLeft,
  ChevronRight,
  FileText
} from 'lucide-react';

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

interface PDFPageResult {
  page_number: number;
  image_url: string;  // URL to access the page image
  image_dimensions: {
    width: number;
    height: number;
  };
  processing_time: number;
  detections: Detection[];
  total_detections: number;
}

interface PDFDetectionResult {
  success: boolean;
  message: string;
  pdf_path: string;
  pdf_id: string;  // Unique identifier for this PDF processing session
  total_pages: number;
  total_detections: number;
  total_processing_time: number;
  page_results: PDFPageResult[];
  model_info: any;
}

interface InteractivePDFViewerProps {
  pdfResult: PDFDetectionResult;
  onClose: () => void;
  onExport: () => void;
}

const InteractivePDFViewer: React.FC<InteractivePDFViewerProps> = ({
  pdfResult,
  onClose,
  onExport
}) => {
  // State management
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [showOverlays, setShowOverlays] = useState(true);
  const [selectedElement, setSelectedElement] = useState<number | null>(null);
  const [hoveredElement, setHoveredElement] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Refs
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Confidence threshold for filtering (25%)
  const CONFIDENCE_THRESHOLD = 0.25;

  // Get current page data
  const currentPageData = pdfResult.page_results.find(p => p.page_number === currentPage);
  const detections = useMemo(() => currentPageData?.detections || [], [currentPageData]);

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
    if (confidence >= 0.8) return '#10B981'; // Green
    if (confidence >= 0.6) return '#F59E0B'; // Yellow
    if (confidence >= 0.4) return '#EF4444'; // Red
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

        const x = bbox.x1 * zoom;
        const y = bbox.y1 * zoom;
        const width = (bbox.x2 - bbox.x1) * zoom;
        const height = (bbox.y2 - bbox.y1) * zoom;

        // Draw subtle outline for interaction feedback - GREEN for selected
        ctx.strokeStyle = isSelected ? '#10B981' : '#6b7280'; // Green for selected, gray for hovered
        ctx.lineWidth = isSelected ? 3 : 1;
        ctx.setLineDash(isSelected ? [] : [5, 5]);
        ctx.strokeRect(x, y, width, height);
        ctx.setLineDash([]); // Reset line dash

        // Draw label for selected/hovered elements
        if (isSelected || isHovered) {
          const label = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;

          ctx.font = `${12 * zoom}px Arial`;
          const textMetrics = ctx.measureText(label);
          const textWidth = textMetrics.width;
          const textHeight = 16 * zoom;

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

    // Full overlay mode
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
      ctx.lineWidth = (isSelected ? 4 : isHovered ? 2 : 1) * zoom; // Thicker border for selected
      ctx.fillStyle = isSelected ? '#10B98120' : isHovered ? `${color}20` : `${color}10`;

      const bbox = detection.bbox;
      const x = bbox.x1 * zoom;
      const y = bbox.y1 * zoom;
      const width = (bbox.x2 - bbox.x1) * zoom;
      const height = (bbox.y2 - bbox.y1) * zoom;

      // Draw filled rectangle
      ctx.fillRect(x, y, width, height);

      // Draw border
      ctx.strokeRect(x, y, width, height);

      // Draw label
      const label = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;
      ctx.font = `${12 * zoom}px Arial`;
      const textMetrics = ctx.measureText(label);
      const textWidth = textMetrics.width;
      const textHeight = 16 * zoom;

      // Background for text
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(x, y - textHeight - 2, textWidth + 8, textHeight + 4);

      // Text
      ctx.fillStyle = '#fff';
      ctx.fillText(label, x + 4, y - 4);
    });
  }, [detections, filteredDetections, selectedElement, hoveredElement, showOverlays, searchTerm, zoom, CONFIDENCE_THRESHOLD]);

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / zoom;
    const y = (event.clientY - rect.top) / zoom;

    const elementIndex = findElementAtCoordinates(x, y);
    setSelectedElement(elementIndex);
  };

  // Handle canvas mouse move
  const handleCanvasMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / zoom;
    const y = (event.clientY - rect.top) / zoom;

    const elementIndex = findElementAtCoordinates(x, y);
    setHoveredElement(elementIndex);
  };

  // Handle canvas mouse leave
  const handleCanvasMouseLeave = () => {
    setHoveredElement(null);
  };

  // Page navigation
  const goToPreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
      setSelectedElement(null);
      setHoveredElement(null);
    }
  };

  const goToNextPage = () => {
    if (currentPage < pdfResult.total_pages) {
      setCurrentPage(currentPage + 1);
      setSelectedElement(null);
      setHoveredElement(null);
    }
  };



  // Zoom controls
  const zoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3));
  const zoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.5));
  const resetZoom = () => setZoom(1);

  // Load page image and setup canvas
  useEffect(() => {
    if (!currentPageData) return;

    const image = imageRef.current;
    const canvas = canvasRef.current;

    if (!image || !canvas) return;

    // Get the image URL for the current page from the PDF result
    const pageImageUrl = currentPageData?.image_url || '';

    image.onload = () => {
      // Set canvas size to match image
      canvas.width = image.naturalWidth * zoom;
      canvas.height = image.naturalHeight * zoom;

      // Draw overlays
      drawOverlays();
    };

    // For now, create a placeholder image
    // In real implementation, this would be the actual PDF page image
    image.src = pageImageUrl;
  }, [currentPage, currentPageData, zoom, drawOverlays]);

  // Redraw overlays when dependencies change
  useEffect(() => {
    drawOverlays();
  }, [drawOverlays]);

  if (!currentPageData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p>Page {currentPage} not found</p>
          <button onClick={onClose} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-7xl max-h-[95vh] flex flex-col relative">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <FileText className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                PDF Component Viewer
              </h2>
              <p className="text-sm text-gray-600">
                {pdfResult.pdf_path} - Page {currentPage} of {pdfResult.total_pages}
              </p>
            </div>
          </div>

          {/* Page Navigation */}
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPreviousPage}
              disabled={currentPage === 1}
              className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <span className="text-sm text-gray-600 min-w-[80px] text-center">
              {currentPage} / {pdfResult.total_pages}
            </span>

            <button
              onClick={goToNextPage}
              disabled={currentPage === pdfResult.total_pages}
              className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={zoomOut}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>

            <span className="text-sm text-gray-600 min-w-[50px] text-center">
              {Math.round(zoom * 100)}%
            </span>

            <button
              onClick={zoomIn}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>

            <button
              onClick={resetZoom}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title="Reset Zoom"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              onClick={() => setShowOverlays(!showOverlays)}
              className={`p-2 rounded-lg transition-colors ${showOverlays
                  ? 'text-blue-600 bg-blue-50 hover:bg-blue-100'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              title={showOverlays ? 'Switch to Clean View (hide overlays)' : 'Switch to Full View (show overlays)'}
            >
              {showOverlays ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>

            <button
              onClick={onExport}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title="Export Results"
            >
              <Download className="w-4 h-4" />
            </button>

            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">

          {/* PDF Page Display */}
          <div className="flex-1 relative overflow-auto bg-gray-100" ref={containerRef}>
            <div className="p-4">
              <div className="relative inline-block">
                <img
                  ref={imageRef}
                  src={currentPageData?.image_url || ''}
                  alt={`PDF Page ${currentPage}`}
                  className="max-w-none"
                  style={{
                    transform: `scale(${zoom})`,
                    transformOrigin: 'top left'
                  }}
                />
                <canvas
                  ref={canvasRef}
                  className="absolute top-0 left-0 pointer-events-auto"
                  onClick={handleCanvasClick}
                  onMouseMove={handleCanvasMouseMove}
                  onMouseLeave={handleCanvasMouseLeave}
                  style={{
                    cursor: hoveredElement !== null ? 'pointer' : showOverlays ? 'crosshair' : 'default',
                    opacity: showOverlays ? 1 : 0.8
                  }}
                />
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="w-80 border-l border-gray-200 bg-white flex flex-col">

            {/* Search */}
            <div className="p-4 border-b border-gray-200">
              <input
                type="text"
                placeholder="Search components..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Page Summary */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-2">Page {currentPage} Summary</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <div>Components: {filteredDetections.length}</div>
                <div>Processing: {currentPageData.processing_time.toFixed(2)}s</div>
                <div>Dimensions: {currentPageData.image_dimensions.width}×{currentPageData.image_dimensions.height}</div>
              </div>
            </div>

            {/* Components List */}
            <div className="flex-1 overflow-y-auto p-4">
              <h3 className="font-medium text-gray-900 mb-3">Detected Components</h3>

              {filteredDetections.length === 0 ? (
                <p className="text-gray-500 text-sm">No components found on this page.</p>
              ) : (
                <div className="space-y-2">
                  {filteredDetections.map((detection, index) => {
                    const originalIndex = detections.indexOf(detection);
                    const isSelected = selectedElement === originalIndex;

                    return (
                      <div
                        key={index}
                        onClick={() => setSelectedElement(originalIndex)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 text-sm">
                              {detection.class_name}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              Confidence: {(detection.confidence * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div
                            className="w-3 h-3 rounded-full ml-2 flex-shrink-0"
                            style={{ backgroundColor: getConfidenceColor(detection.confidence) }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
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
              Page {currentPage}: {filteredDetections.length} components (≥25% confidence)
            </span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default InteractivePDFViewer;

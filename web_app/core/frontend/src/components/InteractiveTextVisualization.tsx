import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Download, Search, Filter, Eye, EyeOff, Type } from 'lucide-react';

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
  center: {
    x: number;
    y: number;
  };
  area: number;
}

interface InteractiveTextVisualizationProps {
  imageFile: File;
  textElements: TextElement[];
  imageDimensions: {
    width: number;
    height: number;
  };
}

const InteractiveTextVisualization: React.FC<InteractiveTextVisualizationProps> = ({
  imageFile,
  textElements,
  imageDimensions
}) => {
  const [selectedTextElement, setSelectedTextElement] = useState<TextElement | null>(null);
  const [hoveredTextElement, setHoveredTextElement] = useState<TextElement | null>(null);
  const [zoom, setZoom] = useState(1);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [searchText, setSearchText] = useState('');
  const [minConfidence, setMinConfidence] = useState(0);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [sortBy, setSortBy] = useState<'confidence' | 'text' | 'area'>('confidence');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Text element colors based on confidence
  const getTextElementColor = (confidence: number): string => {
    if (confidence >= 0.9) return '#10B981'; // Green for high confidence
    if (confidence >= 0.7) return '#F59E0B'; // Yellow for medium confidence
    return '#EF4444'; // Red for low confidence
  };

  // Create image URL from file
  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [imageFile]);

  // Filter text elements based on search and confidence
  const filteredTextElements = textElements.filter(element => {
    const matchesSearch = searchText === '' || 
      element.text.toLowerCase().includes(searchText.toLowerCase());
    const matchesConfidence = element.confidence >= minConfidence;
    return matchesSearch && matchesConfidence;
  });

  // Sort text elements
  const sortedTextElements = [...filteredTextElements].sort((a, b) => {
    switch (sortBy) {
      case 'confidence':
        return b.confidence - a.confidence;
      case 'text':
        return a.text.localeCompare(b.text);
      case 'area':
        return b.area - a.area;
      default:
        return 0;
    }
  });

  // Draw text elements on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    
    if (!canvas || !image || !imageUrl) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const drawVisualization = () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw image
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

      if (!showBoundingBoxes) return;

      // Calculate scale factors
      const scaleX = canvas.width / imageDimensions.width;
      const scaleY = canvas.height / imageDimensions.height;

      // Draw bounding boxes for filtered text elements
      filteredTextElements.forEach((element, index) => {
        const x1 = element.bounding_box.x1 * scaleX;
        const y1 = element.bounding_box.y1 * scaleY;
        const x2 = element.bounding_box.x2 * scaleX;
        const y2 = element.bounding_box.y2 * scaleY;

        const width = x2 - x1;
        const height = y2 - y1;

        const color = getTextElementColor(element.confidence);
        const isSelected = selectedTextElement === element;
        const isHovered = hoveredTextElement === element;

        // Draw bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;
        ctx.setLineDash(isSelected ? [8, 4] : isHovered ? [4, 2] : []);
        ctx.strokeRect(x1, y1, width, height);

        // Draw background for text
        if (isSelected || isHovered) {
          ctx.fillStyle = color + '20'; // 20% opacity
          ctx.fillRect(x1, y1, width, height);
        }

        // Draw text label for selected/hovered elements
        if ((isSelected || isHovered) && element.text.length < 50) {
          ctx.fillStyle = color;
          ctx.font = '12px Arial';
          ctx.fillText(element.text, x1, y1 - 5);
        }
      });
    };

    if (image.complete) {
      drawVisualization();
    } else {
      image.onload = drawVisualization;
    }
  }, [imageUrl, filteredTextElements, selectedTextElement, hoveredTextElement, showBoundingBoxes, imageDimensions]);

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const scaleX = imageDimensions.width / canvas.width;
    const scaleY = imageDimensions.height / canvas.height;

    const imageX = x * scaleX;
    const imageY = y * scaleY;

    // Find clicked text element
    const clickedElement = filteredTextElements.find(element => {
      return imageX >= element.bounding_box.x1 && imageX <= element.bounding_box.x2 &&
             imageY >= element.bounding_box.y1 && imageY <= element.bounding_box.y2;
    });

    setSelectedTextElement(clickedElement || null);
  };

  // Handle canvas mouse move for hover effects
  const handleCanvasMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const tooltip = tooltipRef.current;
    if (!canvas || !tooltip) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const scaleX = imageDimensions.width / canvas.width;
    const scaleY = imageDimensions.height / canvas.height;

    const imageX = x * scaleX;
    const imageY = y * scaleY;

    // Find hovered text element
    const hoveredElement = filteredTextElements.find(element => {
      return imageX >= element.bounding_box.x1 && imageX <= element.bounding_box.x2 &&
             imageY >= element.bounding_box.y1 && imageY <= element.bounding_box.y2;
    });

    setHoveredTextElement(hoveredElement || null);

    // Show/hide tooltip
    if (hoveredElement) {
      tooltip.style.display = 'block';
      tooltip.style.left = `${event.clientX + 10}px`;
      tooltip.style.top = `${event.clientY - 10}px`;
      tooltip.innerHTML = `
        <div class="font-medium">${hoveredElement.text}</div>
        <div class="text-sm text-gray-600">Confidence: ${(hoveredElement.confidence * 100).toFixed(1)}%</div>
      `;
    } else {
      tooltip.style.display = 'none';
    }
  };

  // Handle canvas mouse leave
  const handleCanvasMouseLeave = () => {
    setHoveredTextElement(null);
    const tooltip = tooltipRef.current;
    if (tooltip) {
      tooltip.style.display = 'none';
    }
  };

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 5));
  const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.1));
  const handleResetZoom = () => setZoom(1);

  // Export functionality
  const handleExport = () => {
    const dataStr = JSON.stringify(filteredTextElements, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'text_detection_results.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Main Visualization Area */}
      <div className="flex-1 min-h-0">
        <div className="card p-4 h-full flex flex-col">
          {/* Controls */}
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center space-x-2">
              <button
                onClick={handleZoomIn}
                className="btn btn-outline btn-sm"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={handleZoomOut}
                className="btn btn-outline btn-sm"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                onClick={handleResetZoom}
                className="btn btn-outline btn-sm"
                title="Reset Zoom"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-600">
                {Math.round(zoom * 100)}%
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
                className={`btn btn-sm ${showBoundingBoxes ? 'btn-primary' : 'btn-outline'}`}
                title="Toggle Bounding Boxes"
              >
                {showBoundingBoxes ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </button>
              <button
                onClick={handleExport}
                className="btn btn-outline btn-sm"
                title="Export Results"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Canvas Container */}
          <div className="flex-1 relative overflow-auto border rounded-lg bg-gray-50">
            <div
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'top left',
                width: `${100 / zoom}%`,
                height: `${100 / zoom}%`,
              }}
            >
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="block max-w-full h-auto cursor-crosshair"
                onClick={handleCanvasClick}
                onMouseMove={handleCanvasMouseMove}
                onMouseLeave={handleCanvasMouseLeave}
              />
              <img
                ref={imageRef}
                src={imageUrl}
                alt="SLD Document"
                className="hidden"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className="w-full lg:w-96 flex flex-col">
        {/* Search and Filters */}
        <div className="card p-4 mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Type className="w-5 h-5 mr-2" />
            Text Elements ({filteredTextElements.length})
          </h3>

          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search text..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          {/* Confidence Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Confidence: {Math.round(minConfidence * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Sort Options */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sort by
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'confidence' | 'text' | 'area')}
              className="input"
            >
              <option value="confidence">Confidence</option>
              <option value="text">Text (A-Z)</option>
              <option value="area">Size</option>
            </select>
          </div>
        </div>

        {/* Text Elements List */}
        <div className="card p-4 flex-1 min-h-0">
          <div className="h-full overflow-y-auto">
            <div className="space-y-2">
              {sortedTextElements.map((element, index) => (
                <div
                  key={index}
                  onClick={() => setSelectedTextElement(element)}
                  onMouseEnter={() => setHoveredTextElement(element)}
                  onMouseLeave={() => setHoveredTextElement(null)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors border ${
                    selectedTextElement === element
                      ? 'bg-blue-100 border-blue-300'
                      : hoveredTextElement === element
                      ? 'bg-gray-100 border-gray-300'
                      : 'hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">
                        {element.text}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Confidence: {(element.confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Size: {Math.round(element.area)} px²
                      </div>
                    </div>
                    <div
                      className="w-3 h-3 rounded-full ml-2 flex-shrink-0"
                      style={{ backgroundColor: getTextElementColor(element.confidence) }}
                    />
                  </div>
                </div>
              ))}

              {sortedTextElements.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <Type className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No text elements found</p>
                  <p className="text-sm">Try adjusting your search or filters</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Selected Element Details */}
        {selectedTextElement && (
          <div className="card p-4 mt-4">
            <h4 className="font-semibold text-gray-900 mb-3">Text Details</h4>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-gray-700">Text:</span>
                <div className="mt-1 p-2 bg-gray-50 rounded text-gray-900 break-words">
                  {selectedTextElement.text}
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">Confidence:</span>
                <span className="ml-2 text-gray-900">
                  {(selectedTextElement.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Position:</span>
                <span className="ml-2 text-gray-900">
                  ({Math.round(selectedTextElement.bounding_box.x1)}, {Math.round(selectedTextElement.bounding_box.y1)})
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Size:</span>
                <span className="ml-2 text-gray-900">
                  {Math.round(selectedTextElement.bounding_box.width)} × {Math.round(selectedTextElement.bounding_box.height)} px
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Area:</span>
                <span className="ml-2 text-gray-900">
                  {Math.round(selectedTextElement.area)} px²
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Page:</span>
                <span className="ml-2 text-gray-900">
                  {selectedTextElement.page_number}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 bg-black text-white text-xs rounded px-2 py-1 pointer-events-none"
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default InteractiveTextVisualization;

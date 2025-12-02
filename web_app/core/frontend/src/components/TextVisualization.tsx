import React, { useState } from 'react';
import { Search, Type, Download } from 'lucide-react';

interface TextElement {
  text: string;
  confidence: number;
  bounding_box: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
  page_number: number;
}

interface TextVisualizationProps {
  textElements: TextElement[];
}

const TextVisualization: React.FC<TextVisualizationProps> = ({
  textElements
}) => {
  const [searchText, setSearchText] = useState('');
  const [minConfidence, setMinConfidence] = useState(0);
  const [sortBy, setSortBy] = useState<'confidence' | 'text' | 'area'>('confidence');

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
        return (b.bounding_box.width * b.bounding_box.height) - (a.bounding_box.width * a.bounding_box.height);
      default:
        return 0;
    }
  });

  // Get text element color based on confidence
  const getTextElementColor = (confidence: number): string => {
    if (confidence >= 0.9) return '#10B981'; // Green for high confidence
    if (confidence >= 0.7) return '#F59E0B'; // Yellow for medium confidence
    return '#EF4444'; // Red for low confidence
  };

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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Controls and Filters */}
      <div className="space-y-6">
        <div className="card p-6">
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

          {/* Export Button */}
          <button
            onClick={handleExport}
            className="btn btn-outline w-full"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Results
          </button>
        </div>
      </div>

      {/* Text Elements List */}
      <div className="card p-6">
        <div className="h-96 overflow-y-auto">
          <div className="space-y-3">
            {sortedTextElements.map((element, index) => (
              <div
                key={index}
                className="p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 break-words">
                      {element.text}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      Confidence: {(element.confidence * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Position: ({Math.round(element.bounding_box.left)}, {Math.round(element.bounding_box.top)})
                    </div>
                    <div className="text-xs text-gray-500">
                      Size: {Math.round(element.bounding_box.width)} × {Math.round(element.bounding_box.height)} px
                    </div>
                    <div className="text-xs text-gray-500">
                      Page: {element.page_number}
                    </div>
                  </div>
                  <div
                    className="w-3 h-3 rounded-full ml-3 flex-shrink-0"
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
    </div>
  );
};

export default TextVisualization;

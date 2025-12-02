import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';

import { Upload, FileText, Download, Eye, Home, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { useSLD } from '../contexts/SLDContext.tsx';
import InteractiveTextViewer from '../components/InteractiveTextViewer.tsx';

const TextDetectionPage: React.FC = () => {
  const { setSLDData, setCurrentImageUrl, setIsProcessing: setGlobalProcessing } = useSLD();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [showInteractiveViewer, setShowInteractiveViewer] = useState(false);

  // Update global context when results change
  useEffect(() => {
    if (results) {
      setSLDData(results);
    }
  }, [results, setSLDData]);

  // Update global context when image URL changes
  useEffect(() => {
    if (imageUrl) {
      setCurrentImageUrl(imageUrl);
    }
  }, [imageUrl, setCurrentImageUrl]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      setResults(null);

      // Create image URL for the interactive viewer
      const url = URL.createObjectURL(file);
      setImageUrl(url);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  // Cleanup image URL on unmount
  useEffect(() => {
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [imageUrl]);

  const handleProcess = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    setIsProcessing(true);
    setGlobalProcessing(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('output_format', 'detailed');
    formData.append('save_results', 'true');

    try {
      const response = await fetch('/api/v1/text/extract', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Text extraction failed');
      }

      const result = await response.json();
      setResults(result);

      // Check if any text elements were detected
      if (result.text_elements.length === 0) {
        toast.error('No text elements detected in the document. Please try with a clearer image or PDF.');
        return;
      }

      toast.success(`Extracted ${result.text_elements.length} text elements`);
    } catch (error) {
      toast.error('Failed to extract text');
      console.error('Error:', error);
    } finally {
      setIsProcessing(false);
      setGlobalProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb Navigation */}
        <nav className="flex items-center space-x-2 py-4 text-sm text-gray-600">
          <Home className="w-4 h-4" />
          <span>SLD Processing Platform</span>
          <ChevronRight className="w-4 h-4" />
          <span className="text-blue-600 font-medium">Text Detection</span>
        </nav>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Text Detection
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Extract text from SLD documents using HOSHO's Text Detector with OCR technology.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2">
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Document
              </h2>

              {/* File Upload */}
              <div
                {...getRootProps()}
                className={`upload-area ${isDragActive ? 'dragover' : ''}`}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                {isDragActive ? (
                  <p className="text-lg text-primary-600">Drop the file here...</p>
                ) : (
                  <div className="text-center">
                    <p className="text-lg text-gray-600 mb-2">
                      Drag & drop a document here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports JPG, PNG, PDF, BMP, TIFF (max 500MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Selected File */}
              {selectedFile && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}

              {/* Process Button */}
              <button
                onClick={handleProcess}
                disabled={!selectedFile || isProcessing}
                className="btn btn-primary w-full mt-6"
              >
                {isProcessing ? (
                  <>
                    <div className="spinner w-4 h-4 mr-2" />
                    Extracting Text...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Extract Text
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Information Section */}
          <div className="space-y-6">

            {/* Features */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                OCR Features
              </h3>
              <div className="space-y-3 text-sm">
                {[
                  'High-precision text extraction',
                  'Polygon bounding boxes',
                  'Confidence scores',
                  'Multi-language support',
                  'PDF and image support',
                  'Structured output format'
                ].map((feature, index) => (
                  <div key={index} className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-3" />
                    <span className="text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Azure Info
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Azure Document Intelligence
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Powered by Microsoft's advanced OCR technology with support for 100+ languages.
              </p>
              <div className="text-xs text-gray-500">
                <div>Model: prebuilt-read</div>
                <div>API Version: 2024-02-29-preview</div>
              </div>
            </div> */}
          </div>
        </div>

        {/* Results Section */}
        {results && (
          <div className="mt-8">
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Extraction Results
                </h2>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setShowInteractiveViewer(true)}
                    className="btn btn-secondary"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Interactive Results ({results.text_elements.length} elements)
                  </button>
                  <button className="btn btn-primary">
                    <Download className="w-4 h-4 mr-2" />
                    Export Results
                  </button>
                </div>
              </div>

              {/* Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {results.text_elements.length}
                  </div>
                  <div className="text-sm text-blue-600">Text Elements</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {results.processing_time.toFixed(2)}s
                  </div>
                  <div className="text-sm text-green-600">Processing Time</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {results.page_count}
                  </div>
                  <div className="text-sm text-purple-600">Pages</div>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {results.total_text_length}
                  </div>
                  <div className="text-sm text-orange-600">Characters</div>
                </div>
              </div>

              {/* Enhanced Text Detection Results */}
              <div className="mt-6">
                <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                  <h4 className="text-lg font-semibold text-blue-900 mb-2">✨ Enhanced Text Detection</h4>
                  <p className="text-sm text-blue-700 mb-3">
                    <strong>Multi-level extraction:</strong> Now extracting text at paragraphs, lines, and word levels
                    for comprehensive detection using enhanced HOSHO's Text Detection.
                  </p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="bg-white p-3 rounded">
                      <strong className="text-blue-800">📄 Paragraphs:</strong> Structured text blocks
                    </div>
                    <div className="bg-white p-3 rounded">
                      <strong className="text-blue-800">📝 Lines:</strong> Multi-word elements
                    </div>
                    <div className="bg-white p-3 rounded">
                      <strong className="text-blue-800">🔤 Words:</strong> Individual text elements
                    </div>
                    <div className="bg-white p-3 rounded">
                      <strong className="text-blue-800">💾 Auto-save:</strong> JSON export enabled
                    </div>
                  </div>
                </div>

                {/* Interactive Viewer */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-blue-900 mb-2 flex items-center">
                    📄 Export Results
                  </h4>
                  <p className="text-blue-700 mb-3">
                    Download the text detection results in JSON format for further processing. The interactive visualization will open automatically after processing.
                  </p>
                  <div className="flex flex-wrap gap-2">

                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(results, null, 2);
                        const dataBlob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(dataBlob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = 'text_detection_results.json';
                        link.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="btn btn-outline btn-sm"
                    >
                      💾 Download JSON
                    </button>
                  </div>
                  <p className="text-xs text-blue-600 mt-2">
                    💡 Features: Image overlay, bounding boxes, search, zoom, pan, and click-to-select
                  </p>
                </div>

                {/* Simple Text List */}
                <div className="mt-6 bg-white rounded-lg border border-gray-200 p-4">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    📋 Detected Text Elements ({results.text_elements.length})
                  </h4>
                  <div className="max-h-96 overflow-y-auto space-y-2">
                    {results.text_elements.map((element: any, index: number) => (
                      <div key={index} className="flex items-start justify-between p-3 bg-gray-50 rounded border">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900 break-words">
                            {element.text}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            Confidence: {(element.confidence * 100).toFixed(1)}% |
                            Position: ({Math.round(element.bounding_box.left)}, {Math.round(element.bounding_box.top)}) |
                            Size: {Math.round(element.bounding_box.width)}×{Math.round(element.bounding_box.height)}px
                          </div>
                        </div>
                        <div
                          className="w-3 h-3 rounded-full ml-3 flex-shrink-0"
                          style={{
                            backgroundColor: element.confidence >= 0.9 ? '#10B981' :
                              element.confidence >= 0.7 ? '#F59E0B' : '#EF4444'
                          }}
                          title={`Confidence: ${(element.confidence * 100).toFixed(1)}%`}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Interactive Text Viewer */}
        {showInteractiveViewer && results && imageUrl && (
          <InteractiveTextViewer
            imageUrl={imageUrl}
            textElements={results.text_elements}
            imageDimensions={results.image_dimensions}
            onClose={() => setShowInteractiveViewer(false)}
          />
        )}

      </div>
    </div>
  );
};

export default TextDetectionPage;

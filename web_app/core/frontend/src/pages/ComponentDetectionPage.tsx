import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useLocation } from 'react-router-dom';
import { Upload, Zap, X, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import { detectComponents, detectComponentsInPDF, validateImageFile } from '../services/api';
import InteractiveComponentViewer from '../components/InteractiveComponentViewer';
import InteractivePDFViewer from '../components/InteractivePDFViewer';

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

interface DetectionResult {
  image_id: string;
  processing_time: number;
  detections: Detection[];
  image_dimensions: {
    width: number;
    height: number;
  };
  model_info: {
    model_type: string;
    confidence_threshold: string;
    iou_threshold: string;
  };
}

const ComponentDetectionPage: React.FC = () => {
  const location = useLocation();

  // Upload mode state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<DetectionResult | null>(null);
  const [pdfResults, setPdfResults] = useState<any | null>(null);
  const [showInteractiveViewer, setShowInteractiveViewer] = useState(false);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isPdfFile, setIsPdfFile] = useState(false);

  // Check if we have results passed from navigation
  useEffect(() => {
    const state = location.state as any;
    if (state?.results && state?.selectedFile) {
      setResults(state.results);
      setSelectedFile(state.selectedFile);
    }
  }, [location.state]);

  // Cleanup image URL on unmount
  useEffect(() => {
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [imageUrl]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const validation = validateImageFile(file);

      if (!validation.valid) {
        toast.error(validation.error || 'Invalid file');
        return;
      }

      setSelectedFile(file);
      setResults(null);
      setPdfResults(null);

      // Check if it's a PDF file
      const isPdf = file.type === 'application/pdf';
      setIsPdfFile(isPdf);

      if (!isPdf) {
        // Create image URL for the interactive viewer (only for images)
        const url = URL.createObjectURL(file);
        setImageUrl(url);
      } else {
        setImageUrl(null);
      }
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

  const handleProcess = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    // Validate file
    const validation = validateImageFile(selectedFile);
    if (!validation.valid) {
      toast.error(validation.error || 'Invalid file');
      return;
    }

    setIsProcessing(true);

    try {
      if (isPdfFile) {
        // Process PDF file
        const response = await detectComponentsInPDF(selectedFile, true);

        if (!response.success) {
          throw new Error(response.error || 'PDF processing failed');
        }

        const pdfData = response.data;
        setPdfResults(pdfData);

        // Check if any components were detected across all pages
        if (pdfData.total_detections === 0) {
          toast.error('No electrical components detected in the PDF. Please try with a clearer SLD diagram or adjust the image quality.');
          return;
        }

        toast.success(`PDF processed: ${pdfData.total_detections} components found across ${pdfData.total_pages} pages`);

        // Show PDF viewer with results
        setShowPdfViewer(true);
      } else {
        // Send SLD file to custom trained YOLO model for prediction
        const response = await detectComponents(selectedFile, {
          confidence_threshold: 0.01,  // Optimized for smaller components
          iou_threshold: 0.3,  // Lower IoU for better small component detection
          save_visualization: true,
          device: 'auto'
        });

        if (!response.success) {
          throw new Error(response.error || 'Processing failed');
        }

        setResults(response.data);

        // Check if any components were detected
        if (response.data.detections.length === 0) {
          toast.error('No electrical components detected in the image. Please try with a clearer SLD diagram or adjust the image quality.');
          return;
        }

        toast.success(`YOLO11x detected ${response.data.detections.length} components`);

        // Show interactive viewer with results
        setShowInteractiveViewer(true);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process image';
      toast.error(errorMessage);
      console.error('Error:', error);
    } finally {
      setIsProcessing(false);
    }
  };



  return (
    <div className="min-h-screen py-8" style={{ backgroundColor: '#f9fafb' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🔍   Component Detection
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Detect electrical components in SLD diagrams using our advanced model.
            Specialized for Single Line Diagram electrical component recognition.
          </p>
        </div>

        {/* Upload Mode */}
          <div className="mb-8">
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Image
              </h2>
              
              {/* File Upload */}
              <div
                {...getRootProps()}
                className={`upload-area ${isDragActive ? 'dragover' : ''}`}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                {isDragActive ? (
                  <p className="text-lg text-primary-600">Drop the image here...</p>
                ) : (
                  <div className="text-center">
                    <p className="text-lg text-gray-600 mb-2">
                      Drag & drop an image or PDF here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports JPG, PNG, BMP, TIFF, PDF (max 10MB)
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
              {isProcessing ? (
                <div className="flex space-x-3 mt-6">
                  <div className="flex-1 btn btn-primary opacity-75 cursor-not-allowed">
                    <div className="spinner w-4 h-4 mr-2" />
                    Processing...
                  </div>
                  <button
                    onClick={() => setIsProcessing(false)}
                    className="btn btn-outline px-4"
                    title="Cancel Processing"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="space-y-3 mt-6">
                  <button
                    onClick={handleProcess}
                    disabled={!selectedFile}
                    className="btn btn-primary w-full"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Detect Components
                  </button>

                  {results && results.detections.length > 0 && (
                    <button
                      onClick={() => setShowInteractiveViewer(true)}
                      className="btn btn-secondary w-full"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Interactive Results ({results.detections.length} components)
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

        {/* Detectable Components Section */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Detectable SLD Components (5 Classes)
          </h3>
          <p className="text-gray-600 mb-4">
            Our custom-trained model can detect the following electrical components in Single Line Diagrams:
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 text-sm">
            {[
              'Ammeter',
              'Cable Termination Box',
              'Earth Electrode',
              'Single Phase Tap-Off Unit',
              'voltmeter'
            ].map((component, index) => (
              <div key={index} className="flex items-center p-2 rounded" style={{ backgroundColor: '#f0fdf4' }}>
                <div className="w-3 h-3 rounded-full mr-2 flex-shrink-0" style={{ backgroundColor: '#22c55e' }} />
                <span className="text-gray-700">{component}</span>
              </div>
            ))}
          </div>

          <div className="mt-6 p-3 rounded-lg" style={{ backgroundColor: '#f0fdf4' }}>
            <p className="text-sm text-green-700">
              <strong>Note:</strong> This model is specifically trained for Single Line Diagram (SLD) electrical components.
              Component recognition accuracy depends on image quality, diagram clarity, and component visibility.
            </p>
          </div>
        </div>

        {/* Interactive Component Viewer */}
        {showInteractiveViewer && results && imageUrl && (
          <InteractiveComponentViewer
            imageUrl={imageUrl}
            detections={results.detections}
            imageDimensions={results.image_dimensions}
            onClose={() => setShowInteractiveViewer(false)}
          />
        )}

        {/* Interactive PDF Viewer */}
        {showPdfViewer && pdfResults && (
          <InteractivePDFViewer
            pdfResult={pdfResults}
            onClose={() => setShowPdfViewer(false)}
            onExport={() => {
              // TODO: Implement PDF export functionality
              toast.success('Export functionality coming soon!');
            }}
          />
        )}

      </div>
    </div>
  );
};

export default ComponentDetectionPage;

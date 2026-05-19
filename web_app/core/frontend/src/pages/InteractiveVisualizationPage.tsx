import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Share2, Settings, Camera } from 'lucide-react';
import toast from 'react-hot-toast';
import InteractiveVisualization from '../components/InteractiveVisualization';

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

interface TextElement {
  text: string;
  confidence: number;
  bounding_box: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
}

interface LocationState {
  imageFile: File | null;
  detections?: ComponentDetection[];
  textElements?: TextElement[];
  imageDimensions: {
    width: number;
    height: number;
  };
  processingTime: number;
  modelInfo: any;
  isRealtime?: boolean;
  detectionType?: 'component' | 'text';
}

const InteractiveVisualizationPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState<LocationState | null>(null);

  useEffect(() => {
    // Get data from navigation state
    const state = location.state as LocationState;

    if (!state) {
      toast.error('No visualization data found. Please run detection first.');
      navigate('/component-detection');
      return;
    }

    // Determine detection type and validate data
    const hasComponentData = state.detections && state.detections.length > 0;
    const hasTextData = state.textElements && state.textElements.length > 0;
    const isRealtimeComponent = state.isRealtime && hasComponentData;

    if (!hasComponentData && !hasTextData && !isRealtimeComponent) {
      // This should rarely happen now since ComponentDetectionPage checks for empty results
      console.warn('InteractiveVisualizationPage received empty detection results');
      toast.error('Invalid detection data received. Redirecting back to detection page.');
      navigate('/component-detection');
      return;
    }

    // Set detection type for UI rendering
    const detectionType = hasTextData ? 'text' : 'component';
    setData({ ...state, detectionType });
  }, [location.state, navigate]);

  const handleBackToResults = () => {
    const targetPage = data?.detectionType === 'text' ? '/text-detection' : '/component-detection';

    if (data?.detectionType === 'text') {
      // Navigate back to text detection page
      navigate(targetPage, {
        state: {
          results: data ? {
            text_elements: data.textElements,
            image_dimensions: data.imageDimensions,
            processing_time: data.processingTime
          } : null,
          selectedFile: data?.imageFile
        }
      });
    } else {
      // Navigate back to component detection page
      navigate(targetPage, {
        state: {
          results: data ? {
            detections: data.detections,
            image_dimensions: data.imageDimensions,
            processing_time: data.processingTime,
            model_info: data.modelInfo
          } : null,
          selectedFile: data?.imageFile
        }
      });
    }
  };

  const handleExportResults = () => {
    if (!data) return;

    let summary: any;
    let filename: string;

    if (data.detectionType === 'text') {
      // Create summary for text detection results
      summary = {
        timestamp: new Date().toISOString(),
        detection_type: 'text',
        image_info: data.imageFile ? {
          name: data.imageFile.name,
          size: data.imageFile.size,
          dimensions: data.imageDimensions
        } : { dimensions: data.imageDimensions },
        detection_summary: {
          total_text_elements: data.textElements?.length || 0,
          processing_time: data.processingTime
        },
        text_elements: data.textElements?.map((element, index) => ({
          id: index + 1,
          text: element.text,
          confidence: Math.round(element.confidence * 100),
          position: {
            x: element.bounding_box.left,
            y: element.bounding_box.top,
            width: element.bounding_box.width,
            height: element.bounding_box.height
          }
        })) || []
      };
      filename = `text_detection_${Date.now()}.json`;
    } else {
      // Create summary for component detection results
      summary = {
        timestamp: new Date().toISOString(),
        detection_type: 'component',
        image_info: data.imageFile ? {
          name: data.imageFile.name,
          size: data.imageFile.size,
          dimensions: data.imageDimensions
        } : {
          dimensions: data.imageDimensions,
          source: data.isRealtime ? 'real-time camera' : 'uploaded image'
        },
        detection_summary: {
          total_components: data.detections?.length || 0,
          processing_time: data.processingTime,
          model_info: data.modelInfo
        },
        detections: data.detections?.map((detection, index) => ({
          id: index + 1,
          component: detection.class_name,
          confidence: Math.round(detection.confidence * 100),
          position: {
            x: detection.bbox.x1,
            y: detection.bbox.y1,
            width: detection.bbox.x2 - detection.bbox.x1,
            height: detection.bbox.y2 - detection.bbox.y1
          },
          area: detection.area
        })) || []
      };
      filename = `component_detection_${Date.now()}.json`;
    }

    // Download as JSON
    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success('Results exported successfully!');
  };

  const handleShareResults = async () => {
    if (!data) return;

    const shareData = {
      title: 'SLD Component Detection Results',
      text: `Detected ${data.detections?.length || 0} electrical components in SLD diagram`,
      url: window.location.href
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        toast.success('Results shared successfully!');
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(
          `${shareData.title}\n${shareData.text}\n${shareData.url}`
        );
        toast.success('Results copied to clipboard!');
      }
    } catch (error) {
      console.error('Error sharing:', error);
      toast.error('Failed to share results');
    }
  };

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading visualization...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between py-4 sm:h-16 gap-4">
            <div className="flex items-center">
              <button
                onClick={handleBackToResults}
                className="flex items-center text-gray-600 hover:text-gray-900 mr-4"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                <span className="hidden sm:inline">Back to Results</span>
                <span className="sm:hidden">Back</span>
              </button>
              <div>
                <h1 className="text-lg sm:text-xl font-semibold text-gray-900">
                  {data.detectionType === 'text' ? 'Interactive Text Visualization' : 'Interactive SLD Visualization'}
                </h1>
                <p className="text-xs sm:text-sm text-gray-500">
                  {data.imageFile ? data.imageFile.name : (data.isRealtime ? 'Real-time Camera Feed' : 'Uploaded Image')} • {' '}
                  {data.detectionType === 'text'
                    ? `${data.textElements?.length || 0} text elements detected`
                    : `${data.detections?.length || 0} components detected`
                  }
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 sm:space-x-3">
              <button
                onClick={handleShareResults}
                className="btn btn-outline text-xs sm:text-sm"
                title="Share Results"
              >
                <Share2 className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Share</span>
              </button>
              <button
                onClick={handleExportResults}
                className="btn btn-outline text-xs sm:text-sm"
                title="Export Results"
              >
                <Download className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Export</span>
              </button>
              <button
                className="btn btn-outline text-xs sm:text-sm"
                title="Settings"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 lg:py-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4 lg:mb-6">
          <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
            <div className="text-lg sm:text-2xl font-bold text-blue-600">
              {data.detectionType === 'text' ? (data.textElements?.length || 0) : (data.detections?.length || 0)}
            </div>
            <div className="text-xs sm:text-sm text-gray-600">
              {data.detectionType === 'text' ? 'Text Elements' : 'Components Found'}
            </div>
          </div>
          <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
            <div className="text-lg sm:text-2xl font-bold text-green-600">
              {data.processingTime.toFixed(2)}s
            </div>
            <div className="text-xs sm:text-sm text-gray-600">Processing Time</div>
          </div>
          <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
            <div className="text-lg sm:text-2xl font-bold text-purple-600">
              {data.imageDimensions.width}×{data.imageDimensions.height}
            </div>
            <div className="text-xs sm:text-sm text-gray-600">Image Resolution</div>
          </div>
          <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
            <div className="text-lg sm:text-2xl font-bold text-orange-600">
              {data.detectionType === 'text'
                ? Math.round(((data.textElements?.reduce((sum, d) => sum + d.confidence, 0) || 0) / (data.textElements?.length || 1)) * 100)
                : Math.round(((data.detections?.reduce((sum, d) => sum + d.confidence, 0) || 0) / (data.detections?.length || 1)) * 100)
              }%
            </div>
            <div className="text-xs sm:text-sm text-gray-600">Avg. Confidence</div>
          </div>
        </div>

        {/* Interactive Visualization */}
        {data.detectionType === 'component' && data.detections && data.imageFile && (
          <InteractiveVisualization
            imageFile={data.imageFile}
            detections={data.detections}
            imageDimensions={data.imageDimensions}
          />
        )}

        {data.detectionType === 'text' && data.textElements && data.imageFile && (
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Text Detection Results</h3>
            <p className="text-gray-600 mb-4">
              Text detection visualization will be implemented here. For now, showing detected text elements:
            </p>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {data.textElements.map((element, index) => (
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
        )}

        {data.isRealtime && !data.imageFile && (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <div className="text-gray-500">
              <Camera className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Real-time Detection Capture</h3>
              <p className="text-gray-600">
                This frame was captured from the real-time detection feed.
                The interactive visualization shows the detected components with their bounding boxes and confidence scores.
              </p>
            </div>
          </div>
        )}

        {/* Additional Information */}
        <div className="mt-4 lg:mt-6 bg-white rounded-lg shadow-sm p-3 sm:p-4 lg:p-6">
          <h3 className="text-base lg:text-lg font-semibold text-gray-900 mb-3 lg:mb-4">Detection Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2 text-sm lg:text-base">
                {data.detectionType === 'text' ? 'Text Elements' : 'Component Types Detected'}
              </h4>
              <div className="space-y-1">
                {data.detectionType === 'text' && data.textElements ? (
                  <div className="text-xs sm:text-sm text-gray-600">
                    {data.textElements.length} text elements detected
                  </div>
                ) : data.detections ? (
                  Object.entries(
                    data.detections.reduce((acc, detection) => {
                      acc[detection.class_name] = (acc[detection.class_name] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([component, count]) => (
                    <div key={component} className="flex justify-between text-xs sm:text-sm">
                      <span className="text-gray-600">{component}</span>
                      <span className="font-medium">{String(count)}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs sm:text-sm text-gray-500">No detections available</div>
                )}
              </div>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2 text-sm lg:text-base">Model Information</h4>
              <div className="space-y-1 text-xs sm:text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Device:</span>
                  <span className="font-medium">{data.modelInfo.device || 'CPU'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Confidence Threshold:</span>
                  <span className="font-medium">{data.modelInfo.confidence_threshold || '0.03'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">IoU Threshold:</span>
                  <span className="font-medium">{data.modelInfo.iou_threshold || '0.45'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveVisualizationPage;

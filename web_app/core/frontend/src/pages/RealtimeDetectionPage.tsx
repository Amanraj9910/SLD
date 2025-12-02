import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Zap, Download, X, Wifi, WifiOff } from 'lucide-react';
import toast from 'react-hot-toast';
import InteractiveVisualization from '../components/InteractiveVisualization.tsx';

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

const RealtimeDetectionPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [results, setResults] = useState<DetectionResult | null>(null);
  const [confidence, setConfidence] = useState(0.03);
  const [iouThreshold, setIouThreshold] = useState(0.45);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [logs, setLogs] = useState<string[]>([]);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    addLog('Connecting to YOLOv8x detection server...');

    try {
      // Connect to the backend WebSocket endpoint
      const wsUrl = `ws://localhost:8000/api/v1/realtime/detect`;
      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        setConnectionStatus('connected');
        setIsConnected(true);
        addLog('✅ Connected to YOLOv8x real-time detection server');
        toast.success('Connected to detection server');
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          addLog(`❌ Error parsing message: ${error}`);
        }
      };

      websocketRef.current.onclose = () => {
        setConnectionStatus('disconnected');
        setIsConnected(false);
        addLog('❌ Connection closed');
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          addLog('🔄 Attempting to reconnect...');
          connectWebSocket();
        }, 3000);
      };

      websocketRef.current.onerror = (error) => {
        setConnectionStatus('error');
        setIsConnected(false);
        addLog(`❌ WebSocket error: ${error}`);
        toast.error('Connection failed. Make sure the backend server is running.');
      };

    } catch (error) {
      setConnectionStatus('error');
      addLog(`❌ Failed to connect: ${error}`);
      toast.error('Failed to establish WebSocket connection');
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    setConnectionStatus('disconnected');
    setIsConnected(false);
    addLog('🔌 Disconnected from server');
  }, []); // eslint-disable-line react-hooks/exhaustive-deps



  // Handle detection results
  const handleDetectionResult = useCallback((result: DetectionResult) => {
    addLog(`🔍 Detection completed: ${result.detections.length} components found`);
    addLog(`⏱️ Processing time: ${(result.processing_time * 1000).toFixed(1)}ms`);

    setResults(result);
    setIsProcessing(false);
    toast.success(`Detected ${result.detections.length} components in ${(result.processing_time * 1000).toFixed(1)}ms`);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Add log entry
  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${message}`;
    setLogs(prev => [...prev.slice(-49), logEntry]); // Keep last 50 logs
  }, [setLogs]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connected':
        addLog(`🎉 ${message.message}`);
        if (message.server_info) {
          addLog(`📊 Model: ${message.server_info.model_type}`);
          addLog(`🎯 Confidence: ${message.server_info.confidence_threshold}`);
          addLog(`📋 Classes: ${message.server_info.supported_classes?.length || 0} supported`);
        }
        break;

      case 'detection_result':
        handleDetectionResult(message.data);
        break;

      case 'error':
        addLog(`❌ Server error: ${message.message}`);
        toast.error(`Detection error: ${message.message}`);
        setIsProcessing(false);
        break;

      case 'pong':
        addLog('🏓 Server responded to ping');
        break;

      default:
        addLog(`❓ Unknown message type: ${message.type}`);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // File upload handling
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      addLog(`📁 Selected file: ${file.name}`);
      toast.success(`Selected: ${file.name}`);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.bmp', '.tiff']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false
  });

  // Process image with YOLOv8x
  const processImage = async () => {
    if (!selectedFile) {
      toast.error('Please select an image first');
      return;
    }

    if (!isConnected) {
      toast.error('Not connected to detection server');
      return;
    }

    setIsProcessing(true);
    addLog(`🚀 Sending image for YOLOv8x detection: ${selectedFile.name}`);

    try {
      // Convert file to base64
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result as string;
        
        // Send detection request via WebSocket
        const message = {
          type: 'detect_image',
          image: base64Data,
          image_id: `${selectedFile.name}_${Date.now()}`,
          confidence_threshold: confidence,
          iou_threshold: iouThreshold
        };

        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify(message));
          addLog('📤 Image sent to YOLOv8x model for processing...');
        } else {
          throw new Error('WebSocket connection not available');
        }
      };
      
      reader.onerror = () => {
        throw new Error('Failed to read image file');
      };
      
      reader.readAsDataURL(selectedFile);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process image';
      toast.error(errorMessage);
      addLog(`❌ Error: ${errorMessage}`);
      setIsProcessing(false);
    }
  };

  // Auto-connect on component mount
  useEffect(() => {
    connectWebSocket();
    addLog('🚀 Real-time YOLOv8x detection system initialized');

    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]); // eslint-disable-line react-hooks/exhaustive-deps

  // Connection status indicator
  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'connecting': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <Wifi className="w-4 h-4" />;
      case 'connecting': return <div className="w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin" />;
      default: return <WifiOff className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                🔍 Real-time YOLOv8x Component Detection
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Live electrical component detection using trained YOLOv8x model
              </p>
            </div>
            
            {/* Connection Status */}
            <div className={`mt-3 sm:mt-0 flex items-center gap-2 px-3 py-2 rounded-lg border ${getConnectionStatusColor()}`}>
              {getConnectionIcon()}
              <span className="text-sm font-medium">
                {connectionStatus === 'connected' && 'Connected to YOLOv8x'}
                {connectionStatus === 'connecting' && 'Connecting...'}
                {connectionStatus === 'disconnected' && 'Disconnected'}
                {connectionStatus === 'error' && 'Connection Error'}
              </span>
              {connectionStatus !== 'connected' && (
                <button
                  onClick={connectWebSocket}
                  className="ml-2 text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Reconnect
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {!results ? (
          /* Upload Section */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Upload SLD Image for Real-time Detection
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
                        Drag & drop an SLD image here, or click to select
                      </p>
                      <p className="text-sm text-gray-500">
                        Supports JPG, PNG, BMP, TIFF (max 10MB)
                      </p>
                    </div>
                  )}
                </div>

                {/* Selected File Info */}
                {selectedFile && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-blue-900">{selectedFile.name}</p>
                        <p className="text-sm text-blue-700">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Detection Controls */}
                <div className="mt-6 space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Confidence Threshold: {(confidence * 100).toFixed(1)}%
                      </label>
                      <input
                        type="range"
                        min="0.01"
                        max="1.0"
                        step="0.01"
                        value={confidence}
                        onChange={(e) => setConfidence(parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>1%</span>
                        <span>100%</span>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        IoU Threshold: {(iouThreshold * 100).toFixed(1)}%
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="0.9"
                        step="0.05"
                        value={iouThreshold}
                        onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>10%</span>
                        <span>90%</span>
                      </div>
                    </div>
                  </div>

                  {/* Process Button */}
                  <button
                    onClick={processImage}
                    disabled={!selectedFile || !isConnected || isProcessing}
                    className="w-full btn btn-primary flex items-center justify-center gap-2"
                  >
                    {isProcessing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Processing with YOLOv8x...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4" />
                        Detect Components with YOLOv8x
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Side Panel - Logs and Info */}
            <div className="space-y-6">
              {/* YOLOv8x Model Info */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  🤖 YOLOv8x Model Info
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Model:</span>
                    <span className="font-medium">YOLOv8x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Classes:</span>
                    <span className="font-medium">23 Electrical Components</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Primary Focus:</span>
                    <span className="font-medium">Circuit Breaker, HRC Fuse, Isolator</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Connection:</span>
                    <span className={`font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                      {isConnected ? 'Real-time WebSocket' : 'Disconnected'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Activity Log */}
              <div className="card p-6">
                <h3 className="text-lg font-semibent text-gray-900 mb-4">
                  📋 Activity Log
                </h3>
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs max-h-64 overflow-y-auto">
                  {logs.length === 0 ? (
                    <div className="text-gray-500">No activity yet...</div>
                  ) : (
                    logs.map((log, index) => (
                      <div key={index} className="mb-1">
                        {log}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Results Section - Using the same UI as InteractiveVisualizationPage */
          <div>
            {/* Quick Stats - Same as original */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4 lg:mb-6">
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
                <div className="text-lg sm:text-2xl font-bold text-blue-600">
                  {results.detections.length}
                </div>
                <div className="text-xs sm:text-sm text-gray-600">Components Found</div>
              </div>
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
                <div className="text-lg sm:text-2xl font-bold text-green-600">
                  {(results.processing_time * 1000).toFixed(1)}ms
                </div>
                <div className="text-xs sm:text-sm text-gray-600">Processing Time</div>
              </div>
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
                <div className="text-lg sm:text-2xl font-bold text-purple-600">
                  {results.image_dimensions.width}×{results.image_dimensions.height}
                </div>
                <div className="text-xs sm:text-sm text-gray-600">Image Resolution</div>
              </div>
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm">
                <div className="text-lg sm:text-2xl font-bold text-orange-600">
                  {results.detections.length > 0
                    ? Math.round((results.detections.reduce((sum, d) => sum + d.confidence, 0) / results.detections.length) * 100)
                    : 0}%
                </div>
                <div className="text-xs sm:text-sm text-gray-600">Avg. Confidence</div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2 mb-6">
              <button
                onClick={() => {
                  setResults(null);
                  setSelectedFile(null);
                  addLog('🔄 Reset for new detection');
                }}
                className="btn btn-secondary flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Detect Another Image
              </button>

              <button
                onClick={() => {
                  const dataStr = JSON.stringify(results, null, 2);
                  const dataBlob = new Blob([dataStr], { type: 'application/json' });
                  const url = URL.createObjectURL(dataBlob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `yolov8x_detection_${Date.now()}.json`;
                  link.click();
                  URL.revokeObjectURL(url);
                  toast.success('Detection results downloaded');
                }}
                className="btn btn-secondary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download Results
              </button>
            </div>

            {/* Interactive Visualization - Same component as original */}
            <InteractiveVisualization
              imageFile={selectedFile!}
              detections={results.detections}
              imageDimensions={results.image_dimensions}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default RealtimeDetectionPage;

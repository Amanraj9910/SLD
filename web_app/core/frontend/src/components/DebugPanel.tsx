import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, RefreshCw, X } from 'lucide-react';

const DebugPanel: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<'loading' | 'connected' | 'error'>('loading');
  const [apiTest, setApiTest] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [isVisible, setIsVisible] = useState<boolean>(true);

  const testBackendConnection = async () => {
    setBackendStatus('loading');
    setApiTest('loading');
    setErrorMessage('');

    try {
      // Test basic health endpoint
      const healthResponse = await fetch('/health');
      if (!healthResponse.ok) {
        throw new Error(`Health check failed: ${healthResponse.status}`);
      }
      const healthData = await healthResponse.json();
      console.log('Health check:', healthData);
      setBackendStatus('connected');

      // Test API endpoint
      const apiResponse = await fetch('/api/test');
      if (!apiResponse.ok) {
        throw new Error(`API test failed: ${apiResponse.status}`);
      }
      const apiData = await apiResponse.json();
      console.log('API test:', apiData);
      setApiTest('success');

    } catch (error) {
      console.error('Connection test failed:', error);
      setBackendStatus('error');
      setApiTest('error');
      setErrorMessage(error instanceof Error ? error.message : 'Unknown error');
    }
  };

  useEffect(() => {
    testBackendConnection();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'loading':
        return <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />;
      case 'connected':
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <RefreshCw className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'loading':
        return 'Testing...';
      case 'connected':
      case 'success':
        return 'Connected';
      case 'error':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm z-50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">Connection Status</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={testBackendConnection}
            className="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Backend:</span>
          <div className="flex items-center space-x-2">
            {getStatusIcon(backendStatus)}
            <span className="text-sm">{getStatusText(backendStatus)}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">API:</span>
          <div className="flex items-center space-x-2">
            {getStatusIcon(apiTest)}
            <span className="text-sm">{getStatusText(apiTest)}</span>
          </div>
        </div>

        {errorMessage && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            {errorMessage}
          </div>
        )}

        <div className="mt-3 pt-2 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            <div>Frontend: localhost:3000</div>
            <div>Backend: localhost:8000</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebugPanel;

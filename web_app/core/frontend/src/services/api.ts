// API service functions for SLD Processing Platform
const BASE_URL = "https://sld-d5fhdrdxendcdndb.australiacentral-01.azurewebsites.net";

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Base API request function with error handling
 */
async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${BASE_URL}${url}`, {

      ...options,
      headers: {
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorMessage;
      } catch {
        // If not JSON, use the text as error message
        errorMessage = errorText || errorMessage;
      }
      
      return {
        success: false,
        error: errorMessage,
      };
    }

    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    console.error('API request failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Test backend connection
 */
export async function testConnection(): Promise<ApiResponse> {
  return apiRequest('/health');
}

/**
 * Test API endpoint
 */
export async function testApi(): Promise<ApiResponse> {
  return apiRequest('/api/test');
}

/**
 * Component detection API
 */
export async function detectComponents(
  file: File,
  options: {
    confidence_threshold?: number;
    iou_threshold?: number;
    save_visualization?: boolean;
    device?: string;
  } = {}
): Promise<ApiResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('confidence_threshold', (options.confidence_threshold || 0.01).toString());
  formData.append('iou_threshold', (options.iou_threshold || 0.3).toString());
  formData.append('save_visualization', (options.save_visualization || false).toString());
  formData.append('device', options.device || 'auto');

  return apiRequest('/api/v1/components/predict', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Text extraction API
 */
export async function extractText(
  file: File,
  options: {
    output_format?: string;
  } = {}
): Promise<ApiResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('output_format', options.output_format || 'detailed');

  return apiRequest('/api/v1/text/extract', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Create annotation project
 */
export async function createAnnotationProject(
  file: File,
  projectName: string,
  createdBy: string = 'user'
): Promise<ApiResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_name', projectName);
  formData.append('created_by', createdBy);

  return apiRequest('/api/v1/annotations/projects', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Get annotation project
 */
export async function getAnnotationProject(projectName: string): Promise<ApiResponse> {
  return apiRequest(`/api/v1/annotations/projects/${projectName}`);
}

/**
 * Health check for component detection
 */
export async function checkComponentHealth(): Promise<ApiResponse> {
  return apiRequest('/api/v1/components/health');
}

/**
 * Health check for text detection
 */
export async function checkTextHealth(): Promise<ApiResponse> {
  return apiRequest('/api/v1/text/health');
}

/**
 * Test Azure connection
 */
export async function testAzureConnection(): Promise<ApiResponse> {
  return apiRequest('/api/v1/text/test-connection', {
    method: 'POST',
  });
}

/**
 * Get available component classes
 */
export async function getComponentClasses(): Promise<ApiResponse> {
  return apiRequest('/api/v1/components/classes');
}

/**
 * Get supported formats for text detection
 */
export async function getSupportedFormats(): Promise<ApiResponse> {
  return apiRequest('/api/v1/text/supported-formats');
}

/**
 * Real-time detection WebSocket API
 */
export class RealtimeDetectionAPI {
  private websocket: WebSocket | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

constructor(private baseUrl: string = 'wss://sld-d5fhdrdxendcdndb.australiacentral-01.azurewebsites.net') {}


  /**
   * Connect to the real-time detection WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.baseUrl}/api/v1/realtime/detect`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
          this.reconnectAttempts = 0;
          resolve();
        };

        this.websocket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            const handler = this.messageHandlers.get(message.type);
            if (handler) {
              handler(message);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.websocket.onclose = () => {
          this.websocket = null;
          this.attemptReconnect();
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }

  /**
   * Send message to server
   */
  private sendMessage(message: any): void {
    if (this.isConnected()) {
      this.websocket!.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  /**
   * Register message handler
   */
  onMessage(type: string, handler: (data: any) => void): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Remove message handler
   */
  offMessage(type: string): void {
    this.messageHandlers.delete(type);
  }

  /**
   * Send image for real-time detection
   */
  detectImage(
    imageData: string,
    options: {
      imageId?: string;
      confidenceThreshold?: number;
      iouThreshold?: number;
    } = {}
  ): void {
    const message = {
      type: 'detect_image',
      image: imageData,
      image_id: options.imageId || `realtime_${Date.now()}`,
      confidence_threshold: options.confidenceThreshold || 0.03,
      iou_threshold: options.iouThreshold || 0.45
    };

    this.sendMessage(message);
  }

  /**
   * Send ping to server
   */
  ping(): void {
    this.sendMessage({ type: 'ping' });
  }

  /**
   * Get server status
   */
  getStatus(): void {
    this.sendMessage({ type: 'get_status' });
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect().catch(() => {
          // Reconnection failed, will try again
        });
      }, this.reconnectDelay);
    }
  }
}

/**
 * Get real-time detection service info
 */
export async function getRealtimeDetectionInfo(): Promise<ApiResponse> {
  return apiRequest('/api/v1/realtime/info');
}

/**
 * Health check for real-time detection service
 */
export async function checkRealtimeDetectionHealth(): Promise<ApiResponse> {
  return apiRequest('/api/v1/realtime/health');
}

/**
 * Utility function to validate file before upload (supports images and PDFs)
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'application/pdf'];
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Please upload JPG, PNG, BMP, TIFF, or PDF files.',
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'File too large. Maximum size is 10MB.',
    };
  }

  return { valid: true };
}

/**
 * Utility function to validate document file before upload
 */
export function validateDocumentFile(file: File): { valid: boolean; error?: string } {
  const validTypes = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff',
    'application/pdf'
  ];
  const maxSize = 500 * 1024 * 1024; // 500MB

  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Please upload JPG, PNG, BMP, TIFF, or PDF files.',
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'File too large. Maximum size is 500MB.',
    };
  }

  return { valid: true };
}

/**
 * Detect components in a PDF document
 */
export async function detectComponentsInPDF(
  file: File,
  saveVisualizations: boolean = false
): Promise<ApiResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('save_visualizations', saveVisualizations.toString());

  return apiRequest('/api/v1/pdf/detect', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Get PDF information without processing
 */
export async function getPDFInfo(file: File): Promise<ApiResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return apiRequest('/api/v1/pdf/info', {
    method: 'POST',  // Changed to POST since we're sending form data
    body: formData,
  });
}

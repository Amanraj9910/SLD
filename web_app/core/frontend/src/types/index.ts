// Type definitions for SLD Processing Platform

export interface ComponentDetection {
  class_name: string;
  class_id: number;
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

export interface ComponentDetectionResponse {
  success: boolean;
  message: string;
  image_path: string;
  image_dimensions: {
    width: number;
    height: number;
  };
  processing_time: number;
  detections: ComponentDetection[];
  model_info: {
    device?: string;
    model_path?: string;
  };
  visualization_url?: string;
}

export interface TextElement {
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
  center?: {
    x: number;
    y: number;
  };
  area?: number;
}

export interface TextDetectionResponse {
  success: boolean;
  message: string;
  document_path: string;
  document_type: string;
  page_count: number;
  processing_time: number;
  total_text_length: number;
  text_elements: TextElement[];
  image_dimensions?: {
    width: number;
    height: number;
  };
  service_info: {
    [key: string]: string;
  };
}

export interface Annotation {
  class_id: number;
  class_name: string;
  bbox: number[]; // [x_center, y_center, width, height]
  confidence: number;
  annotator: string;
}

export interface AnnotationProject {
  project_name: string;
  image_path: string;
  image_dimensions: {
    width: number;
    height: number;
  };
  annotations: Annotation[];
  class_names: { [key: number]: string };
  created_by: string;
  last_modified?: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

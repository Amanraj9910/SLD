// Utility functions for SLD Processing Platform

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combine class names with Tailwind CSS merge
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format duration in human readable format
 */
export function formatDuration(seconds: number): string {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  }
  if (seconds < 60) {
    return `${seconds.toFixed(2)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

/**
 * Validate file type
 */
export function isValidImageFile(file: File): boolean {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
  return validTypes.includes(file.type);
}

/**
 * Validate document file type
 */
export function isValidDocumentFile(file: File): boolean {
  const validTypes = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff',
    'application/pdf'
  ];
  return validTypes.includes(file.type);
}

/**
 * Generate random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Download file from blob
 */
export function downloadFile(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy text: ', err);
    return false;
  }
}

/**
 * Format confidence percentage
 */
export function formatConfidence(confidence: number): string {
  return `${(confidence * 100).toFixed(1)}%`;
}

/**
 * Calculate bounding box area
 */
export function calculateBboxArea(bbox: { x1: number; y1: number; x2: number; y2: number }): number {
  return Math.abs((bbox.x2 - bbox.x1) * (bbox.y2 - bbox.y1));
}

/**
 * Convert YOLO format to pixel coordinates
 */
export function yoloToPixel(
  yolo: [number, number, number, number],
  imageWidth: number,
  imageHeight: number
): { x1: number; y1: number; x2: number; y2: number } {
  const [x_center, y_center, width, height] = yolo;
  
  const x1 = (x_center - width / 2) * imageWidth;
  const y1 = (y_center - height / 2) * imageHeight;
  const x2 = (x_center + width / 2) * imageWidth;
  const y2 = (y_center + height / 2) * imageHeight;
  
  return { x1, y1, x2, y2 };
}

/**
 * Convert pixel coordinates to YOLO format
 */
export function pixelToYolo(
  pixel: { x1: number; y1: number; x2: number; y2: number },
  imageWidth: number,
  imageHeight: number
): [number, number, number, number] {
  const x_center = ((pixel.x1 + pixel.x2) / 2) / imageWidth;
  const y_center = ((pixel.y1 + pixel.y2) / 2) / imageHeight;
  const width = Math.abs(pixel.x2 - pixel.x1) / imageWidth;
  const height = Math.abs(pixel.y2 - pixel.y1) / imageHeight;
  
  return [x_center, y_center, width, height];
}

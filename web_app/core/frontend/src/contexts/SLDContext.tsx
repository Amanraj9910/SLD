import React, { createContext, useContext, useState, ReactNode } from 'react';

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

interface SLDData {
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
    endpoint: string;
    model_id: string;
    api_version: string;
  };
}

interface SLDContextType {
  sldData: SLDData | null;
  setSLDData: (data: SLDData | null) => void;
  currentImageUrl: string | null;
  setCurrentImageUrl: (url: string | null) => void;
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
}

const SLDContext = createContext<SLDContextType | undefined>(undefined);

export const useSLD = () => {
  const context = useContext(SLDContext);
  if (context === undefined) {
    throw new Error('useSLD must be used within a SLDProvider');
  }
  return context;
};

interface SLDProviderProps {
  children: ReactNode;
}

export const SLDProvider: React.FC<SLDProviderProps> = ({ children }) => {
  const [sldData, setSLDData] = useState<SLDData | null>(null);
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const value: SLDContextType = {
    sldData,
    setSLDData,
    currentImageUrl,
    setCurrentImageUrl,
    isProcessing,
    setIsProcessing,
  };

  return (
    <SLDContext.Provider value={value}>
      {children}
    </SLDContext.Provider>
  );
};

export default SLDContext;

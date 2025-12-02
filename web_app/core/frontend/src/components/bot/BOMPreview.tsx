import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileText, X, ChevronDown, ChevronUp } from 'lucide-react';
import { BOMData, BOMComponent, exportBOMToCSV, exportBOMToTXT, downloadFile } from '../../utils/bomGenerator';
import { EnhancedTable, CollapsibleSection } from './MarkdownRenderer';

interface BOMPreviewProps {
  bomData: BOMData;
  onClose: () => void;
  className?: string;
}

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (format: string) => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose, onExport }) => {
  if (!isOpen) return null;

  const exportFormats = [
    {
      format: 'csv',
      icon: FileSpreadsheet,
      title: 'CSV (Excel Compatible)',
      description: 'Comma-separated values for spreadsheet applications',
      extension: '.csv'
    },
    {
      format: 'txt',
      icon: FileText,
      title: 'Text Summary',
      description: 'Human-readable text format with detailed analysis',
      extension: '.txt'
    }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Export Bill of Materials</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 space-y-3">
          {exportFormats.map(({ format, icon: Icon, title, description, extension }) => (
            <button
              key={format}
              onClick={() => {
                onExport(format);
                onClose();
              }}
              className="w-full p-4 border border-gray-200 rounded-lg hover:border-red-300 hover:bg-red-50 transition-all duration-200 text-left group"
            >
              <div className="flex items-start space-x-3">
                <div className="bg-red-100 group-hover:bg-red-200 rounded-lg p-2 transition-colors">
                  <Icon className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900">{title}</h4>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {extension}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
        
        <div className="px-4 pb-4">
          <button
            onClick={onClose}
            className="w-full py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

const BOMPreview: React.FC<BOMPreviewProps> = ({ bomData, onClose, className = '' }) => {
  const [showExportModal, setShowExportModal] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    summary: true,
    components: true,
    details: false
  });

  const handleExport = (format: string) => {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    
    if (format === 'csv') {
      const csvContent = exportBOMToCSV(bomData);
      downloadFile(csvContent, `BOM_${timestamp}.csv`, 'text/csv');
    } else if (format === 'txt') {
      const txtContent = exportBOMToTXT(bomData);
      downloadFile(txtContent, `BOM_${timestamp}.txt`, 'text/plain');
    }
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Prepare table data
  const tableHeaders = ['Item#', 'Component Type', 'Description', 'Qty', 'Specifications', 'Confidence'];
  const tableRows = bomData.components.map(comp => [
    comp.itemNumber.toString(),
    comp.componentType,
    comp.description,
    comp.quantity.toString(),
    comp.specifications.join(', ') || 'None',
    `${Math.round(comp.confidence * 100)}%`
  ]);

  // Group components by category
  const componentsByCategory = bomData.components.reduce((acc, comp) => {
    const category = getComponentCategory(comp.componentType);
    if (!acc[category]) acc[category] = [];
    acc[category].push(comp);
    return acc;
  }, {} as Record<string, BOMComponent[]>);

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-green-100">
        <div className="flex items-center space-x-3">
          <div className="bg-green-500 rounded-full p-2">
            <FileSpreadsheet className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Bill of Materials</h3>
            <p className="text-sm text-gray-600">
              Generated from SLD analysis • {bomData.components.length} unique components
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowExportModal(true)}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
        {/* Summary Section */}
        <CollapsibleSection
          title="Summary Statistics"
          defaultExpanded={expandedSections.summary}
          className="border-green-200"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {bomData.summary.totalComponents}
              </div>
              <div className="text-sm text-blue-800">Total Components</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {bomData.summary.uniqueTypes}
              </div>
              <div className="text-sm text-purple-800">Unique Types</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(bomData.summary.averageConfidence * 100)}%
              </div>
              <div className="text-sm text-green-800">Avg Confidence</div>
            </div>
            <div className="bg-orange-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {bomData.metadata.totalTextElements}
              </div>
              <div className="text-sm text-orange-800">Text Elements</div>
            </div>
          </div>
        </CollapsibleSection>

        {/* Components Table */}
        <CollapsibleSection
          title="Component List"
          defaultExpanded={expandedSections.components}
          className="border-green-200"
        >
          <EnhancedTable
            headers={tableHeaders}
            rows={tableRows}
            className="text-xs"
          />
        </CollapsibleSection>

        {/* Detailed Breakdown */}
        <CollapsibleSection
          title="Category Breakdown"
          defaultExpanded={expandedSections.details}
          className="border-green-200"
        >
          <div className="space-y-4">
            {Object.entries(componentsByCategory).map(([category, components]) => (
              <div key={category} className="border border-gray-200 rounded-lg p-3">
                <h4 className="font-medium text-gray-900 mb-2 flex items-center justify-between">
                  <span>{category}</span>
                  <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                    {components.reduce((sum, comp) => sum + comp.quantity, 0)} items
                  </span>
                </h4>
                <div className="space-y-1">
                  {components.map(comp => (
                    <div key={comp.id} className="text-sm text-gray-600 flex justify-between">
                      <span>{comp.description}</span>
                      <span className="font-medium">×{comp.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      </div>

      {/* Export Modal */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleExport}
      />
    </div>
  );
};

// Helper function to categorize components
const getComponentCategory = (componentType: string): string => {
  const categoryMap: Record<string, string> = {
    'Circuit Breaker': 'Protection',
    'Current Transformer': 'Measurement',
    'Potential Transformer': 'Measurement',
    'Transformer': 'Power Equipment',
    'Generator': 'Generation',
    'Motor': 'Loads',
    'Bus Bar': 'Distribution',
    'Isolator': 'Switching',
    'Relay': 'Protection',
    'Capacitor': 'Compensation',
    'Cable': 'Connections',
    'Load': 'Loads'
  };

  return categoryMap[componentType] || 'Other';
};

export default BOMPreview;

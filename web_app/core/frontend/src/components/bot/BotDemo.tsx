import React, { useState } from 'react';
import { Play, RefreshCw, FileText, Download } from 'lucide-react';
import SLDBot from '../SLDBot';
import MarkdownRenderer from './MarkdownRenderer';
import BOMPreview from './BOMPreview';
import { mockSLDData, mockMarkdownResponse, mockBOMData } from './BotTestData';

const BotDemo: React.FC = () => {
  const [showBot, setShowBot] = useState(false);
  const [showMarkdownDemo, setShowMarkdownDemo] = useState(false);
  const [showBOMDemo, setShowBOMDemo] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            SLD Bot Enhancement Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience the enhanced SLD Bot with improved UI/UX, markdown rendering, 
            BOM generation, and interactive features.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {/* SLD Bot Demo */}
          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="bg-red-100 rounded-full p-3 w-12 h-12 mb-4">
              <Play className="w-6 h-6 text-red-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Enhanced SLD Bot
            </h3>
            <p className="text-gray-600 mb-4">
              Test the improved chat interface with fullscreen mode, 
              dismissible sample questions, and markdown rendering.
            </p>
            <button
              onClick={() => setShowBot(!showBot)}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {showBot ? 'Hide Bot' : 'Show Bot'}
            </button>
          </div>

          {/* Markdown Rendering Demo */}
          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mb-4">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Markdown Rendering
            </h3>
            <p className="text-gray-600 mb-4">
              See how bot responses are formatted with tables, 
              collapsible sections, and enhanced typography.
            </p>
            <button
              onClick={() => setShowMarkdownDemo(!showMarkdownDemo)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {showMarkdownDemo ? 'Hide Demo' : 'Show Demo'}
            </button>
          </div>

          {/* BOM Generation Demo */}
          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="bg-green-100 rounded-full p-3 w-12 h-12 mb-4">
              <Download className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              BOM Generation
            </h3>
            <p className="text-gray-600 mb-4">
              Experience the complete Bill of Materials workflow 
              with preview and multi-format export.
            </p>
            <button
              onClick={() => setShowBOMDemo(!showBOMDemo)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {showBOMDemo ? 'Hide BOM' : 'Show BOM'}
            </button>
          </div>
        </div>

        {/* Demo Sections */}
        
        {/* Markdown Demo */}
        {showMarkdownDemo && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-gray-900">
                Markdown Rendering Demo
              </h2>
              <button
                onClick={() => setShowMarkdownDemo(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <MarkdownRenderer content={mockMarkdownResponse} />
            </div>
          </div>
        )}

        {/* BOM Demo */}
        {showBOMDemo && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-gray-900">
                BOM Generation Demo
              </h2>
              <button
                onClick={() => setShowBOMDemo(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <BOMPreview
              bomData={mockBOMData}
              onClose={() => setShowBOMDemo(false)}
            />
          </div>
        )}

        {/* Features List */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            ✨ Enhancement Features
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                🎨 UI/UX Improvements
              </h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Enhanced markdown rendering with tables and sections</li>
                <li>• Dismissible sample questions with animations</li>
                <li>• Fullscreen mode with navbar preservation</li>
                <li>• Improved typography and spacing</li>
                <li>• Smooth transitions and hover effects</li>
                <li>• Responsive design for all screen sizes</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                ⚡ Functionality Enhancements
              </h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Complete BOM generation workflow</li>
                <li>• Multi-format export (CSV, TXT)</li>
                <li>• Component extraction and analysis</li>
                <li>• Collapsible content sections</li>
                <li>• Copy-to-clipboard functionality</li>
                <li>• Enhanced error handling and loading states</li>
              </ul>
            </div>
          </div>

          <div className="mt-8 p-4 bg-gradient-to-r from-red-50 to-red-100 rounded-lg">
            <h4 className="font-semibold text-red-800 mb-2">
              🚀 Ready for Production
            </h4>
            <p className="text-red-700 text-sm">
              All enhancements are implemented with proper TypeScript interfaces, 
              error handling, accessibility features, and comprehensive testing support.
            </p>
          </div>
        </div>
      </div>

      {/* SLD Bot */}
      {showBot && (
        <SLDBot
          sldData={mockSLDData}
          isVisible={true}
        />
      )}
    </div>
  );
};

export default BotDemo;

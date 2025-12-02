import React from 'react';
import { Play, FileImage, MousePointer, Square, Download } from 'lucide-react';

const AnnotationToolDemo: React.FC = () => {
  const features = [
    {
      icon: FileImage,
      title: "Image Gallery",
      description: "Browse and manage all your annotated SLD images in an organized gallery view"
    },
    {
      icon: Square,
      title: "Interactive Annotation",
      description: "Draw precise bounding boxes around electrical components with real-time feedback"
    },
    {
      icon: MousePointer,
      title: "Smart Selection",
      description: "Select, move, and resize annotations with intuitive mouse controls"
    },
    {
      icon: Download,
      title: "Export Options",
      description: "Download annotated images and JSON data for training machine learning models"
    }
  ];

  const steps = [
    "Upload your SLD image and create a new project",
    "Select component types from the dropdown or add custom ones",
    "Use the rectangle tool to draw boxes around components",
    "Fine-tune annotations with select and move tools",
    "Export your annotations as JSON for further processing"
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          SLD Annotation Tool
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Create precise annotations for Single Line Diagrams with our interactive tool. 
          Perfect for training AI models and component recognition systems.
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-2 gap-8 mb-12">
        {features.map((feature, index) => (
          <div key={index} className="card p-6 hover:shadow-medium transition-all duration-200">
            <div className="flex items-start space-x-4">
              <div className="bg-primary-100 p-3 rounded-lg">
                <feature.icon className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* How it Works */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          How It Works
        </h2>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={index} className="flex items-start space-x-4">
              <div className="bg-primary-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                {index + 1}
              </div>
              <p className="text-gray-700 pt-1">
                {step}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Component Types */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Supported Component Types
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            'Circuit Breaker',
            'HRC Fuse',
            'Isolator',
            'Contactor',
            'Relay',
            'Transformer',
            'Motor',
            'Generator',
            'Capacitor',
            'Resistor'
          ].map((component) => (
            <div key={component} className="bg-gray-100 rounded-lg p-3 text-center">
              <span className="text-sm font-medium text-gray-700">
                {component}
              </span>
            </div>
          ))}
        </div>
        <p className="text-center text-gray-600 mt-4">
          + Add custom component types as needed
        </p>
      </div>

      {/* Key Benefits */}
      <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-8 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Key Benefits
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">
              Precise
            </div>
            <p className="text-gray-700">
              Pixel-perfect annotations with zoom and pan capabilities
            </p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">
              Efficient
            </div>
            <p className="text-gray-700">
              Streamlined workflow with intuitive tools and shortcuts
            </p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">
              Exportable
            </div>
            <p className="text-gray-700">
              JSON format compatible with ML training pipelines
            </p>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="text-center">
        <button className="btn btn-primary text-lg px-8 py-3">
          <Play className="w-5 h-5 mr-2" />
          Start Annotating
        </button>
        <p className="text-gray-600 mt-4">
          Ready to create your first annotation project?
        </p>
      </div>
    </div>
  );
};

export default AnnotationToolDemo;

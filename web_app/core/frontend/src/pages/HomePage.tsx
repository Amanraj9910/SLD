import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Zap, 
  FileText, 
  Edit3, 
  ArrowRight, 
  CheckCircle, 
  Upload,
  Download,
  Eye
} from 'lucide-react';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: Zap,
      title: 'Component Detection',
      description: 'AI-powered detection of electrical components in SLD diagrams using advanced models.',
      link: '/component-detection',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    {
      icon: FileText,
      title: 'Text Detection',
      description: 'Extract text from diagrams with precise bounding boxes using HOSHO Document Analyser.',
      link: '/text-detection',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      icon: Edit3,
      title: 'Annotation Tool',
      description: 'Manual labeling interface for creating training datasets and validating AI predictions.',
      link: '/annotation-tool',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  const benefits = [
    'Automated component recognition with 90%+ accuracy',
    'High-precision text extraction with confidence scores',
    'Manual annotation tools for quality control',
    'Export to Structured format for model training',
    'RESTful API for easy integration',
    'Scalable cloud-based processing',
  ];

  const workflow = [
    {
      icon: Upload,
      title: 'Upload',
      description: 'Upload your SLD diagram (JPG, PNG, PDF)',
    },
    {
      icon: Zap,
      title: 'Process',
      description: 'AI analyzes and detects components and text',
    },
    {
      icon: Eye,
      title: 'Review',
      description: 'Validate results and make corrections',
    },
    {
      icon: Download,
      title: 'Export',
      description: 'Download results in multiple formats',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-gray-50 to-white py-20 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 mb-6">
              Single Line Diagram
              <span className="text-gradient block">Processing Platform</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Advanced AI-powered analysis of electrical single line diagrams with component detection, 
              text extraction, and manual annotation capabilities.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/component-detection"
                className="btn btn-primary text-lg px-8 py-3"
              >
                <Zap className="w-5 h-5 mr-2" />
                Start Processing
              </Link>
              <Link
                to="/about"
                className="btn btn-outline text-lg px-8 py-3"
              >
                Learn More
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to analyze and process single line diagrams efficiently.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Link
                key={index}
                to={feature.link}
                className="card card-hover p-8 text-center group"
              >
                <div className={`w-16 h-16 ${feature.bgColor} rounded-xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-200`}>
                  <feature.icon className={`w-8 h-8 ${feature.color}`} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {feature.title}
                </h3>
                <p className="text-gray-600 mb-6">
                  {feature.description}
                </p>
                <div className="flex items-center justify-center text-primary-600 font-medium group-hover:text-primary-700">
                  Try it now
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Simple 4-step process to analyze your electrical diagrams.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {workflow.map((step, index) => (
              <div key={index} className="text-center">
                <div className="relative">
                  <div className="w-16 h-16 bg-primary-500 rounded-xl flex items-center justify-center mx-auto mb-6">
                    <step.icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  {index < workflow.length - 1 && (
                    <div className="hidden md:block absolute top-8 left-full w-full h-0.5 bg-gray-300 -translate-y-1/2"></div>
                  )}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-gray-600">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
                Why Choose Our Platform?
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Built specifically for electrical engineering professionals who need 
                accurate, fast, and reliable diagram analysis.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start">
                    <CheckCircle className="w-6 h-6 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="aspect-video bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl flex items-center justify-center">
                <div className="text-center">
                  <Zap className="w-16 h-16 text-primary-500 mx-auto mb-4" />
                  <p className="text-primary-700 font-medium">
                    Interactive Demo Coming Soon
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Upload your first SLD diagram and experience the power of AI-driven analysis.
          </p>
          <Link
            to="/component-detection"
            className="inline-flex items-center px-8 py-3 bg-white text-primary-600 font-semibold rounded-lg hover:bg-gray-50 transition-colors duration-200"
          >
            <Zap className="w-5 h-5 mr-2" />
            Start Processing Now
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;

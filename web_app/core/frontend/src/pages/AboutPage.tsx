import React from 'react';
import {
  Zap,
  FileText,
  Edit3,
  Brain,
  Cloud,
  Shield,
  Users,
  Award,
  Github
} from 'lucide-react';

const AboutPage: React.FC = () => {
  const features = [
    {
      icon: Zap,
      title: 'AI-Powered Component Detection',
      description: 'Advanced HOSHO model trained specifically for electrical components in single line diagrams.',
      stats: '90%+ accuracy'
    },
    {
      icon: FileText,
      title: 'Intelligent Text Extraction',
      description: 'HOSHO Text Detector OCR with precise bounding boxes and confidence scores.',
      stats: '100+ languages'
    },
    {
      icon: Edit3,
      title: 'Manual Annotation Tools',
      description: 'Professional-grade annotation interface for creating training datasets and quality control.',
      stats: 'Structured export'
    },
    {
      icon: Brain,
      title: 'Machine Learning Ready',
      description: 'Export annotations in Structured format for training custom models and improving accuracy.',
      stats: 'Custom training'
    },
    {
      icon: Cloud,
      title: 'Cloud-Based Processing',
      description: 'Scalable cloud infrastructure for handling large volumes of diagram analysis.',
      stats: 'Unlimited scale'
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Secure processing with data encryption and compliance with industry standards.',
      stats: 'SOC 2 compliant'
    }
  ];

  const team = [
    {
      name: 'Development Team',
      role: 'Full-Stack Engineers',
      description: 'Experienced developers specializing in AI/ML applications and web technologies.',
      icon: Users
    },
    {
      name: 'AI Research Team',
      role: 'Machine Learning Engineers',
      description: 'Experts in computer vision, deep learning, and electrical engineering domain knowledge.',
      icon: Brain
    },
    {
      name: 'Quality Assurance',
      role: 'Testing & Validation',
      description: 'Ensuring accuracy, reliability, and performance across all platform features.',
      icon: Award
    }
  ];

  const technologies = [
    { name: 'YOLOv8', category: 'Computer Vision', description: 'State-of-the-art object detection' },
    { name: 'Azure Document Intelligence', category: 'OCR', description: 'Enterprise-grade text extraction' },
    { name: 'React + TypeScript', category: 'Frontend', description: 'Modern web application framework' },
    { name: 'FastAPI', category: 'Backend', description: 'High-performance Python API framework' },
    { name: 'PyTorch', category: 'ML Framework', description: 'Deep learning model training and inference' },
    { name: 'OpenCV', category: 'Image Processing', description: 'Computer vision and image manipulation' }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-gray-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
            About <span className="text-gradient">HOSHŌ DIGITAL</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            We're revolutionizing electrical engineering workflows with AI-powered analysis 
            of single line diagrams, making complex diagram processing accessible and efficient.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              <Github className="w-4 h-4 mr-2" />
              View on GitHub
            </a>
            <a
              href="/component-detection"
              className="btn btn-outline"
            >
              <Zap className="w-4 h-4 mr-2" />
              Get Started
            </a>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Our Mission
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                To empower electrical engineers and technicians with cutting-edge AI tools 
                that automate the analysis of single line diagrams, reducing manual effort 
                and improving accuracy in electrical system documentation.
              </p>
              <p className="text-lg text-gray-600 mb-8">
                We believe that by combining domain expertise with advanced machine learning, 
                we can transform how electrical diagrams are processed, analyzed, and understood.
              </p>
              <div className="grid grid-cols-2 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600">90%+</div>
                  <div className="text-sm text-gray-600">Detection Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600">10x</div>
                  <div className="text-sm text-gray-600">Faster Processing</div>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl flex items-center justify-center">
                <div className="text-center">
                  <Zap className="w-24 h-24 text-primary-500 mx-auto mb-4" />
                  <p className="text-primary-700 font-medium text-lg">
                    AI-Powered Analysis
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Platform Features
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive tools for every aspect of SLD analysis and processing.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card p-6 text-center">
                <div className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: '#f0fdf4' }}>
                  <feature.icon className="w-8 h-8 text-green-700" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {feature.title}
                </h3>
                <p className="text-gray-600 mb-4">
                  {feature.description}
                </p>
                <div className="inline-flex items-center px-3 py-1 bg-primary-100 text-primary-800 text-sm font-medium rounded-full">
                  {feature.stats}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Technology Stack
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Built with modern, proven technologies for reliability and performance.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {technologies.map((tech, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6 hover:border-primary-300 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{tech.name}</h3>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {tech.category}
                  </span>
                </div>
                <p className="text-gray-600 text-sm">{tech.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Our Team
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Passionate experts dedicated to advancing electrical engineering through AI.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {team.map((member, index) => (
              <div key={index} className="card p-8 text-center">
                <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <member.icon className="w-10 h-10 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {member.name}
                </h3>
                <p className="text-primary-600 font-medium mb-4">
                  {member.role}
                </p>
                <p className="text-gray-600">
                  {member.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Get Started Section */}
      <section className="py-20 bg-primary-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">
            Ready to Transform Your Workflow?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Join the future of electrical diagram analysis. Start processing your SLD diagrams today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/component-detection"
              className="inline-flex items-center px-8 py-3 bg-white text-primary-600 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Zap className="w-5 h-5 mr-2" />
              Get Started
            </a>
            <a
              href="/about"
              className="inline-flex items-center px-8 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-primary-600 transition-colors"
            >
              <FileText className="w-5 h-5 mr-2" />
              Learn More
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Upload, Save, Download, Plus, Trash2, ZoomIn, ZoomOut,
  Move, Square, MousePointer, ChevronLeft, ChevronRight, FileDown,
  Image as ImageIcon, Settings
} from 'lucide-react';
import toast from 'react-hot-toast';

// Type definitions
interface AnnotationBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  componentName: string;
  componentType: string;
  isSelected: boolean;
}

interface AnnotatedProject {
  id: string;
  name: string;
  imagePath: string;
  imageUrl: string;
  annotations: AnnotationBox[];
  createdAt: string;
  lastModified: string;
}

interface CanvasState {
  zoom: number;
  panX: number;
  panY: number;
  isDragging: boolean;
  isDrawing: boolean;
  startPoint: { x: number; y: number } | null;
  selectedTool: 'select' | 'rectangle' | 'move';
}

// Utility functions for data persistence
const STORAGE_KEY = 'sld_annotated_projects';

const saveProjectsToStorage = (projects: AnnotatedProject[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
  } catch (error) {
    console.error('Failed to save projects to localStorage:', error);
  }
};

const loadProjectsFromStorage = (): AnnotatedProject[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to load projects from localStorage:', error);
    return [];
  }
};

const generateProjectId = () => `project_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

const createImageUrl = (file: File): Promise<string> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.readAsDataURL(file);
  });
};

const AnnotationToolPage: React.FC = () => {
  const [annotatedProjects, setAnnotatedProjects] = useState<AnnotatedProject[]>([]);
  const [currentProject, setCurrentProject] = useState<any>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [showGallery, setShowGallery] = useState(true);

  // Load projects from localStorage on component mount
  useEffect(() => {
    const savedProjects = loadProjectsFromStorage();
    setAnnotatedProjects(savedProjects);
  }, []);

  const handleCreateProject = async (file: File, projectName: string) => {
    setIsCreating(true);

    try {
      // Create image URL for thumbnail and annotation
      const imageUrl = await createImageUrl(file);

      // Create new project object
      const newProject: AnnotatedProject = {
        id: generateProjectId(),
        name: projectName,
        imagePath: file.name,
        imageUrl: imageUrl,
        annotations: [],
        createdAt: new Date().toISOString(),
        lastModified: new Date().toISOString()
      };

      // Create project for annotation interface (compatible with existing interface)
      const annotationProject = {
        project_name: projectName,
        image_path: imageUrl,
        image_dimensions: { width: 0, height: 0 }, // Will be set when image loads
        annotations: [],
        created_by: 'user',
        id: newProject.id
      };

      // Set current project for annotation
      setCurrentProject(annotationProject);
      toast.success('Project created successfully');
    } catch (error) {
      toast.error('Failed to create project');
      console.error('Error:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {!currentProject ? (
        /* Main Gallery View */
        <div className="flex h-screen">
          {/* Left Sidebar - Gallery */}
          <div className={`${showGallery ? 'w-80' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden`}>
            <AnnotationGallery
              projects={annotatedProjects}
              onSelectProject={(project: AnnotatedProject) => {
                // Convert AnnotatedProject to format expected by InteractiveAnnotationInterface
                const annotationProject = {
                  id: project.id,
                  project_name: project.name,
                  image_path: project.imageUrl,
                  image_dimensions: { width: 0, height: 0 }, // Will be set when image loads
                  annotations: project.annotations,
                  created_by: 'user',
                  createdAt: project.createdAt
                };
                setCurrentProject(annotationProject);
              }}
              onToggleGallery={() => setShowGallery(!showGallery)}
              isVisible={showGallery}
            />
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    SLD Annotation Tool
                  </h1>
                  <p className="text-gray-600 mt-1">
                    Create interactive annotations for Single Line Diagrams
                  </p>
                </div>
                <button
                  onClick={() => setShowGallery(!showGallery)}
                  className="btn btn-outline"
                >
                  {showGallery ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  {showGallery ? 'Hide Gallery' : 'Show Gallery'}
                </button>
              </div>
            </div>

            {/* Project Creation Area */}
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="max-w-2xl w-full">
                <div className="card p-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">
                    Create New Annotation Project
                  </h2>

                  <ProjectCreationForm
                    onSubmit={handleCreateProject}
                    isLoading={isCreating}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Annotation Interface */
        <InteractiveAnnotationInterface
          project={currentProject}
          onBack={() => setCurrentProject(null)}
          onSave={(updatedProject) => {
            // Convert annotation project back to gallery project format
            const galleryProject: AnnotatedProject = {
              id: updatedProject.id,
              name: updatedProject.project_name,
              imagePath: updatedProject.image_path,
              imageUrl: updatedProject.image_path, // Same as imagePath for now
              annotations: updatedProject.annotations || [],
              createdAt: updatedProject.createdAt || new Date().toISOString(),
              lastModified: new Date().toISOString()
            };

            // Update or add the project in the gallery
            setAnnotatedProjects(prev => {
              const existingIndex = prev.findIndex(p => p.id === galleryProject.id);
              let updatedProjects: AnnotatedProject[];

              if (existingIndex >= 0) {
                // Update existing project
                updatedProjects = prev.map(p => p.id === galleryProject.id ? galleryProject : p);
              } else {
                // Add new project
                updatedProjects = [...prev, galleryProject];
              }

              // Save to localStorage
              saveProjectsToStorage(updatedProjects);
              return updatedProjects;
            });

            toast.success('Project saved to gallery');
          }}
        />
      )}
    </div>
  );
};

const AnnotationGallery: React.FC<{
  projects: AnnotatedProject[];
  onSelectProject: (project: any) => void;
  onToggleGallery: () => void;
  isVisible: boolean;
}> = ({ projects, onSelectProject, onToggleGallery, isVisible }) => {
  const handleDownloadImage = async (project: AnnotatedProject, e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      if (project.annotations.length === 0) {
        // If no annotations, download original image
        const link = document.createElement('a');
        link.href = project.imageUrl;
        link.download = `${project.name}_original.png`;
        link.click();
        toast.success('Original image downloaded');
        return;
      }

      // Create canvas to draw annotations on image
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;

        // Draw original image
        ctx!.drawImage(img, 0, 0);

        // Draw annotations
        project.annotations.forEach(annotation => {
          ctx!.strokeStyle = '#E21C15';
          ctx!.lineWidth = 1;
          ctx!.fillStyle = 'rgba(226, 28, 21, 0.1)';

          // Draw bounding box
          ctx!.fillRect(annotation.x, annotation.y, annotation.width, annotation.height);
          ctx!.strokeRect(annotation.x, annotation.y, annotation.width, annotation.height);

          // Draw label
          ctx!.fillStyle = '#E21C15';
          ctx!.font = '16px Inter, sans-serif';
          ctx!.fillText(annotation.componentName, annotation.x, annotation.y - 5);
        });

        // Download annotated image
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${project.name}_annotated.png`;
            link.click();
            URL.revokeObjectURL(url);
            toast.success('Annotated image downloaded');
          }
        }, 'image/png');
      };

      img.src = project.imageUrl;
    } catch (error) {
      console.error('Error downloading image:', error);
      toast.error('Failed to download image');
    }
  };

  const handleDownloadJSON = (project: AnnotatedProject, e: React.MouseEvent) => {
    e.stopPropagation();

    // Create comprehensive JSON data for annotations (excluding image path for privacy)
    const annotationData = {
      projectInfo: {
        id: project.id,
        name: project.name,
        createdAt: project.createdAt,
        lastModified: project.lastModified,
        totalAnnotations: project.annotations.length
      },
      annotations: project.annotations.map(ann => ({
        id: ann.id,
        componentName: ann.componentName,
        componentType: ann.componentType,
        coordinates: {
          x: Math.round(ann.x),
          y: Math.round(ann.y),
          width: Math.round(ann.width),
          height: Math.round(ann.height)
        },
        boundingBox: {
          left: Math.round(ann.x),
          top: Math.round(ann.y),
          right: Math.round(ann.x + ann.width),
          bottom: Math.round(ann.y + ann.height)
        }
      })),
      metadata: {
        exportedAt: new Date().toISOString(),
        exportFormat: 'SLD_Annotation_v1.0',
        coordinateSystem: 'pixel-based'
      }
    };

    const blob = new Blob([JSON.stringify(annotationData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${project.name}_annotations_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Annotations JSON downloaded');
  };

  if (!isVisible) return null;

  return (
    <div className="h-full flex flex-col">
      {/* Gallery Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Annotated Images
          </h2>
          <button
            onClick={onToggleGallery}
            className="btn btn-ghost p-2"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          {projects.length} project{projects.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Gallery Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {projects.length === 0 ? (
          <div className="text-center py-8">
            <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500">No annotated images yet</p>
            <p className="text-sm text-gray-400">Create your first annotation project</p>
          </div>
        ) : (
          projects.map((project) => (
            <div
              key={project.id}
              className="card p-3 hover:shadow-medium transition-all duration-200 cursor-pointer"
              onClick={() => onSelectProject(project)}
            >
              {/* Project Image Thumbnail */}
              <div className="aspect-video bg-gray-100 rounded-lg mb-3 overflow-hidden">
                <img
                  src={project.imageUrl}
                  alt={project.name}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Project Info */}
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 truncate">
                  {project.name}
                </h3>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{project.annotations.length} annotations</span>
                  <span>{new Date(project.lastModified).toLocaleDateString()}</span>
                </div>

                {/* Download Actions */}
                <div className="flex space-x-2 pt-2">
                  <button
                    onClick={(e) => handleDownloadImage(project, e)}
                    className="flex-1 btn btn-outline text-xs py-1"
                    title="Download annotated image"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Image
                  </button>
                  <button
                    onClick={(e) => handleDownloadJSON(project, e)}
                    className="flex-1 btn btn-outline text-xs py-1"
                    title="Download annotation JSON"
                  >
                    <FileDown className="w-3 h-3 mr-1" />
                    JSON
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const ProjectCreationForm: React.FC<{
  onSubmit: (file: File, projectName: string) => void;
  isLoading: boolean;
}> = ({ onSubmit, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !projectName.trim()) {
      toast.error('Please select a file and enter a project name');
      return;
    }
    onSubmit(selectedFile, projectName.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Project Name
        </label>
        <input
          type="text"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="input"
          placeholder="Enter project name"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          SLD Image
        </label>
        <div className="upload-area">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            className="hidden"
            id="file-upload"
            required
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">
              {selectedFile ? selectedFile.name : 'Click to select an image'}
            </p>
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="btn btn-primary w-full"
      >
        {isLoading ? (
          <>
            <div className="spinner w-4 h-4 mr-2" />
            Creating Project...
          </>
        ) : (
          <>
            <Plus className="w-4 h-4 mr-2" />
            Create Project
          </>
        )}
      </button>
    </form>
  );
};

const InteractiveAnnotationInterface: React.FC<{
  project: any;
  onBack: () => void;
  onSave: (project: any) => void;
}> = ({ project, onBack, onSave }) => {
  // Canvas and image refs
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // State management
  const [annotations, setAnnotations] = useState<AnnotationBox[]>(project.annotations || []);
  const [selectedTool, setSelectedTool] = useState<'select' | 'rectangle' | 'move'>('select');
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);

  // Canvas state
  const [canvasState, setCanvasState] = useState<CanvasState>({
    zoom: 1,
    panX: 0,
    panY: 0,
    isDragging: false,
    isDrawing: false,
    startPoint: null,
    selectedTool: 'select'
  });

  // Component management
  const [componentNames, setComponentNames] = useState<string[]>([
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
  ]);
  const [selectedComponentType, setSelectedComponentType] = useState(componentNames[0]);
  const [newComponentName, setNewComponentName] = useState('');

  // Image dimensions
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  // Load image and set up canvas
  useEffect(() => {
    const image = imageRef.current;
    if (image && project.image_path) {
      image.onload = () => {
        setImageDimensions({
          width: image.naturalWidth,
          height: image.naturalHeight
        });
        drawCanvas();
      };
      image.src = project.image_path;
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.image_path]);

  // Draw individual annotation box
  const drawAnnotationBox = useCallback((ctx: CanvasRenderingContext2D, annotation: AnnotationBox) => {
    const x = annotation.x * canvasState.zoom + canvasState.panX;
    const y = annotation.y * canvasState.zoom + canvasState.panY;
    const width = annotation.width * canvasState.zoom;
    const height = annotation.height * canvasState.zoom;

    // Box styling
    ctx.strokeStyle = annotation.isSelected ? '#00FF00' : '#E21C15';
    ctx.lineWidth = 1 / canvasState.zoom; // Keep line width consistent
    ctx.fillStyle = annotation.isSelected ? 'rgba(0, 255, 0, 0.1)' : 'rgba(226, 28, 21, 0.1)';

    // Draw box
    ctx.fillRect(x, y, width, height);
    ctx.strokeRect(x, y, width, height);

    // Draw label
    ctx.fillStyle = annotation.isSelected ? '#00FF00' : '#E21C15';
    ctx.font = `${12 / canvasState.zoom}px Inter, sans-serif`;
    ctx.fillText(annotation.componentName, x, y - 5);

    // Draw resize handles if selected
    if (annotation.isSelected) {
      const handleSize = 8 / canvasState.zoom;
      ctx.fillStyle = '#00FF00';

      // Corner handles
      ctx.fillRect(x - handleSize/2, y - handleSize/2, handleSize, handleSize);
      ctx.fillRect(x + width - handleSize/2, y - handleSize/2, handleSize, handleSize);
      ctx.fillRect(x - handleSize/2, y + height - handleSize/2, handleSize, handleSize);
      ctx.fillRect(x + width - handleSize/2, y + height - handleSize/2, handleSize, handleSize);
    }
  }, [canvasState]);

  // Canvas drawing function
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size based on container and zoom
    const container = containerRef.current;
    if (!container) return;

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const scaledWidth = imageDimensions.width * canvasState.zoom;
    const scaledHeight = imageDimensions.height * canvasState.zoom;

    canvas.width = Math.max(containerWidth, scaledWidth);
    canvas.height = Math.max(containerHeight, scaledHeight);

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw image
    ctx.drawImage(
      image,
      canvasState.panX,
      canvasState.panY,
      scaledWidth,
      scaledHeight
    );

    // Draw annotations
    annotations.forEach(annotation => {
      drawAnnotationBox(ctx, annotation);
    });
  }, [annotations, canvasState, imageDimensions, drawAnnotationBox]);

  // Mouse event handlers
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - canvasState.panX) / canvasState.zoom;
    const y = (e.clientY - rect.top - canvasState.panY) / canvasState.zoom;

    if (selectedTool === 'rectangle') {
      // Start drawing new annotation
      setCanvasState(prev => ({
        ...prev,
        isDrawing: true,
        startPoint: { x, y }
      }));
    } else if (selectedTool === 'select') {
      // Check if clicking on existing annotation
      const clickedAnnotation = annotations.find(ann =>
        x >= ann.x && x <= ann.x + ann.width &&
        y >= ann.y && y <= ann.y + ann.height
      );

      if (clickedAnnotation) {
        setSelectedAnnotation(clickedAnnotation.id);
        setAnnotations(prev => prev.map(ann => ({
          ...ann,
          isSelected: ann.id === clickedAnnotation.id
        })));
      } else {
        setSelectedAnnotation(null);
        setAnnotations(prev => prev.map(ann => ({ ...ann, isSelected: false })));
      }
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !canvasState.isDrawing || !canvasState.startPoint) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - canvasState.panX) / canvasState.zoom;
    const y = (e.clientY - rect.top - canvasState.panY) / canvasState.zoom;

    // Update canvas to show preview of new box
    drawCanvas();

    const ctx = canvas.getContext('2d');
    if (ctx) {
      const width = x - canvasState.startPoint.x;
      const height = y - canvasState.startPoint.y;

      ctx.strokeStyle = '#E21C15';
      ctx.lineWidth = 2;
      ctx.strokeRect(
        canvasState.startPoint.x * canvasState.zoom + canvasState.panX,
        canvasState.startPoint.y * canvasState.zoom + canvasState.panY,
        width * canvasState.zoom,
        height * canvasState.zoom
      );
    }
  };

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasState.isDrawing || !canvasState.startPoint) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - canvasState.panX) / canvasState.zoom;
    const y = (e.clientY - rect.top - canvasState.panY) / canvasState.zoom;

    const width = Math.abs(x - canvasState.startPoint.x);
    const height = Math.abs(y - canvasState.startPoint.y);

    // Only create annotation if box is large enough
    if (width > 10 && height > 10) {
      const newAnnotation: AnnotationBox = {
        id: `annotation_${Date.now()}`,
        x: Math.min(canvasState.startPoint.x, x),
        y: Math.min(canvasState.startPoint.y, y),
        width,
        height,
        componentName: selectedComponentType,
        componentType: selectedComponentType,
        isSelected: false
      };

      setAnnotations(prev => [...prev, newAnnotation]);
    }

    setCanvasState(prev => ({
      ...prev,
      isDrawing: false,
      startPoint: null
    }));
  };

  // Redraw canvas when state changes
  useEffect(() => {
    drawCanvas();
  }, [drawCanvas, annotations, canvasState]);

  // Utility functions
  const handleZoomIn = () => {
    setCanvasState(prev => ({ ...prev, zoom: Math.min(prev.zoom * 1.2, 5) }));
  };

  const handleZoomOut = () => {
    setCanvasState(prev => ({ ...prev, zoom: Math.max(prev.zoom / 1.2, 0.1) }));
  };

  const handleAddNewComponent = () => {
    if (newComponentName.trim() && !componentNames.includes(newComponentName.trim())) {
      setComponentNames(prev => [...prev, newComponentName.trim()]);
      setSelectedComponentType(newComponentName.trim());
      setNewComponentName('');
      toast.success('Component added successfully');
    }
  };

  const handleDeleteAnnotation = (annotationId: string) => {
    setAnnotations(prev => prev.filter(ann => ann.id !== annotationId));
    setSelectedAnnotation(null);
    toast.success('Annotation deleted');
  };

  const handleExportJSON = () => {
    const exportData = {
      projectName: project.project_name,
      imageDimensions,
      annotations: annotations.map(ann => ({
        id: ann.id,
        componentName: ann.componentName,
        componentType: ann.componentType,
        coordinates: {
          x: Math.round(ann.x),
          y: Math.round(ann.y),
          width: Math.round(ann.width),
          height: Math.round(ann.height)
        },
        boundingBox: {
          left: Math.round(ann.x),
          top: Math.round(ann.y),
          right: Math.round(ann.x + ann.width),
          bottom: Math.round(ann.y + ann.height)
        }
      })),
      metadata: {
        exportedAt: new Date().toISOString(),
        exportFormat: 'SLD_Annotation_v1.0',
        coordinateSystem: 'pixel-based'
      }
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${project.project_name}_annotations.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Annotations exported successfully');
  };

  const handleSaveProject = async () => {
    try {
      const updatedProject = {
        ...project,
        annotations,
        lastModified: new Date().toISOString()
      };
      onSave(updatedProject);
      toast.success('Project saved successfully');
    } catch (error) {
      toast.error('Failed to save project');
    }
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Control Panel */}
      <div className={`${isLeftPanelCollapsed ? 'w-0' : 'w-80'} transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden flex flex-col`}>
        {!isLeftPanelCollapsed && (
          <>
            {/* Panel Header */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Annotation Tools
                </h2>
                <button
                  onClick={() => setIsLeftPanelCollapsed(true)}
                  className="btn btn-ghost p-2"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Panel Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Add New Box Button */}
              <div>
                <button
                  onClick={() => setSelectedTool('rectangle')}
                  className={`w-full btn ${selectedTool === 'rectangle' ? 'btn-primary' : 'btn-outline'}`}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add New Box
                </button>
              </div>

              {/* Component Naming */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-900">Component Type</h3>

                {/* Dropdown for existing components */}
                <select
                  value={selectedComponentType}
                  onChange={(e) => setSelectedComponentType(e.target.value)}
                  className="input"
                >
                  {componentNames.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>

                {/* Add new component */}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newComponentName}
                    onChange={(e) => setNewComponentName(e.target.value)}
                    placeholder="New component name"
                    className="input flex-1"
                    onKeyDown={(e) => e.key === 'Enter' && handleAddNewComponent()}
                  />
                  <button
                    onClick={handleAddNewComponent}
                    className="btn btn-outline"
                    disabled={!newComponentName.trim()}
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Drawing Tools */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-900">Tools</h3>
                <div className="space-y-2">
                  {[
                    { id: 'select', name: 'Select', icon: MousePointer },
                    { id: 'rectangle', name: 'Rectangle', icon: Square },
                    { id: 'move', name: 'Move', icon: Move }
                  ].map((tool) => (
                    <button
                      key={tool.id}
                      onClick={() => setSelectedTool(tool.id as 'select' | 'rectangle' | 'move')}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center ${
                        selectedTool === tool.id
                          ? 'bg-primary-500 text-white'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <tool.icon className="w-4 h-4 mr-2" />
                      {tool.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Coordinate Display */}
              {selectedAnnotation && (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-gray-900">Selected Box</h3>
                  {(() => {
                    const annotation = annotations.find(ann => ann.id === selectedAnnotation);
                    if (!annotation) return null;

                    return (
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span>X:</span>
                          <span>{annotation.x.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Y:</span>
                          <span>{annotation.y.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Width:</span>
                          <span>{annotation.width.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Height:</span>
                          <span>{annotation.height.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Component:</span>
                          <span className="font-medium">{annotation.componentName}</span>
                        </div>
                        <button
                          onClick={() => handleDeleteAnnotation(annotation.id)}
                          className="w-full btn btn-outline text-red-600 hover:bg-red-50 mt-2"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </button>
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Export Functionality */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-900">Export</h3>
                <button
                  onClick={handleExportJSON}
                  className="w-full btn btn-primary"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export JSON
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Right Image Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Canvas Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {isLeftPanelCollapsed && (
                <button
                  onClick={() => setIsLeftPanelCollapsed(false)}
                  className="btn btn-outline"
                >
                  <ChevronRight className="w-4 h-4 mr-2" />
                  Show Tools
                </button>
              )}
              <h2 className="text-xl font-semibold text-gray-900">
                {project.project_name}
              </h2>
            </div>

            <div className="flex items-center space-x-2">
              {/* Zoom Controls */}
              <div className="flex items-center space-x-1 border border-gray-300 rounded-lg">
                <button
                  onClick={handleZoomOut}
                  className="p-2 hover:bg-gray-100 rounded-l-lg"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="px-2 text-sm text-gray-600 border-x border-gray-300">
                  {Math.round(canvasState.zoom * 100)}%
                </span>
                <button
                  onClick={handleZoomIn}
                  className="p-2 hover:bg-gray-100 rounded-r-lg"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
              </div>

              <button
                onClick={onBack}
                className="btn btn-outline"
              >
                Back to Gallery
              </button>
              <button
                onClick={handleSaveProject}
                className="btn btn-secondary"
              >
                <Save className="w-4 h-4 mr-2" />
                Save
              </button>
            </div>
          </div>
        </div>

        {/* Canvas Container */}
        <div className="flex-1 bg-gray-100 relative overflow-hidden" ref={containerRef}>
          {/* Hidden image for loading */}
          <img
            ref={imageRef}
            alt="SLD"
            className="hidden"
          />

          {/* Interactive Canvas */}
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 cursor-crosshair"
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            style={{
              cursor: selectedTool === 'rectangle' ? 'crosshair' :
                     selectedTool === 'move' ? 'move' : 'pointer'
            }}
          />

          {/* Canvas Overlay Info */}
          <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 rounded-lg p-3 text-sm">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span>Annotations: {annotations.length}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Settings className="w-3 h-3 text-gray-500" />
                <span>Tool: {selectedTool}</span>
              </div>
              {imageDimensions.width > 0 && (
                <div className="flex items-center space-x-2">
                  <ImageIcon className="w-3 h-3 text-gray-500" />
                  <span>{imageDimensions.width} × {imageDimensions.height}</span>
                </div>
              )}
            </div>
          </div>


        </div>
      </div>
    </div>
  );
};

export default AnnotationToolPage;

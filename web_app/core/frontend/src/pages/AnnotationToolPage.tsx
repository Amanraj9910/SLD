import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Download, Plus, Trash2, ZoomIn, ZoomOut,
  Move, Square, MousePointer, ChevronLeft, ChevronRight, FileDown
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  listProjects, createProject, getProject, deleteProject,
  saveAnnotations, getExportCocoUrl, getExportZipUrl, getImageUrl,
  ProjectSummary, ProjectDetail, COCOAnnotation, COCOCategory
} from '../services/my_annotation_api';

interface CanvasState {
  zoom: number;
  panX: number;
  panY: number;
  isDragging: boolean;
  isDrawing: boolean;
  startPoint: { x: number; y: number } | null;
  selectedTool: 'select' | 'rectangle' | 'move';
}

const AnnotationToolPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProject, setActiveProject] = useState<ProjectDetail | null>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // UI States
  const [isLoading, setIsLoading] = useState(false);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);

  // Canvas & Annotations
  const [annotations, setAnnotations] = useState<COCOAnnotation[]>([]);
  const [categories, setCategories] = useState<COCOCategory[]>([]);
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<number | null>(null);

  const [canvasState, setCanvasState] = useState<CanvasState>({
    zoom: 1, panX: 0, panY: 0, isDragging: false, isDrawing: false,
    startPoint: null, selectedTool: 'select'
  });

  const [newComponentName, setNewComponentName] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  // Load Projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (e) {
      toast.error('Failed to load projects');
    }
  };

  // ─── Project Selection ──────────────────────────────────────────────
  const handleSelectProject = async (name: string) => {
    try {
      setIsLoading(true);
      const data = await getProject(name);
      setActiveProject(data);
      setAnnotations(data.annotations || []);
      setCategories(data.categories || []);
      setCurrentImageIndex(0);
      if (data.categories?.length > 0) {
        setSelectedCategoryId(data.categories[0].id);
      }
    } catch (e) {
      toast.error('Failed to load project');
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Project Creation ───────────────────────────────────────────────
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadProjectName, setUploadProjectName] = useState('');

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadProjectName || uploadFiles.length === 0) {
      return toast.error('Name and files are required');
    }
    try {
      setIsLoading(true);
      await createProject(uploadFiles, uploadProjectName);
      toast.success('Project created');
      setUploadFiles([]);
      setUploadProjectName('');
      fetchProjects();
    } catch (err: any) {
      toast.error(err.message || 'Failed to create project');
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Auto-Save Debouncer ────────────────────────────────────────────
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const triggerAutoSave = useCallback((newAnnotations: COCOAnnotation[], newCategories: COCOCategory[]) => {
    if (!activeProject) return;
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);

    saveTimeoutRef.current = setTimeout(async () => {
      try {
        await saveAnnotations(activeProject.name, newAnnotations, newCategories);
        toast.success('Auto-saved', { id: 'autosave', duration: 1000 });
      } catch (e) {
        toast.error('Failed to auto-save');
      }
    }, 1500);
  }, [activeProject]);

  // ─── Image Loading & Canvas Render ──────────────────────────────────
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const img = imageRef.current;
    if (!canvas || !container || !img) return;

    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(canvasState.panX, canvasState.panY);
    ctx.scale(canvasState.zoom, canvasState.zoom);

    // Draw Image
    ctx.drawImage(img, 0, 0);

    // Draw Annotations for CURRENT image
    const currentImgId = activeProject!.images[currentImageIndex].id;
    const currentAnnotations = annotations.filter(a => a.image_id === currentImgId);

    currentAnnotations.forEach(ann => {
      const [x, y, w, h] = ann.bbox;
      const isSelected = ann.id === selectedAnnotationId;
      const category = categories.find(c => c.id === ann.category_id);

      ctx.strokeStyle = isSelected ? '#3b82f6' : '#22c55e';
      ctx.lineWidth = 2 / canvasState.zoom;
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = isSelected ? 'rgba(59, 130, 246, 0.2)' : 'rgba(34, 197, 94, 0.2)';
      ctx.fillRect(x, y, w, h);

      if (category) {
        ctx.fillStyle = ctx.strokeStyle;
        const fontSize = 12 / canvasState.zoom;
        ctx.font = `${fontSize}px sans-serif`;
        ctx.fillText(category.name, x, y - 4 / canvasState.zoom);
      }
    });

    ctx.restore();
  }, [canvasState, annotations, activeProject, currentImageIndex, categories, selectedAnnotationId]);

  useEffect(() => {
    if (!activeProject || !activeProject.images.length) return;

    const img = new Image();
    const currentImg = activeProject.images[currentImageIndex];
    img.src = getImageUrl(activeProject.name, currentImg.sequence_number);
    img.onload = () => {
      imageRef.current = img;
      renderCanvas();
    };
  }, [activeProject, currentImageIndex, canvasState.zoom, canvasState.panX, canvasState.panY, annotations, selectedAnnotationId, renderCanvas]);

  // ─── Mouse Interactions ─────────────────────────────────────────────
  const getMousePos = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - canvasState.panX) / canvasState.zoom,
      y: (e.clientY - rect.top - canvasState.panY) / canvasState.zoom
    };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    const pos = getMousePos(e);

    if (canvasState.selectedTool === 'move') {
      setCanvasState(s => ({ ...s, isDragging: true, startPoint: { x: e.clientX, y: e.clientY } }));
      return;
    }

    if (canvasState.selectedTool === 'rectangle') {
      if (!selectedCategoryId) {
        toast.error('Please create or select a category first');
        return;
      }
      setCanvasState(s => ({ ...s, isDrawing: true, startPoint: pos }));
      return;
    }

    if (canvasState.selectedTool === 'select') {
      const currentImgId = activeProject!.images[currentImageIndex].id;
      const clicked = annotations.find(ann => {
        if (ann.image_id !== currentImgId) return false;
        const [x, y, w, h] = ann.bbox;
        return pos.x >= x && pos.x <= x + w && pos.y >= y && pos.y <= y + h;
      });
      setSelectedAnnotationId(clicked ? clicked.id : null);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (canvasState.isDragging && canvasState.startPoint && canvasState.selectedTool === 'move') {
      setCanvasState(s => ({
        ...s,
        panX: s.panX + (e.clientX - s.startPoint!.x),
        panY: s.panY + (e.clientY - s.startPoint!.y),
        startPoint: { x: e.clientX, y: e.clientY }
      }));
      return;
    }

    if (canvasState.isDrawing && canvasState.startPoint) {
      renderCanvas(); // Redraw base
      const pos = getMousePos(e);
      const ctx = canvasRef.current?.getContext('2d');
      if (ctx) {
        ctx.save();
        ctx.translate(canvasState.panX, canvasState.panY);
        ctx.scale(canvasState.zoom, canvasState.zoom);
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2 / canvasState.zoom;
        const w = pos.x - canvasState.startPoint.x;
        const h = pos.y - canvasState.startPoint.y;
        ctx.strokeRect(canvasState.startPoint.x, canvasState.startPoint.y, w, h);
        ctx.restore();
      }
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (canvasState.isDragging) {
      setCanvasState(s => ({ ...s, isDragging: false, startPoint: null }));
    }

    if (canvasState.isDrawing && canvasState.startPoint) {
      const pos = getMousePos(e);
      const x = Math.min(canvasState.startPoint.x, pos.x);
      const y = Math.min(canvasState.startPoint.y, pos.y);
      const w = Math.abs(pos.x - canvasState.startPoint.x);
      const h = Math.abs(pos.y - canvasState.startPoint.y);

      if (w > 5 && h > 5) {
        const newAnn: COCOAnnotation = {
          id: Date.now(),
          image_id: activeProject!.images[currentImageIndex].id,
          category_id: selectedCategoryId!,
          bbox: [x, y, w, h],
          area: w * h,
          segmentation: [],
          iscrowd: 0
        };
        const newAnnotations = [...annotations, newAnn];
        setAnnotations(newAnnotations);
        triggerAutoSave(newAnnotations, categories);
      }
      setCanvasState(s => ({ ...s, isDrawing: false, startPoint: null }));
    }
  };

  // ─── Actions ────────────────────────────────────────────────────────
  const handleAddCategory = () => {
    if (!newComponentName.trim()) return;
    const exists = categories.find(c => c.name.toLowerCase() === newComponentName.trim().toLowerCase());
    if (exists) {
      setSelectedCategoryId(exists.id);
    } else {
      const newCat = { id: Date.now(), name: newComponentName.trim(), supercategory: 'none' };
      const newCats = [...categories, newCat];
      setCategories(newCats);
      setSelectedCategoryId(newCat.id);
      triggerAutoSave(annotations, newCats);
    }
    setNewComponentName('');
  };

  const handleDeleteAnnotation = () => {
    if (!selectedAnnotationId) return;
    const newAnns = annotations.filter(a => a.id !== selectedAnnotationId);
    setAnnotations(newAnns);
    setSelectedAnnotationId(null);
    triggerAutoSave(newAnns, categories);
  };

  const handleDeleteProject = async (e: React.MouseEvent, name: string) => {
    e.stopPropagation();
    if (!window.confirm(`Delete project ${name}?`)) return;
    try {
      await deleteProject(name);
      toast.success('Project deleted');
      fetchProjects();
    } catch (e) {
      toast.error('Failed to delete project');
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────
  if (!activeProject) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">Annotation Projects</h1>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Create New Card */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">Create Project</h2>
              <form onSubmit={handleCreateProject} className="space-y-4">
                <input
                  type="text"
                  placeholder="Project Name"
                  className="input w-full"
                  value={uploadProjectName}
                  onChange={e => setUploadProjectName(e.target.value)}
                />
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png"
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                  onChange={e => setUploadFiles(Array.from(e.target.files || []))}
                />
                <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
                  {isLoading ? 'Creating...' : 'Create Project'}
                </button>
              </form>
            </div>

            {/* List Projects */}
            {projects.map(p => (
              <div
                key={p.name}
                onClick={() => handleSelectProject(p.name)}
                className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:border-primary-500 transition-colors"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-gray-900">{p.display_name}</h3>
                  <button onClick={(e) => handleDeleteProject(e, p.name)} className="text-red-500 hover:text-red-700">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
                <div className="space-y-2 text-sm text-gray-600">
                  <p>Images: {p.image_count}</p>
                  <p>Annotations: {p.annotation_count}</p>
                  <p>Created: {new Date(p.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Active Project Workspace
  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Panel */}
      <div className={`${isLeftPanelCollapsed ? 'w-0' : 'w-80'} transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden flex flex-col`}>
        {!isLeftPanelCollapsed && (
          <>
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Tools</h2>
              <button onClick={() => setIsLeftPanelCollapsed(true)} className="btn btn-ghost p-2">
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Categories */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold">Component Class</h3>
                <select
                  value={selectedCategoryId || ''}
                  onChange={(e) => setSelectedCategoryId(Number(e.target.value))}
                  className="input w-full"
                >
                  <option value="" disabled>Select category...</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newComponentName}
                    onChange={e => setNewComponentName(e.target.value)}
                    placeholder="New class"
                    className="input flex-1"
                  />
                  <button onClick={handleAddCategory} className="btn btn-outline"><Plus className="w-4 h-4" /></button>
                </div>
              </div>

              {/* Tools */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold">Action</h3>
                {[
                  { id: 'select', name: 'Select', icon: MousePointer },
                  { id: 'rectangle', name: 'Draw Box', icon: Square },
                  { id: 'move', name: 'Pan Canvas', icon: Move }
                ].map(tool => (
                  <button
                    key={tool.id}
                    onClick={() => setCanvasState(s => ({ ...s, selectedTool: tool.id as any }))}
                    className={`w-full text-left px-3 py-2 rounded-lg flex items-center ${canvasState.selectedTool === tool.id ? 'bg-primary-500 text-white' : 'hover:bg-gray-100'}`}
                  >
                    <tool.icon className="w-4 h-4 mr-2" /> {tool.name}
                  </button>
                ))}
              </div>

              {/* Selected Annotation */}
              {selectedAnnotationId && (
                <div className="space-y-3">
                  <button onClick={handleDeleteAnnotation} className="w-full btn btn-outline text-red-600">
                    <Trash2 className="w-4 h-4 mr-2" /> Delete Selected Box
                  </button>
                </div>
              )}

              {/* Exports */}
              <div className="space-y-3 pt-6 border-t border-gray-200">
                <a href={getExportCocoUrl(activeProject.name)} className="btn btn-primary w-full flex items-center justify-center">
                  <FileDown className="w-4 h-4 mr-2" /> COCO JSON
                </a>
                <a href={getExportZipUrl(activeProject.name)} className="btn btn-outline w-full flex items-center justify-center">
                  <Download className="w-4 h-4 mr-2" /> Full ZIP
                </a>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {isLeftPanelCollapsed && (
              <button onClick={() => setIsLeftPanelCollapsed(false)} className="btn btn-outline p-2">
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
            <h2 className="text-xl font-semibold truncate">{activeProject.display_name}</h2>
          </div>

          <div className="flex items-center space-x-4">
            <button onClick={() => setCanvasState(s => ({ ...s, zoom: s.zoom - 0.1 }))} className="p-2 hover:bg-gray-100"><ZoomOut className="w-4 h-4" /></button>
            <span className="text-sm">{Math.round(canvasState.zoom * 100)}%</span>
            <button onClick={() => setCanvasState(s => ({ ...s, zoom: s.zoom + 0.1 }))} className="p-2 hover:bg-gray-100"><ZoomIn className="w-4 h-4" /></button>

            <button onClick={() => setActiveProject(null)} className="btn btn-outline">Exit</button>
          </div>
        </div>

        <div className="flex-1 bg-gray-100 relative overflow-hidden flex" ref={containerRef}>
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0"
            style={{ cursor: canvasState.selectedTool === 'rectangle' ? 'crosshair' : canvasState.selectedTool === 'move' ? 'move' : 'default' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        </div>

        {/* Thumbnail Strip / Navigation */}
        <div className="bg-white border-t border-gray-200 h-24 px-4 flex items-center overflow-x-auto space-x-2">
          {activeProject.images.map((img, idx) => (
            <div
              key={img.id}
              onClick={() => setCurrentImageIndex(idx)}
              className={`flex-shrink-0 h-20 w-20 relative cursor-pointer border-2 rounded ${idx === currentImageIndex ? 'border-primary-500' : 'border-transparent hover:border-gray-300'}`}
            >
              <img src={getImageUrl(activeProject.name, img.sequence_number)} alt={`Thumbnail ${idx}`} className="w-full h-full object-cover rounded-sm" />
              <div className="absolute top-0 right-0 bg-black/50 text-white text-xs px-1 rounded-bl">
                {annotations.filter(a => a.image_id === img.id).length}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnnotationToolPage;

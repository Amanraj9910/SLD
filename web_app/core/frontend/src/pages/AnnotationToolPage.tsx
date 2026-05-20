import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import {
  Download, Plus, Trash2, ZoomIn, ZoomOut,
  Move, Square, MousePointer, ChevronLeft, ChevronRight, FileDown,
  Upload, X, BarChart3, Lock
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  listProjects, createProject, getProject, deleteProject,
  saveAnnotations, getExportCocoUrl, getExportZipUrl, getImageUrl,
  addImages, deleteImage, getMergeZipUrl, getMergeCocoUrl,
  ProjectSummary, ProjectDetail, COCOAnnotation, COCOCategory
} from '../services/my_annotation_api';

type ResizeHandle = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | null;

interface CanvasState {
  zoom: number;
  panX: number;
  panY: number;
  isDragging: boolean;
  isDrawing: boolean;
  isResizing: boolean;
  isDraggingBox: boolean;
  resizeHandle: ResizeHandle;
  dragOffset: { x: number; y: number } | null;
  startPoint: { x: number; y: number } | null;
  selectedTool: 'select' | 'rectangle' | 'move';
}

const AnnotationToolPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProject, setActiveProject] = useState<ProjectDetail | null>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [selectedProjectsForMerge, setSelectedProjectsForMerge] = useState<Set<string>>(new Set());

  const isCurrentProjectLocked = useMemo(() => {
    if (!activeProject) return false;
    const proj = projects.find(p => p.name === activeProject.name);
    return proj?.locked ?? false;
  }, [activeProject, projects]);

  // UI States
  const [isLoading, setIsLoading] = useState(false);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);

  // Canvas & Annotations
  const [annotations, setAnnotations] = useState<COCOAnnotation[]>([]);
  const [categories, setCategories] = useState<COCOCategory[]>([]);
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<number | string | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | string | null>(null);

  const [canvasState, setCanvasState] = useState<CanvasState>({
    zoom: 1, panX: 0, panY: 0, isDragging: false, isDrawing: false,
    isResizing: false, isDraggingBox: false, resizeHandle: null, dragOffset: null,
    startPoint: null, selectedTool: 'select'
  });

  const addImageInputRef = useRef<HTMLInputElement>(null);

  const [newComponentName, setNewComponentName] = useState('');


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

  // ─── Helper: detect resize handle ────────────────────────────────────
  const HANDLE_SIZE = 8;

  const getResizeHandle = useCallback((pos: {x: number; y: number}, bbox: [number, number, number, number]): ResizeHandle => {
    const [bx, by, bw, bh] = bbox;
    const hs = HANDLE_SIZE / canvasState.zoom;
    const handles: { handle: ResizeHandle; cx: number; cy: number }[] = [
      { handle: 'nw', cx: bx, cy: by },
      { handle: 'n',  cx: bx + bw / 2, cy: by },
      { handle: 'ne', cx: bx + bw, cy: by },
      { handle: 'e',  cx: bx + bw, cy: by + bh / 2 },
      { handle: 'se', cx: bx + bw, cy: by + bh },
      { handle: 's',  cx: bx + bw / 2, cy: by + bh },
      { handle: 'sw', cx: bx, cy: by + bh },
      { handle: 'w',  cx: bx, cy: by + bh / 2 },
    ];
    for (const h of handles) {
      if (Math.abs(pos.x - h.cx) <= hs && Math.abs(pos.y - h.cy) <= hs) return h.handle;
    }
    return null;
  }, [canvasState.zoom]);

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
        ctx.font = `bold ${fontSize}px sans-serif`;
        ctx.fillText(category.name, x, y - 4 / canvasState.zoom);
      }

      // Draw resize handles on selected box
      if (isSelected) {
        const hs = HANDLE_SIZE / canvasState.zoom;
        const handlePositions = [
          [x, y], [x + w / 2, y], [x + w, y],
          [x + w, y + h / 2],
          [x + w, y + h], [x + w / 2, y + h], [x, y + h],
          [x, y + h / 2],
        ];
        ctx.fillStyle = '#3b82f6';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1 / canvasState.zoom;
        handlePositions.forEach(([hx, hy]) => {
          ctx.fillRect(hx - hs / 2, hy - hs / 2, hs, hs);
          ctx.strokeRect(hx - hs / 2, hy - hs / 2, hs, hs);
        });
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

      // Check if clicking a resize handle on the selected annotation
      if (selectedAnnotationId) {
        const selAnn = annotations.find(a => a.id === selectedAnnotationId);
        if (selAnn) {
          const handle = getResizeHandle(pos, selAnn.bbox);
          if (handle) {
            setCanvasState(s => ({ ...s, isResizing: true, resizeHandle: handle, startPoint: pos }));
            return;
          }
        }
      }

      // Check if clicking inside any annotation (drag or select)
      const clicked = annotations.find(ann => {
        if (ann.image_id !== currentImgId) return false;
        const [x, y, w, h] = ann.bbox;
        return pos.x >= x && pos.x <= x + w && pos.y >= y && pos.y <= y + h;
      });

      if (clicked) {
        setSelectedAnnotationId(clicked.id);
        const [bx, by] = clicked.bbox;
        setCanvasState(s => ({
          ...s, isDraggingBox: true, startPoint: pos,
          dragOffset: { x: pos.x - bx, y: pos.y - by }
        }));
      } else {
        setSelectedAnnotationId(null);
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    // Pan canvas
    if (canvasState.isDragging && canvasState.startPoint && canvasState.selectedTool === 'move') {
      setCanvasState(s => ({
        ...s,
        panX: s.panX + (e.clientX - s.startPoint!.x),
        panY: s.panY + (e.clientY - s.startPoint!.y),
        startPoint: { x: e.clientX, y: e.clientY }
      }));
      return;
    }

    // Resize selected annotation
    if (canvasState.isResizing && canvasState.startPoint && selectedAnnotationId && canvasState.resizeHandle) {
      const pos = getMousePos(e);
      setAnnotations(prev => prev.map(ann => {
        if (ann.id !== selectedAnnotationId) return ann;
        let [bx, by, bw, bh] = ann.bbox;
        const handle = canvasState.resizeHandle!;
        if (handle.includes('w')) { const newX = pos.x; bw = bw + (bx - newX); bx = newX; }
        if (handle.includes('e')) { bw = pos.x - bx; }
        if (handle.includes('n')) { const newY = pos.y; bh = bh + (by - newY); by = newY; }
        if (handle.includes('s')) { bh = pos.y - by; }
        // Enforce minimum size
        if (bw < 5) bw = 5;
        if (bh < 5) bh = 5;
        return { ...ann, bbox: [bx, by, bw, bh] as [number, number, number, number], area: bw * bh };
      }));
      return;
    }

    // Drag selected annotation
    if (canvasState.isDraggingBox && canvasState.dragOffset && selectedAnnotationId) {
      const pos = getMousePos(e);
      setAnnotations(prev => prev.map(ann => {
        if (ann.id !== selectedAnnotationId) return ann;
        const [, , bw, bh] = ann.bbox;
        const newX = pos.x - canvasState.dragOffset!.x;
        const newY = pos.y - canvasState.dragOffset!.y;
        return { ...ann, bbox: [newX, newY, bw, bh] as [number, number, number, number] };
      }));
      return;
    }

    // Draw preview rectangle
    if (canvasState.isDrawing && canvasState.startPoint) {
      renderCanvas();
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

    // Finish resize
    if (canvasState.isResizing) {
      setCanvasState(s => ({ ...s, isResizing: false, resizeHandle: null, startPoint: null }));
      triggerAutoSave(annotations, categories);
    }

    // Finish drag box
    if (canvasState.isDraggingBox) {
      setCanvasState(s => ({ ...s, isDraggingBox: false, dragOffset: null, startPoint: null }));
      triggerAutoSave(annotations, categories);
    }

    if (canvasState.isDrawing && canvasState.startPoint) {
      const pos = getMousePos(e);
      const x = Math.min(canvasState.startPoint.x, pos.x);
      const y = Math.min(canvasState.startPoint.y, pos.y);
      const w = Math.abs(pos.x - canvasState.startPoint.x);
      const h = Math.abs(pos.y - canvasState.startPoint.y);

      if (w > 5 && h > 5) {
        const newAnn: COCOAnnotation = {
          id: crypto.randomUUID(),
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
      const newCat = { id: crypto.randomUUID(), name: newComponentName.trim(), supercategory: 'none' };
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

  // Feature 3: Change class of selected annotation
  const handleChangeCategoryOfAnnotation = (newCatId: number | string) => {
    if (!selectedAnnotationId) return;
    const newAnns = annotations.map(a =>
      a.id === selectedAnnotationId ? { ...a, category_id: newCatId } : a
    );
    setAnnotations(newAnns);
    triggerAutoSave(newAnns, categories);
  };

  // Feature 1: Add more images to existing project
  const handleAddImages = async (files: FileList | null) => {
    if (!files || files.length === 0 || !activeProject) return;
    try {
      setIsLoading(true);
      await addImages(activeProject.name, Array.from(files));
      const refreshed = await getProject(activeProject.name, true);
      setActiveProject(refreshed);
      setAnnotations(refreshed.annotations || []);
      setCategories(refreshed.categories || []);
      toast.success(`Added ${files.length} image(s)`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to add images');
    } finally {
      setIsLoading(false);
      if (addImageInputRef.current) addImageInputRef.current.value = '';
    }
  };

  // Feature 4: Delete an image from the project
  const handleDeleteImage = async (e: React.MouseEvent, seqNum: number, imgId: number) => {
    e.stopPropagation();
    if (!activeProject) return;
    if (!window.confirm('Delete this image and its annotations?')) return;
    try {
      setIsLoading(true);
      await deleteImage(activeProject.name, seqNum);
      // Remove annotations for that image locally
      const newAnns = annotations.filter(a => a.image_id !== imgId);
      setAnnotations(newAnns);
      // Refresh project
      const refreshed = await getProject(activeProject.name, true);
      setActiveProject(refreshed);
      setAnnotations(refreshed.annotations || []);
      setCategories(refreshed.categories || []);
      // Adjust current index if needed
      if (currentImageIndex >= refreshed.images.length) {
        setCurrentImageIndex(Math.max(0, refreshed.images.length - 1));
      }
      toast.success('Image deleted');
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete image');
    } finally {
      setIsLoading(false);
    }
  };

  // Feature 5: Per-class annotation statistics
  const annotationStats = useMemo(() => {
    const stats: { catId: string | number; name: string; count: number; currentImageCount: number }[] = [];
    const currentImgId = activeProject?.images[currentImageIndex]?.id;
    categories.forEach(cat => {
      const count = annotations.filter(a => a.category_id === cat.id).length;
      const currentImageCount = currentImgId
        ? annotations.filter(a => a.category_id === cat.id && a.image_id === currentImgId).length
        : 0;
      stats.push({ catId: cat.id, name: cat.name, count, currentImageCount });
    });
    return {
      perClass: stats,
      totalAll: annotations.length,
      totalCurrentImage: currentImgId ? annotations.filter(a => a.image_id === currentImgId).length : 0,
    };
  }, [annotations, categories, activeProject, currentImageIndex]);

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

  const toggleProjectSelection = (e: React.MouseEvent | React.ChangeEvent, name: string) => {
    e.stopPropagation();
    const newSet = new Set(selectedProjectsForMerge);
    if (newSet.has(name)) newSet.delete(name);
    else newSet.add(name);
    setSelectedProjectsForMerge(newSet);
  };

  const handleMergeProjects = async () => {
    if (selectedProjectsForMerge.size < 2) {
      toast.error('Select at least 2 projects to merge');
      return;
    }
    const projectsToMerge = Array.from(selectedProjectsForMerge);
    try {
      setIsLoading(true);
      const zipUrl = getMergeZipUrl(projectsToMerge);
      const res = await fetch(zipUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_names: projectsToMerge }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let errMsg = 'Failed to merge projects';
        if (errData.detail && errData.detail.errors) {
            errMsg = `Validation errors:\n${errData.detail.errors.join('\n')}`;
        } else if (errData.detail && typeof errData.detail === 'string') {
            errMsg = errData.detail;
        }
        throw new Error(errMsg);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `merged_${projectsToMerge.join('_')}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Projects merged successfully!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to merge projects');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMergeCocoDownload = async () => {
    if (selectedProjectsForMerge.size < 2) {
      toast.error('Select at least 2 projects to merge');
      return;
    }
    const projectsToMerge = Array.from(selectedProjectsForMerge);
    try {
      setIsLoading(true);
      const cocoUrl = getMergeCocoUrl(projectsToMerge);
      const res = await fetch(cocoUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_names: projectsToMerge }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let errMsg = 'Failed to merge projects';
        if (errData.detail && errData.detail.errors) {
            errMsg = `Validation errors:\n${errData.detail.errors.join('\n')}`;
        } else if (errData.detail && typeof errData.detail === 'string') {
            errMsg = errData.detail;
        }
        throw new Error(errMsg);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `merged_${projectsToMerge.join('_')}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Merged COCO JSON downloaded!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to merge');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCoco = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      setIsLoading(true);
      const res = await fetch(getExportCocoUrl(activeProject.name));
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let errMsg = 'Failed to export COCO';
        if (errData.detail && errData.detail.errors) {
            errMsg = `Validation errors:\n${errData.detail.errors.join('\n')}`;
        } else if (errData.detail && typeof errData.detail === 'string') {
            errMsg = errData.detail;
        }
        throw new Error(errMsg);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${activeProject.name}_annotations.coco.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      toast.error(err.message || 'Failed to export');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportZip = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      setIsLoading(true);
      const res = await fetch(getExportZipUrl(activeProject.name));
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let errMsg = 'Failed to export ZIP';
        if (errData.detail && errData.detail.errors) {
            errMsg = `Validation errors:\n${errData.detail.errors.join('\n')}`;
        } else if (errData.detail && typeof errData.detail === 'string') {
            errMsg = errData.detail;
        }
        throw new Error(errMsg);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${activeProject.name}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      toast.error(err.message || 'Failed to export');
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────
  if (!activeProject) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">Annotation Projects</h1>
            {selectedProjectsForMerge.size >= 2 && (
              <div className="flex items-center space-x-3">
                <button 
                  onClick={handleMergeProjects} 
                  className="btn btn-primary flex items-center"
                  disabled={isLoading}
                >
                  <Download className="w-4 h-4 mr-2" />
                  {isLoading ? 'Merging...' : `Merge ZIP (${selectedProjectsForMerge.size})`}
                </button>
                <button 
                  onClick={handleMergeCocoDownload} 
                  className="btn btn-outline flex items-center"
                  disabled={isLoading}
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Merge JSON
                </button>
              </div>
            )}
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
                className={`bg-white rounded-xl shadow-sm border p-6 cursor-pointer transition-colors ${
                  selectedProjectsForMerge.has(p.name)
                    ? 'border-primary-500 ring-2 ring-primary-200'
                    : 'border-gray-200 hover:border-primary-500'
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center space-x-3">
                    <input 
                      type="checkbox" 
                      className="w-5 h-5 text-primary-600 rounded"
                      checked={selectedProjectsForMerge.has(p.name)}
                      onChange={(e) => toggleProjectSelection(e, p.name)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <h3 className="text-xl font-semibold text-gray-900">{p.display_name}</h3>
                    {p.locked && (
                      <span className="inline-flex items-center space-x-1 bg-amber-100 text-amber-700 text-xs font-medium px-2 py-0.5 rounded-full">
                        <Lock className="w-3 h-3" />
                        <span>Locked</span>
                      </span>
                    )}
                  </div>
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
                  <h3 className="text-sm font-semibold">Selected Box</h3>
                  {/* Feature 3: Change class */}
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Change Class</label>
                    <select
                      value={annotations.find(a => a.id === selectedAnnotationId)?.category_id || ''}
                      onChange={(e) => handleChangeCategoryOfAnnotation(Number(e.target.value))}
                      className="input w-full"
                    >
                      {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <button onClick={handleDeleteAnnotation} className="w-full btn btn-outline text-red-600">
                    <Trash2 className="w-4 h-4 mr-2" /> Delete Selected Box
                  </button>
                </div>
              )}

              {/* Feature 5: Annotation Statistics */}
              <div className="space-y-3 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold flex items-center">
                  <BarChart3 className="w-4 h-4 mr-1" /> Statistics
                </h3>
                {annotationStats.perClass.length > 0 ? (
                  <div className="space-y-1">
                    {annotationStats.perClass.map(stat => (
                      <div key={stat.catId} className="flex items-center justify-between text-sm px-2 py-1 rounded bg-gray-50">
                        <span className="text-gray-700 truncate mr-2">{stat.name}</span>
                        <div className="flex items-center space-x-2 flex-shrink-0">
                          <span className="bg-blue-100 text-blue-700 text-xs px-1.5 py-0.5 rounded" title="This image">{stat.currentImageCount}</span>
                          <span className="bg-green-100 text-green-700 text-xs px-1.5 py-0.5 rounded" title="All images">{stat.count}</span>
                        </div>
                      </div>
                    ))}
                    <div className="flex items-center justify-between text-sm font-semibold px-2 py-1.5 rounded bg-gray-100 mt-2">
                      <span>Total</span>
                      <div className="flex items-center space-x-2">
                        <span className="bg-blue-200 text-blue-800 text-xs px-1.5 py-0.5 rounded" title="This image">{annotationStats.totalCurrentImage}</span>
                        <span className="bg-green-200 text-green-800 text-xs px-1.5 py-0.5 rounded" title="All images">{annotationStats.totalAll}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 text-center">
                      <span className="text-blue-500">■</span> this image &nbsp; <span className="text-green-500">■</span> all images
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-gray-400">No annotations yet</p>
                )}
              </div>

              {/* Exports */}
              <div className="space-y-3 pt-4 border-t border-gray-200">
                <button onClick={handleExportCoco} className="btn btn-primary w-full flex items-center justify-center">
                  <FileDown className="w-4 h-4 mr-2" /> COCO JSON
                </button>
                <button onClick={handleExportZip} className="btn btn-outline w-full flex items-center justify-center">
                  <Download className="w-4 h-4 mr-2" /> Full ZIP
                </button>
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
            style={{ cursor: canvasState.isResizing ? (
              canvasState.resizeHandle === 'nw' || canvasState.resizeHandle === 'se' ? 'nwse-resize' :
              canvasState.resizeHandle === 'ne' || canvasState.resizeHandle === 'sw' ? 'nesw-resize' :
              canvasState.resizeHandle === 'n' || canvasState.resizeHandle === 's' ? 'ns-resize' :
              'ew-resize'
            ) : canvasState.isDraggingBox ? 'grabbing' :
              canvasState.selectedTool === 'rectangle' ? 'crosshair' :
              canvasState.selectedTool === 'move' ? 'move' : 'default' }}
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
              className={`flex-shrink-0 h-20 w-20 relative cursor-pointer border-2 rounded group ${idx === currentImageIndex ? 'border-primary-500' : 'border-transparent hover:border-gray-300'}`}
            >
              <img src={getImageUrl(activeProject.name, img.sequence_number)} alt={`Thumbnail ${idx}`} className="w-full h-full object-cover rounded-sm" />
              <div className="absolute top-0 right-0 bg-black/50 text-white text-xs px-1 rounded-bl">
                {annotations.filter(a => a.image_id === img.id).length}
              </div>
              {/* Feature 4: Delete image button */}
              {!isCurrentProjectLocked && (
                <button
                  onClick={(e) => handleDeleteImage(e, img.sequence_number, img.id)}
                  className="absolute top-0 left-0 bg-red-500 text-white p-0.5 rounded-br opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Delete image"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}

          {/* Feature 1: Add more images */}
          <input
            ref={addImageInputRef}
            type="file"
            multiple
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={(e) => handleAddImages(e.target.files)}
          />
          {!isCurrentProjectLocked && (
            <button
              onClick={() => addImageInputRef.current?.click()}
              className="flex-shrink-0 h-20 w-20 border-2 border-dashed border-gray-300 rounded flex flex-col items-center justify-center text-gray-400 hover:border-primary-400 hover:text-primary-500 transition-colors"
              disabled={isLoading}
              title="Add more images"
            >
              <Upload className="w-5 h-5 mb-1" />
              <span className="text-xs">Add</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnnotationToolPage;

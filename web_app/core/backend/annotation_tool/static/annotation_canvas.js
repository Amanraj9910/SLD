/**
 * Canvas-based annotation tool for SLD component labeling
 * Provides interactive bounding box drawing and editing capabilities
 */

class AnnotationCanvas {
    constructor(canvasId, imageId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.image = document.getElementById(imageId);
        
        // Configuration
        this.options = {
            strokeColor: '#E21C15',
            strokeWidth: 2,
            fillColor: 'rgba(226, 28, 21, 0.1)',
            selectedColor: '#00FF00',
            handleSize: 8,
            minBoxSize: 10,
            ...options
        };
        
        // State
        this.annotations = [];
        this.selectedAnnotation = null;
        this.isDrawing = false;
        this.isDragging = false;
        this.isResizing = false;
        this.startPoint = null;
        this.currentBox = null;
        this.dragHandle = null;
        
        // Scale factors for coordinate conversion
        this.scaleX = 1;
        this.scaleY = 1;
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.bindEvents();
        this.updateScale();
    }
    
    setupCanvas() {
        // Set canvas size to match image
        this.canvas.width = this.image.naturalWidth || this.image.width;
        this.canvas.height = this.image.naturalHeight || this.image.height;
        
        // Style canvas
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.cursor = 'crosshair';
        this.canvas.style.zIndex = '10';
    }
    
    updateScale() {
        // Calculate scale factors for coordinate conversion
        const rect = this.canvas.getBoundingClientRect();
        this.scaleX = this.canvas.width / rect.width;
        this.scaleY = this.canvas.height / rect.height;
    }
    
    bindEvents() {
        // Mouse events
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.canvas.addEventListener('click', this.onClick.bind(this));
        
        // Keyboard events
        document.addEventListener('keydown', this.onKeyDown.bind(this));
        
        // Window resize
        window.addEventListener('resize', this.updateScale.bind(this));
    }
    
    getMousePos(event) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (event.clientX - rect.left) * this.scaleX,
            y: (event.clientY - rect.top) * this.scaleY
        };
    }
    
    onMouseDown(event) {
        const pos = this.getMousePos(event);
        
        // Check if clicking on a handle of selected annotation
        if (this.selectedAnnotation) {
            const handle = this.getResizeHandle(pos, this.selectedAnnotation);
            if (handle) {
                this.isResizing = true;
                this.dragHandle = handle;
                return;
            }
            
            // Check if clicking inside selected annotation for dragging
            if (this.isPointInBox(pos, this.selectedAnnotation)) {
                this.isDragging = true;
                this.startPoint = pos;
                return;
            }
        }
        
        // Check if clicking on any annotation
        const clickedAnnotation = this.getAnnotationAt(pos);
        if (clickedAnnotation) {
            this.selectAnnotation(clickedAnnotation);
            return;
        }
        
        // Start drawing new annotation
        this.isDrawing = true;
        this.startPoint = pos;
        this.currentBox = {
            x: pos.x,
            y: pos.y,
            width: 0,
            height: 0,
            classId: 0,
            className: 'CIRCUIT_BREAKER'
        };
        
        this.selectedAnnotation = null;
        this.redraw();
    }
    
    onMouseMove(event) {
        const pos = this.getMousePos(event);
        
        if (this.isDrawing && this.currentBox) {
            // Update current box dimensions
            this.currentBox.width = pos.x - this.startPoint.x;
            this.currentBox.height = pos.y - this.startPoint.y;
            this.redraw();
            this.drawCurrentBox();
        } else if (this.isDragging && this.selectedAnnotation) {
            // Drag selected annotation
            const dx = pos.x - this.startPoint.x;
            const dy = pos.y - this.startPoint.y;
            
            this.selectedAnnotation.x += dx;
            this.selectedAnnotation.y += dy;
            
            this.startPoint = pos;
            this.redraw();
        } else if (this.isResizing && this.selectedAnnotation && this.dragHandle) {
            // Resize selected annotation
            this.resizeAnnotation(pos);
            this.redraw();
        } else {
            // Update cursor based on hover state
            this.updateCursor(pos);
        }
    }
    
    onMouseUp(event) {
        if (this.isDrawing && this.currentBox) {
            // Finalize new annotation
            const box = this.normalizeBox(this.currentBox);
            
            if (box.width >= this.options.minBoxSize && box.height >= this.options.minBoxSize) {
                this.annotations.push(box);
                this.selectedAnnotation = box;
                this.onAnnotationAdded(box);
            }
            
            this.currentBox = null;
        }
        
        this.isDrawing = false;
        this.isDragging = false;
        this.isResizing = false;
        this.dragHandle = null;
        this.redraw();
    }
    
    onClick(event) {
        // Handle single clicks for selection
        if (!this.isDrawing && !this.isDragging && !this.isResizing) {
            const pos = this.getMousePos(event);
            const annotation = this.getAnnotationAt(pos);
            
            if (annotation) {
                this.selectAnnotation(annotation);
            } else {
                this.selectedAnnotation = null;
                this.redraw();
            }
        }
    }
    
    onKeyDown(event) {
        if (event.key === 'Delete' && this.selectedAnnotation) {
            this.deleteAnnotation(this.selectedAnnotation);
        } else if (event.key === 'Escape') {
            this.selectedAnnotation = null;
            this.redraw();
        }
    }
    
    normalizeBox(box) {
        // Ensure box has positive width and height
        const normalized = { ...box };
        
        if (normalized.width < 0) {
            normalized.x += normalized.width;
            normalized.width = -normalized.width;
        }
        
        if (normalized.height < 0) {
            normalized.y += normalized.height;
            normalized.height = -normalized.height;
        }
        
        return normalized;
    }
    
    isPointInBox(point, box) {
        return point.x >= box.x && 
               point.x <= box.x + box.width &&
               point.y >= box.y && 
               point.y <= box.y + box.height;
    }
    
    getAnnotationAt(point) {
        // Return topmost annotation at point (reverse order for z-index)
        for (let i = this.annotations.length - 1; i >= 0; i--) {
            if (this.isPointInBox(point, this.annotations[i])) {
                return this.annotations[i];
            }
        }
        return null;
    }
    
    getResizeHandle(point, annotation) {
        const handles = this.getResizeHandles(annotation);
        const handleSize = this.options.handleSize;
        
        for (const [name, handle] of Object.entries(handles)) {
            if (Math.abs(point.x - handle.x) <= handleSize/2 && 
                Math.abs(point.y - handle.y) <= handleSize/2) {
                return name;
            }
        }
        return null;
    }
    
    getResizeHandles(annotation) {
        const { x, y, width, height } = annotation;
        return {
            'nw': { x: x, y: y },
            'ne': { x: x + width, y: y },
            'sw': { x: x, y: y + height },
            'se': { x: x + width, y: y + height },
            'n': { x: x + width/2, y: y },
            's': { x: x + width/2, y: y + height },
            'w': { x: x, y: y + height/2 },
            'e': { x: x + width, y: y + height/2 }
        };
    }
    
    resizeAnnotation(pos) {
        const annotation = this.selectedAnnotation;
        const handle = this.dragHandle;
        
        switch (handle) {
            case 'nw':
                annotation.width += annotation.x - pos.x;
                annotation.height += annotation.y - pos.y;
                annotation.x = pos.x;
                annotation.y = pos.y;
                break;
            case 'ne':
                annotation.width = pos.x - annotation.x;
                annotation.height += annotation.y - pos.y;
                annotation.y = pos.y;
                break;
            case 'sw':
                annotation.width += annotation.x - pos.x;
                annotation.height = pos.y - annotation.y;
                annotation.x = pos.x;
                break;
            case 'se':
                annotation.width = pos.x - annotation.x;
                annotation.height = pos.y - annotation.y;
                break;
            case 'n':
                annotation.height += annotation.y - pos.y;
                annotation.y = pos.y;
                break;
            case 's':
                annotation.height = pos.y - annotation.y;
                break;
            case 'w':
                annotation.width += annotation.x - pos.x;
                annotation.x = pos.x;
                break;
            case 'e':
                annotation.width = pos.x - annotation.x;
                break;
        }
        
        // Ensure minimum size
        if (annotation.width < this.options.minBoxSize) {
            annotation.width = this.options.minBoxSize;
        }
        if (annotation.height < this.options.minBoxSize) {
            annotation.height = this.options.minBoxSize;
        }
    }
    
    updateCursor(pos) {
        let cursor = 'crosshair';
        
        if (this.selectedAnnotation) {
            const handle = this.getResizeHandle(pos, this.selectedAnnotation);
            if (handle) {
                const cursors = {
                    'nw': 'nw-resize', 'ne': 'ne-resize',
                    'sw': 'sw-resize', 'se': 'se-resize',
                    'n': 'n-resize', 's': 's-resize',
                    'w': 'w-resize', 'e': 'e-resize'
                };
                cursor = cursors[handle];
            } else if (this.isPointInBox(pos, this.selectedAnnotation)) {
                cursor = 'move';
            }
        }
        
        this.canvas.style.cursor = cursor;
    }
    
    selectAnnotation(annotation) {
        this.selectedAnnotation = annotation;
        this.redraw();
        this.onAnnotationSelected(annotation);
    }
    
    deleteAnnotation(annotation) {
        const index = this.annotations.indexOf(annotation);
        if (index > -1) {
            this.annotations.splice(index, 1);
            this.selectedAnnotation = null;
            this.redraw();
            this.onAnnotationDeleted(annotation, index);
        }
    }
    
    redraw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw all annotations
        this.annotations.forEach(annotation => {
            this.drawAnnotation(annotation, annotation === this.selectedAnnotation);
        });
    }
    
    drawAnnotation(annotation, isSelected = false) {
        const { x, y, width, height, className } = annotation;
        
        // Draw bounding box
        this.ctx.strokeStyle = isSelected ? this.options.selectedColor : this.options.strokeColor;
        this.ctx.lineWidth = this.options.strokeWidth;
        this.ctx.fillStyle = this.options.fillColor;
        
        this.ctx.fillRect(x, y, width, height);
        this.ctx.strokeRect(x, y, width, height);
        
        // Draw class label
        this.ctx.fillStyle = this.options.strokeColor;
        this.ctx.font = '14px Arial';
        this.ctx.fillText(className, x, y - 5);
        
        // Draw resize handles if selected
        if (isSelected) {
            this.drawResizeHandles(annotation);
        }
    }
    
    drawResizeHandles(annotation) {
        const handles = this.getResizeHandles(annotation);
        const size = this.options.handleSize;
        
        this.ctx.fillStyle = this.options.selectedColor;
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 1;
        
        Object.values(handles).forEach(handle => {
            this.ctx.fillRect(handle.x - size/2, handle.y - size/2, size, size);
            this.ctx.strokeRect(handle.x - size/2, handle.y - size/2, size, size);
        });
    }
    
    drawCurrentBox() {
        if (!this.currentBox) return;
        
        const box = this.normalizeBox(this.currentBox);
        
        this.ctx.strokeStyle = this.options.strokeColor;
        this.ctx.lineWidth = this.options.strokeWidth;
        this.ctx.setLineDash([5, 5]);
        
        this.ctx.strokeRect(box.x, box.y, box.width, box.height);
        
        this.ctx.setLineDash([]);
    }
    
    // Public API methods
    addAnnotation(annotation) {
        this.annotations.push(annotation);
        this.redraw();
    }
    
    removeAnnotation(index) {
        if (index >= 0 && index < this.annotations.length) {
            const removed = this.annotations.splice(index, 1)[0];
            if (this.selectedAnnotation === removed) {
                this.selectedAnnotation = null;
            }
            this.redraw();
            return removed;
        }
        return null;
    }
    
    updateAnnotation(index, updates) {
        if (index >= 0 && index < this.annotations.length) {
            Object.assign(this.annotations[index], updates);
            this.redraw();
        }
    }
    
    getAnnotations() {
        return this.annotations.slice(); // Return copy
    }
    
    clearAnnotations() {
        this.annotations = [];
        this.selectedAnnotation = null;
        this.redraw();
    }
    
    exportYOLO() {
        const imageWidth = this.canvas.width;
        const imageHeight = this.canvas.height;
        
        return this.annotations.map(ann => {
            const x_center = (ann.x + ann.width / 2) / imageWidth;
            const y_center = (ann.y + ann.height / 2) / imageHeight;
            const width = ann.width / imageWidth;
            const height = ann.height / imageHeight;
            
            return {
                class_id: ann.classId,
                class_name: ann.className,
                bbox: [x_center, y_center, width, height]
            };
        });
    }
    
    importYOLO(yoloAnnotations, classNames) {
        const imageWidth = this.canvas.width;
        const imageHeight = this.canvas.height;
        
        this.annotations = yoloAnnotations.map(ann => {
            const [x_center, y_center, width, height] = ann.bbox;
            
            return {
                x: (x_center - width / 2) * imageWidth,
                y: (y_center - height / 2) * imageHeight,
                width: width * imageWidth,
                height: height * imageHeight,
                classId: ann.class_id,
                className: classNames[ann.class_id] || `Class_${ann.class_id}`
            };
        });
        
        this.redraw();
    }
    
    // Event callbacks (override these)
    onAnnotationAdded(annotation) {
        console.log('Annotation added:', annotation);
    }
    
    onAnnotationSelected(annotation) {
        console.log('Annotation selected:', annotation);
    }
    
    onAnnotationDeleted(annotation, index) {
        console.log('Annotation deleted:', annotation, 'at index:', index);
    }
}

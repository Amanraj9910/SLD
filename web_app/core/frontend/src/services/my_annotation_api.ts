/**
 * Annotation API v2 — Multi-Image Project Service
 * Communicates with the server-side project manager.
 * Includes in-memory caching with automatic invalidation on mutations.
 */

// Use relative URL in dev (proxied), absolute in production
const API_BASE = '/api/v1/annotations/v2';

export interface ProjectSummary {
  name: string;
  display_name: string;
  image_count: number;
  annotation_count: number;
  created_at: string;
  last_modified: string;
  created_by: string;
  locked: boolean;
}

export interface ProjectImage {
  id: number;
  sequence_number: number;
  original_name: string;
  file_name: string;
  width: number;
  height: number;
  date_added: string;
}

export interface COCOAnnotation {
  id: string | number;
  image_id: number;
  category_id: string | number;
  bbox: [number, number, number, number]; // [x, y, width, height]
  area: number;
  segmentation: any[];
  iscrowd: number;
  annotator?: string;
  model_id?: string | null;
}

export interface COCOCategory {
  id: string | number;
  name: string;
  supercategory: string;
}

export interface ProjectDetail {
  name: string;
  display_name: string;
  created_by: string;
  created_at: string;
  last_modified: string;
  next_sequence: number;
  images: ProjectImage[];
  annotations: COCOAnnotation[];
  categories: COCOCategory[];
}

// ─── Cache Layer ──────────────────────────────────────────────

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

let _projectListCache: CacheEntry<ProjectSummary[]> | null = null;
const _projectDetailCache = new Map<string, CacheEntry<ProjectDetail>>();
const _annotationsCache = new Map<string, CacheEntry<{ annotations: COCOAnnotation[]; categories: COCOCategory[] }>>();

function isCacheValid<T>(entry: CacheEntry<T> | null | undefined): entry is CacheEntry<T> {
  if (!entry) return false;
  return Date.now() - entry.timestamp < CACHE_TTL_MS;
}

/** Invalidate project list cache (called after create/delete project) */
function invalidateProjectList(): void {
  _projectListCache = null;
}

/** Invalidate a specific project's cache (called after save/addImages/deleteImage) */
function invalidateProject(projectName: string): void {
  _projectDetailCache.delete(projectName);
  _annotationsCache.delete(projectName);
  // Also invalidate list since counts may have changed
  _projectListCache = null;
}

/** Invalidate everything */
export function invalidateAllCaches(): void {
  _projectListCache = null;
  _projectDetailCache.clear();
  _annotationsCache.clear();
}

// ─── Project Endpoints ────────────────────────────────────────

export async function listProjects(forceRefresh = false): Promise<ProjectSummary[]> {
  if (!forceRefresh && isCacheValid(_projectListCache)) {
    return _projectListCache.data;
  }

  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error(`Failed to list projects: ${res.statusText}`);
  const data = await res.json();
  const projects: ProjectSummary[] = data.projects;

  _projectListCache = { data: projects, timestamp: Date.now() };
  return projects;
}

export async function createProject(
  files: File[],
  projectName: string,
  createdBy: string = 'user'
): Promise<ProjectDetail> {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));
  formData.append('project_name', projectName);
  formData.append('created_by', createdBy);

  const res = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Failed to create project');
  }
  const result = await res.json();

  // Invalidate list — new project added, lock status of other projects may change
  invalidateProjectList();

  return result;
}

export async function getProject(projectName: string, forceRefresh = false): Promise<ProjectDetail> {
  if (!forceRefresh && isCacheValid(_projectDetailCache.get(projectName))) {
    return _projectDetailCache.get(projectName)!.data;
  }

  const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectName)}`);
  if (!res.ok) throw new Error(`Failed to load project: ${res.statusText}`);
  const project: ProjectDetail = await res.json();

  _projectDetailCache.set(projectName, { data: project, timestamp: Date.now() });
  return project;
}

export async function deleteProject(projectName: string): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectName)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.statusText}`);

  // Invalidate this project and the list
  invalidateProject(projectName);
}

// ─── Image Endpoints ──────────────────────────────────────────

export async function addImages(
  projectName: string,
  files: File[]
): Promise<ProjectImage[]> {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));

  const res = await fetch(
    `${API_BASE}/projects/${encodeURIComponent(projectName)}/images`,
    { method: 'POST', body: formData }
  );

  if (!res.ok) throw new Error(`Failed to add images: ${res.statusText}`);
  const data = await res.json();

  // Invalidate project cache — images changed
  invalidateProject(projectName);

  return data.images;
}

export function getImageUrl(projectName: string, sequence: number): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectName)}/images/${sequence}`;
}

export async function deleteImage(
  projectName: string,
  sequence: number
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/projects/${encodeURIComponent(projectName)}/images/${sequence}`,
    { method: 'DELETE' }
  );
  if (!res.ok) throw new Error(`Failed to delete image: ${res.statusText}`);

  // Invalidate project cache — images and annotations changed
  invalidateProject(projectName);
}

// ─── Annotation Endpoints ─────────────────────────────────────

export async function saveAnnotations(
  projectName: string,
  annotations: COCOAnnotation[],
  categories: COCOCategory[]
): Promise<{ success: boolean; annotation_count: number }> {
  const res = await fetch(
    `${API_BASE}/projects/${encodeURIComponent(projectName)}/annotations`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ annotations, categories }),
    }
  );

  if (!res.ok) throw new Error(`Failed to save annotations: ${res.statusText}`);
  const result = await res.json();

  // Invalidate project cache — annotation data changed
  invalidateProject(projectName);

  return result;
}

export async function getAnnotations(
  projectName: string,
  forceRefresh = false
): Promise<{ annotations: COCOAnnotation[]; categories: COCOCategory[] }> {
  if (!forceRefresh && isCacheValid(_annotationsCache.get(projectName))) {
    return _annotationsCache.get(projectName)!.data;
  }

  const res = await fetch(
    `${API_BASE}/projects/${encodeURIComponent(projectName)}/annotations`
  );
  if (!res.ok) throw new Error(`Failed to get annotations: ${res.statusText}`);
  const data = await res.json();

  _annotationsCache.set(projectName, { data, timestamp: Date.now() });
  return data;
}

// ─── Export Endpoints ─────────────────────────────────────────

export function getExportCocoUrl(projectName: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectName)}/export/coco`;
}

export function getExportZipUrl(projectName: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectName)}/export/zip`;
}

// ─── Merge Endpoints ──────────────────────────────────────────

export async function previewMerge(projectNames: string[]): Promise<any> {
  const res = await fetch(`${API_BASE}/projects/merge/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_names: projectNames }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail?.message || errData.detail || 'Failed to preview merge');
  }
  return res.json();
}

export function getMergeCocoUrl(projectNames: string[]): string {
  return `${API_BASE}/projects/merge/coco`;
}

export function getMergeZipUrl(projectNames: string[]): string {
  return `${API_BASE}/projects/merge/zip`;
}

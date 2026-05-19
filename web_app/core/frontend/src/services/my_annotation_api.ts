/**
 * Annotation API v2 — Multi-Image Project Service
 * Communicates with the server-side project manager.
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
  id: number;
  image_id: number;
  category_id: number;
  bbox: [number, number, number, number]; // [x, y, width, height]
  area: number;
  segmentation: any[];
  iscrowd: number;
  annotator?: string;
  model_id?: string | null;
}

export interface COCOCategory {
  id: number;
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

// ─── Project Endpoints ────────────────────────────────────────

export async function listProjects(): Promise<ProjectSummary[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error(`Failed to list projects: ${res.statusText}`);
  const data = await res.json();
  return data.projects;
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
  return res.json();
}

export async function getProject(projectName: string): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectName)}`);
  if (!res.ok) throw new Error(`Failed to load project: ${res.statusText}`);
  return res.json();
}

export async function deleteProject(projectName: string): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectName)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.statusText}`);
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
  return res.json();
}

export async function getAnnotations(
  projectName: string
): Promise<{ annotations: COCOAnnotation[]; categories: COCOCategory[] }> {
  const res = await fetch(
    `${API_BASE}/projects/${encodeURIComponent(projectName)}/annotations`
  );
  if (!res.ok) throw new Error(`Failed to get annotations: ${res.statusText}`);
  return res.json();
}

// ─── Export Endpoints ─────────────────────────────────────────

export function getExportCocoUrl(projectName: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectName)}/export/coco`;
}

export function getExportZipUrl(projectName: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectName)}/export/zip`;
}

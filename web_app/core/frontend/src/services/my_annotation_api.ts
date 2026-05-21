/**
 * Annotation API v2 — Multi-Image Project Service
 * Communicates with the server-side project manager.
 * Includes in-memory caching with automatic invalidation on mutations.
 */

import { saveAs } from 'file-saver';
import { invalidateProjectCache } from './annotationImageCache';

/** Relative in dev (proxy) / same-origin prod; override with REACT_APP_ANNOTATION_API_BASE */
function resolveAnnotationApiBase(): string {
  const envBase = process.env.REACT_APP_ANNOTATION_API_BASE?.replace(/\/$/, '');
  if (envBase) {
    return envBase.endsWith('/v2') ? envBase : `${envBase}/v2`;
  }
  return '/api/v1/annotations/v2';
}

const API_BASE = resolveAnnotationApiBase();

/** Absolute URL for native browser downloads (ZIP). */
export function resolveExportUrl(path: string): string {
  if (path.startsWith('http')) return path;
  const base = API_BASE.startsWith('http') ? API_BASE : `${window.location.origin}${API_BASE}`;
  return `${base}${path}`;
}

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
  _projectListCache = null;
  void invalidateProjectCache(projectName);
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
  return resolveExportUrl(`/projects/${encodeURIComponent(projectName)}/images/${sequence}`);
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
  return resolveExportUrl(`/projects/${encodeURIComponent(projectName)}/export/coco`);
}

export function getExportZipUrl(projectName: string): string {
  return resolveExportUrl(`/projects/${encodeURIComponent(projectName)}/export/zip`);
}

export function getImageThumbUrl(projectName: string, sequence: number, maxEdge = 200): string {
  return resolveExportUrl(
    `/projects/${encodeURIComponent(projectName)}/images/${sequence}/thumb?max_edge=${maxEdge}`
  );
}

export type ExportKind = 'coco' | 'zip';

export interface ExportDownloadResult {
  ok: boolean;
  blob?: Blob;
  filename?: string;
  errorMessage?: string;
  status?: number;
  statusText?: string;
  url?: string;
  detail?: unknown;
}

export interface ExportProgressUpdate {
  phase: 'waiting' | 'downloading' | 'saving';
  percent: number | null;
  loadedBytes: number;
  totalBytes: number | null;
  message: string;
}

export type ExportProgressHandler = (update: ExportProgressUpdate) => void;

/** XHR fetch with download progress (works once server starts sending bytes). */
export function fetchBlobWithProgress(
  url: string,
  onProgress?: ExportProgressHandler
): Promise<{ blob: Blob; status: number; statusText: string }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    xhr.responseType = 'blob';

    const waitingStart = Date.now();
    const waitingTimer = window.setInterval(() => {
      const secs = Math.floor((Date.now() - waitingStart) / 1000);
      onProgress?.({
        phase: 'waiting',
        percent: null,
        loadedBytes: 0,
        totalBytes: null,
        message: `Preparing on server… (${secs}s)`,
      });
    }, 1000);

    onProgress?.({
      phase: 'waiting',
      percent: null,
      loadedBytes: 0,
      totalBytes: null,
      message: 'Preparing export on server…',
    });

    xhr.onprogress = event => {
      window.clearInterval(waitingTimer);
      if (event.lengthComputable && event.total > 0) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress?.({
          phase: 'downloading',
          percent,
          loadedBytes: event.loaded,
          totalBytes: event.total,
          message: `Downloading… ${percent}%`,
        });
      } else {
        onProgress?.({
          phase: 'downloading',
          percent: null,
          loadedBytes: event.loaded,
          totalBytes: null,
          message: `Downloading… ${(event.loaded / (1024 * 1024)).toFixed(1)} MB`,
        });
      }
    };

    xhr.onload = () => {
      window.clearInterval(waitingTimer);
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.({
          phase: 'saving',
          percent: 100,
          loadedBytes: xhr.response?.size ?? 0,
          totalBytes: xhr.response?.size ?? null,
          message: 'Saving file…',
        });
        resolve({ blob: xhr.response, status: xhr.status, statusText: xhr.statusText });
      } else {
        reject({ status: xhr.status, statusText: xhr.statusText, response: xhr.response });
      }
    };

    xhr.onerror = () => {
      window.clearInterval(waitingTimer);
      reject(new Error('Network error during download'));
    };

    xhr.onabort = () => {
      window.clearInterval(waitingTimer);
      reject(new Error('Download cancelled'));
    };

    xhr.send();
  });
}

function parseExportErrorDetail(detail: unknown): string {
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  if (typeof detail === 'object' && detail !== null) {
    const d = detail as { message?: string; errors?: string[] };
    if (d.errors?.length) {
      return `${d.message || 'Export failed'}: ${d.errors.join('; ')}`;
    }
    if (d.message) return d.message;
    try {
      return JSON.stringify(detail);
    } catch {
      return String(detail);
    }
  }
  return String(detail);
}

/** Fetch export with structured console + return value for UI error handling. */
export async function downloadProjectExport(
  projectName: string,
  kind: ExportKind
): Promise<ExportDownloadResult> {
  const url = kind === 'coco' ? getExportCocoUrl(projectName) : getExportZipUrl(projectName);
  const logPrefix = `[annotation-export:${kind}]`;

  console.info(`${logPrefix} start`, { projectName, url });

  try {
    const res = await fetch(url);

    if (!res.ok) {
      const rawText = await res.text().catch(() => '');
      let detail: unknown = rawText;
      try {
        const parsed = rawText ? JSON.parse(rawText) : {};
        detail = (parsed as { detail?: unknown }).detail ?? parsed;
      } catch {
        /* keep rawText */
      }

      const errorMessage = parseExportErrorDetail(detail) || res.statusText || 'Export failed';
      console.error(`${logPrefix} failed`, {
        projectName,
        url,
        status: res.status,
        statusText: res.statusText,
        detail,
        rawText: rawText.slice(0, 500),
      });

      return {
        ok: false,
        errorMessage,
        status: res.status,
        statusText: res.statusText,
        url,
        detail,
      };
    }

    const blob = await res.blob();
    const filename =
      kind === 'coco'
        ? `${projectName}_annotations.coco.json`
        : `${projectName}.zip`;

    console.info(`${logPrefix} success`, {
      projectName,
      url,
      blobSize: blob.size,
      blobType: blob.type,
      filename,
    });

    if (blob.size === 0) {
      console.warn(`${logPrefix} empty blob returned`, { projectName, url });
    }

    return { ok: true, blob, filename, url };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`${logPrefix} network error`, { projectName, url, error: err });
    return {
      ok: false,
      errorMessage: message || 'Network error during export',
      url,
    };
  }
}

/** Save blob via file-saver (avoids revokeObjectURL race). */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  saveAs(blob, filename);
}


async function downloadBlobExport(
  projectName: string,
  kind: ExportKind,
  onProgress?: ExportProgressHandler
): Promise<ExportDownloadResult> {
  const url = kind === 'coco' ? getExportCocoUrl(projectName) : getExportZipUrl(projectName);
  const filename =
    kind === 'coco' ? `${projectName}_annotations.coco.json` : `${projectName}.zip`;
  const logPrefix = `[annotation-export:${kind}]`;

  console.info(`${logPrefix} start`, { projectName, url });

  try {
    const { blob, status, statusText } = await fetchBlobWithProgress(url, onProgress);

    if (blob.size === 0) {
      return { ok: false, errorMessage: 'Export returned an empty file', url, status, statusText };
    }
    if (blob.type.includes('text/html')) {
      return {
        ok: false,
        errorMessage: 'Server returned HTML — check API URL / proxy',
        url,
        status,
        statusText,
      };
    }

    triggerBlobDownload(blob, filename);
    console.info(`${logPrefix} success`, { blobSize: blob.size, filename });
    return { ok: true, blob, filename, url, status, statusText };
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'status' in err) {
      const xhrErr = err as { status: number; statusText: string; response?: Blob };
      let detail = '';
      if (xhrErr.response) {
        try {
          detail = await xhrErr.response.text();
        } catch {
          /* ignore */
        }
      }
      let parsed: unknown = detail;
      try {
        parsed = detail ? JSON.parse(detail) : {};
        parsed = (parsed as { detail?: unknown }).detail ?? parsed;
      } catch {
        /* keep */
      }
      const errorMessage = parseExportErrorDetail(parsed) || xhrErr.statusText || 'Export failed';
      console.error(`${logPrefix} failed`, { url, status: xhrErr.status, detail });
      return {
        ok: false,
        errorMessage,
        status: xhrErr.status,
        statusText: xhrErr.statusText,
        url,
        detail: parsed,
      };
    }
    const message = err instanceof Error ? err.message : String(err);
    console.error(`${logPrefix} network error`, { url, error: err });
    return { ok: false, errorMessage: message || 'Network error during export', url };
  }
}

/** Download COCO JSON via fetch + file-saver. */
export async function downloadProjectCoco(
  projectName: string,
  onProgress?: ExportProgressHandler
): Promise<ExportDownloadResult> {
  return downloadBlobExport(projectName, 'coco', onProgress);
}

/** Download ZIP via fetch + file-saver with progress. */
export async function downloadProjectZip(
  projectName: string,
  onProgress?: ExportProgressHandler
): Promise<ExportDownloadResult> {
  return downloadBlobExport(projectName, 'zip', onProgress);
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

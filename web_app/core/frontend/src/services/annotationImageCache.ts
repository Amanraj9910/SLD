/**
 * L1 memory + L2 IndexedDB cache for annotation images and project JSON.
 */

import { openDB, type IDBPDatabase } from 'idb';
import type { ProjectDetail } from './my_annotation_api';

const DB_NAME = 'annotation-cache';
const DB_VERSION = 1;
const IMAGE_TTL_MS = 24 * 60 * 60 * 1000;
const PROJECT_TTL_MS = 5 * 60 * 1000;
const MEMORY_MAX = 60;

type ImageVariant = 'thumb' | 'full';

interface MemoryEntry {
  blobUrl: string;
  fetchedAt: number;
}

interface ImageRecord {
  key: string;
  blob: Blob;
  contentType: string;
  fetchedAt: number;
  size: number;
}

interface ProjectRecord {
  projectName: string;
  detail: ProjectDetail;
  fetchedAt: number;
}

let dbPromise: Promise<IDBPDatabase> | null = null;

function cacheKey(projectName: string, sequence: number, variant: ImageVariant): string {
  return `v1:${projectName}:${sequence}:${variant}`;
}

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        db.createObjectStore('images', { keyPath: 'key' });
        db.createObjectStore('projects', { keyPath: 'projectName' });
      },
    });
  }
  return dbPromise;
}

const memory = new Map<string, MemoryEntry>();
const memoryOrder: string[] = [];

function touchMemory(key: string, entry: MemoryEntry): void {
  const idx = memoryOrder.indexOf(key);
  if (idx >= 0) memoryOrder.splice(idx, 1);
  memoryOrder.push(key);
  memory.set(key, entry);

  while (memoryOrder.length > MEMORY_MAX) {
    const evictKey = memoryOrder.shift();
    if (!evictKey) break;
    const evicted = memory.get(evictKey);
    if (evicted) URL.revokeObjectURL(evicted.blobUrl);
    memory.delete(evictKey);
  }
}

export async function getCachedImageBlobUrl(
  projectName: string,
  sequence: number,
  variant: ImageVariant,
  fetcher: () => Promise<Blob | null>
): Promise<string | null> {
  const key = cacheKey(projectName, sequence, variant);
  const now = Date.now();

  const mem = memory.get(key);
  if (mem && now - mem.fetchedAt < IMAGE_TTL_MS) {
    touchMemory(key, mem);
    return mem.blobUrl;
  }

  try {
    const db = await getDb();
    const row = (await db.get('images', key)) as ImageRecord | undefined;
    if (row && now - row.fetchedAt < IMAGE_TTL_MS) {
      const blobUrl = URL.createObjectURL(row.blob);
      touchMemory(key, { blobUrl, fetchedAt: row.fetchedAt });
      return blobUrl;
    }
  } catch (e) {
    console.warn('[annotationImageCache] IDB read failed', e);
  }

  const blob = await fetcher();
  if (!blob) return null;

  const blobUrl = URL.createObjectURL(blob);
  touchMemory(key, { blobUrl, fetchedAt: now });

  try {
    const db = await getDb();
    await db.put('images', {
      key,
      blob,
      contentType: blob.type,
      fetchedAt: now,
      size: blob.size,
    } satisfies ImageRecord);
  } catch (e) {
    console.warn('[annotationImageCache] IDB write failed', e);
  }

  return blobUrl;
}

export async function prefetchImageBlob(
  projectName: string,
  sequence: number,
  variant: ImageVariant,
  fetcher: () => Promise<Blob | null>
): Promise<void> {
  const key = cacheKey(projectName, sequence, variant);
  if (memory.has(key)) return;
  try {
    const db = await getDb();
    const row = (await db.get('images', key)) as ImageRecord | undefined;
    if (row && Date.now() - row.fetchedAt < IMAGE_TTL_MS) return;
  } catch {
    /* ignore */
  }
  await getCachedImageBlobUrl(projectName, sequence, variant, fetcher);
}

export async function getCachedProject(
  projectName: string,
  fetcher: () => Promise<ProjectDetail>
): Promise<ProjectDetail> {
  const now = Date.now();
  try {
    const db = await getDb();
    const row = (await db.get('projects', projectName)) as ProjectRecord | undefined;
    if (row && now - row.fetchedAt < PROJECT_TTL_MS) {
      return row.detail;
    }
  } catch (e) {
    console.warn('[annotationImageCache] project IDB read failed', e);
  }

  const detail = await fetcher();
  try {
    const db = await getDb();
    await db.put('projects', {
      projectName,
      detail,
      fetchedAt: now,
    } satisfies ProjectRecord);
  } catch (e) {
    console.warn('[annotationImageCache] project IDB write failed', e);
  }
  return detail;
}

export async function invalidateProjectCache(projectName: string): Promise<void> {
  const memoryKeys = Array.from(memory.keys());
  for (const key of memoryKeys) {
    if (key.includes(`:${projectName}:`)) {
      const entry = memory.get(key);
      if (entry) URL.revokeObjectURL(entry.blobUrl);
      memory.delete(key);
    }
  }
  try {
    const db = await getDb();
    await db.delete('projects', projectName);
    const all = await db.getAllKeys('images');
    for (const k of all) {
      if (String(k).includes(`:${projectName}:`)) {
        await db.delete('images', k);
      }
    }
  } catch (e) {
    console.warn('[annotationImageCache] invalidate failed', e);
  }
}

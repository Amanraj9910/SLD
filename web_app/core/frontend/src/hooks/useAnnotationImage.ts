import { useEffect, useState } from 'react';
import {
  getCachedImageBlobUrl,
  prefetchImageBlob,
} from '../services/annotationImageCache';
import { getImageThumbUrl, getImageUrl } from '../services/my_annotation_api';

async function fetchImageBlob(url: string): Promise<Blob | null> {
  const res = await fetch(url);
  if (!res.ok) return null;
  return res.blob();
}

export function useAnnotationImage(
  projectName: string | undefined,
  sequence: number | undefined,
  variant: 'thumb' | 'full' = 'full',
  enabled = true
): { src: string | null; loading: boolean; error: boolean } {
  const [src, setSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!enabled || !projectName || sequence === undefined) {
      setSrc(null);
      setLoading(false);
      setError(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(false);

    const url =
      variant === 'thumb'
        ? getImageThumbUrl(projectName, sequence)
        : getImageUrl(projectName, sequence);

    getCachedImageBlobUrl(projectName, sequence, variant, () => fetchImageBlob(url))
      .then(blobUrl => {
        if (cancelled) return;
        if (blobUrl) {
          setSrc(blobUrl);
          setError(false);
        } else {
          setSrc(null);
          setError(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSrc(null);
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [projectName, sequence, variant, enabled]);

  return { src, loading, error };
}

export function prefetchAnnotationImages(
  projectName: string,
  sequences: number[],
  variant: 'thumb' | 'full' = 'thumb'
): void {
  const run = () => {
    for (const seq of sequences) {
      const url =
        variant === 'thumb'
          ? getImageThumbUrl(projectName, seq)
          : getImageUrl(projectName, seq);
      prefetchImageBlob(projectName, seq, variant, () => fetchImageBlob(url)).catch(() => {});
    }
  };

  if (typeof requestIdleCallback !== 'undefined') {
    requestIdleCallback(run, { timeout: 2000 });
  } else {
    setTimeout(run, 0);
  }
}

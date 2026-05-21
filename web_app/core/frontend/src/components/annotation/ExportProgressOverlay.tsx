import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ExportProgressState {
  active: boolean;
  label: string;
  message: string;
  phase: 'waiting' | 'downloading' | 'saving';
  percent: number | null;
  loadedBytes: number;
  totalBytes: number | null;
}

interface ExportProgressOverlayProps {
  progress: ExportProgressState;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

const ExportProgressOverlay: React.FC<ExportProgressOverlayProps> = ({ progress }) => {
  if (!progress.active) return null;

  const showBar = progress.percent !== null;
  const subtext =
    progress.message ||
    (progress.phase === 'waiting'
      ? 'Server is building the archive…'
      : progress.totalBytes
        ? `${formatBytes(progress.loadedBytes)} / ${formatBytes(progress.totalBytes)}`
        : progress.loadedBytes > 0
          ? formatBytes(progress.loadedBytes)
          : '');

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Export in progress"
    >
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
        <div className="flex items-center gap-3 mb-4">
          <Loader2 className="w-6 h-6 text-primary-600 animate-spin flex-shrink-0" />
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{progress.label}</p>
            <p className="text-sm text-gray-500">{subtext}</p>
          </div>
        </div>

        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          {showBar ? (
            <div
              className="h-full bg-primary-600 transition-all duration-200 ease-out"
              style={{ width: `${Math.min(100, Math.max(0, progress.percent ?? 0))}%` }}
            />
          ) : (
            <div className="h-full w-1/3 bg-primary-600 rounded-full animate-pulse export-indeterminate" />
          )}
        </div>

        {showBar && progress.percent !== null && (
          <p className="text-xs text-gray-500 mt-2 text-right">{progress.percent}%</p>
        )}
        {!showBar && (
          <p className="text-xs text-gray-500 mt-2 text-center">Please wait…</p>
        )}
      </div>
    </div>
  );
};

export default ExportProgressOverlay;

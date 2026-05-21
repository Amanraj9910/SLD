import React, { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { useAnnotationImage } from '../../hooks/useAnnotationImage';

interface LazyThumbnailProps {
  projectName: string;
  sequence: number;
  isActive: boolean;
  annotationCount: number;
  onClick: () => void;
  onDelete?: (e: React.MouseEvent) => void;
  canDelete: boolean;
}

const LazyThumbnail: React.FC<LazyThumbnailProps> = ({
  projectName,
  sequence,
  isActive,
  annotationCount,
  onClick,
  onDelete,
  canDelete,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setVisible(true);
      },
      { rootMargin: '120px' }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const { src, loading, error } = useAnnotationImage(
    projectName,
    sequence,
    'thumb',
    visible
  );

  return (
    <div
      ref={ref}
      onClick={onClick}
      className={`flex-shrink-0 h-20 w-20 relative cursor-pointer border-2 rounded group ${
        isActive ? 'border-primary-500' : 'border-transparent hover:border-gray-300'
      }`}
    >
      {src ? (
        <img
          src={src}
          alt={`Thumbnail ${sequence}`}
          className="w-full h-full object-cover rounded-sm"
        />
      ) : (
        <div className="w-full h-full bg-gray-200 rounded-sm flex items-center justify-center text-xs text-gray-500">
          {error ? '!' : loading ? '…' : ''}
        </div>
      )}
      <div className="absolute top-0 right-0 bg-black/50 text-white text-xs px-1 rounded-bl">
        {annotationCount}
      </div>
      {canDelete && onDelete && (
        <button
          type="button"
          onClick={onDelete}
          className="absolute top-0 left-0 bg-red-500 text-white p-0.5 rounded-br opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

export default LazyThumbnail;

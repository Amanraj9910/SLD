import React, { useRef, useEffect } from 'react';
import { FixedSizeList, ListChildComponentProps } from 'react-window';
import LazyThumbnail from './LazyThumbnail';
import type { ProjectImage } from '../../services/my_annotation_api';
import { prefetchAnnotationImages } from '../../hooks/useAnnotationImage';

interface ThumbnailStripProps {
  projectName: string;
  images: ProjectImage[];
  currentIndex: number;
  annotationCounts: Map<number, number>;
  onSelect: (index: number) => void;
  onDeleteImage?: (e: React.MouseEvent, sequence: number, imageId: number) => void;
  canDelete: boolean;
}

const ITEM_SIZE = 88;

const ThumbnailStrip: React.FC<ThumbnailStripProps> = ({
  projectName,
  images,
  currentIndex,
  annotationCounts,
  onSelect,
  onDeleteImage,
  canDelete,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<FixedSizeList>(null);
  const [width, setWidth] = React.useState(800);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      const w = entries[0]?.contentRect.width;
      if (w) setWidth(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (listRef.current && images.length > 0) {
      listRef.current.scrollToItem(Math.max(0, currentIndex - 2), 'smart');
    }
  }, [currentIndex, images.length]);

  useEffect(() => {
    if (!images.length) return;
    const seqs: number[] = [];
    for (let i = currentIndex - 2; i <= currentIndex + 2; i++) {
      if (images[i]) seqs.push(images[i].sequence_number);
    }
    prefetchAnnotationImages(projectName, seqs, 'thumb');
    const fullSeqs: number[] = [];
    if (images[currentIndex]) fullSeqs.push(images[currentIndex].sequence_number);
    if (images[currentIndex - 1]) fullSeqs.push(images[currentIndex - 1].sequence_number);
    if (images[currentIndex + 1]) fullSeqs.push(images[currentIndex + 1].sequence_number);
    prefetchAnnotationImages(projectName, fullSeqs, 'full');
  }, [projectName, images, currentIndex]);

  const Row = ({ index, style }: ListChildComponentProps) => {
    const img = images[index];
    return (
      <div style={{ ...style, display: 'flex', alignItems: 'center', paddingRight: 8 }}>
        <LazyThumbnail
          projectName={projectName}
          sequence={img.sequence_number}
          isActive={index === currentIndex}
          annotationCount={annotationCounts.get(img.id) ?? 0}
          onClick={() => onSelect(index)}
          onDelete={
            onDeleteImage
              ? e => onDeleteImage(e, img.sequence_number, img.id)
              : undefined
          }
          canDelete={canDelete}
        />
      </div>
    );
  };

  if (!images.length) return null;

  return (
    <div ref={containerRef} className="w-full h-24">
      <FixedSizeList
        ref={listRef}
        layout="horizontal"
        height={96}
        width={width}
        itemCount={images.length}
        itemSize={ITEM_SIZE}
        overscanCount={4}
      >
        {Row}
      </FixedSizeList>
    </div>
  );
};

export default ThumbnailStrip;

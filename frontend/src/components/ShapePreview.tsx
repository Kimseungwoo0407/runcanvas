import type { ShapeType } from '../types/api';
import { previewShape, svgPath } from '../utils/shapes';

export function ShapePreview({ shape, letter = 'A' }: { shape: ShapeType; letter?: string }) {
  const points = previewShape(shape, letter);
  return (
    <svg className="shape-preview" viewBox="-8 -8 196 156" role="img" aria-label={`${shape} 미리보기`}>
      <path d={svgPath(points)} fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

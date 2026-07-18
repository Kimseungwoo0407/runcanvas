import { describe, expect, it } from 'vitest';
import { previewShape, svgPath } from './shapes';

describe('previewShape', () => {
  it.each(['heart', 'star', 'circle', 'square', 'dog', 'cat'] as const)('creates a finite closed %s shape', (shape) => {
    const points = previewShape(shape);
    expect(points.length).toBeGreaterThan(4);
    expect(points.every(([x, y]) => Number.isFinite(x) && Number.isFinite(y))).toBe(true);
    expect(points[0]).toEqual(points.at(-1));
    expect(points.every(([x, y]) => x >= 0 && x <= 1 && y >= 0 && y <= 1)).toBe(true);
  });

  it('renders a supported letter and SVG path', () => {
    const points = previewShape('letter', 'R');
    expect(points.length).toBeGreaterThan(5);
    expect(svgPath(points)).toMatch(/^M /);
  });
});

import type { ShapeType } from '../types/api';

export type Point2D = [number, number];

function normalize(points: Point2D[], close = true): Point2D[] {
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = maxX - minX;
  const height = maxY - minY;
  const scale = Math.max(width, height);
  const offsetX = (1 - width / scale) / 2;
  const offsetY = (1 - height / scale) / 2;
  const result = points.map(([x, y]) => [
    (x - minX) / scale + offsetX,
    (y - minY) / scale + offsetY,
  ] as Point2D);
  const first = result[0];
  const last = result.at(-1);
  if (close && first && last && (first[0] !== last[0] || first[1] !== last[1])) {
    result.push([first[0], first[1]]);
  }
  return result;
}

export function previewShape(shape: ShapeType, letter = 'A'): Point2D[] {
  if (shape === 'heart') {
    return normalize(
      Array.from({ length: 120 }, (_, index) => {
        const t = (Math.PI * 2 * index) / 119;
        return [
          16 * Math.sin(t) ** 3,
          -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)),
        ] as Point2D;
      }),
    );
  }
  if (shape === 'star') {
    const points = Array.from({ length: 10 }, (_, index) => {
      const angle = -Math.PI / 2 + (index * Math.PI) / 5;
      const radius = index % 2 === 0 ? 1 : 0.42;
      return [radius * Math.cos(angle), radius * Math.sin(angle)] as Point2D;
    });
    points.push(points[0] ?? [0, 0]);
    return normalize(points);
  }
  if (shape === 'circle') {
    return normalize(
      Array.from({ length: 100 }, (_, index) => {
        const angle = (Math.PI * 2 * index) / 99;
        return [Math.cos(angle), Math.sin(angle)] as Point2D;
      }),
    );
  }
  if (shape === 'square') return [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]];
  if (shape === 'dog') {
    return normalize([
      [0.25, 0.2], [0.04, 0.04], [0.08, 0.45], [0.2, 0.55], [0.17, 0.75],
      [0.32, 0.94], [0.5, 1], [0.68, 0.94], [0.83, 0.75], [0.8, 0.55],
      [0.92, 0.45], [0.96, 0.04], [0.75, 0.2], [0.62, 0.13], [0.38, 0.13],
      [0.25, 0.2], [0.31, 0.43], [0.39, 0.4], [0.31, 0.43], [0.5, 0.58],
      [0.58, 0.66], [0.5, 0.75], [0.42, 0.66], [0.5, 0.58], [0.69, 0.43],
      [0.61, 0.4], [0.69, 0.43], [0.75, 0.2], [0.25, 0.2],
    ]);
  }
  if (shape === 'cat') {
    return normalize([
      [0.1, 0.34], [0.07, 0.02], [0.3, 0.17], [0.5, 0.1], [0.7, 0.17],
      [0.93, 0.02], [0.9, 0.34], [0.96, 0.55], [0.84, 0.79], [0.66, 0.96],
      [0.5, 1], [0.34, 0.96], [0.16, 0.79], [0.04, 0.55], [0.1, 0.34],
      [0.28, 0.42], [0.4, 0.46], [0.28, 0.42], [0.5, 0.6], [0.56, 0.66],
      [0.5, 0.72], [0.44, 0.66], [0.5, 0.6], [0.72, 0.42], [0.6, 0.46],
      [0.72, 0.42], [0.9, 0.34], [0.1, 0.34],
    ]);
  }
  if (shape === 'letter') {
    const glyphs: Record<string, Point2D[]> = {
      A: [[0, 1], [0.5, 0], [1, 1], [0.75, 0.55], [0.25, 0.55], [0, 1]],
      C: [[1, 0.15], [0.75, 0], [0.2, 0], [0, 0.25], [0, 0.75], [0.2, 1], [0.75, 1], [1, 0.85]],
      H: [[0, 0], [0, 1], [0, 0.5], [1, 0.5], [1, 0], [1, 1]],
      M: [[0, 1], [0, 0], [0.5, 0.55], [1, 0], [1, 1]],
      R: [[0, 1], [0, 0], [0.7, 0], [1, 0.2], [0.7, 0.5], [0, 0.5], [1, 1]],
      S: [[1, 0.1], [0.75, 0], [0.2, 0], [0, 0.2], [0.2, 0.5], [0.8, 0.5], [1, 0.8], [0.8, 1], [0.2, 1], [0, 0.9]],
      U: [[0, 0], [0, 0.75], [0.2, 1], [0.8, 1], [1, 0.75], [1, 0]],
    };
    return normalize(glyphs[letter[0]?.toUpperCase() || 'A'] || glyphs.A || []);
  }
  return [];
}

export function svgPath(points: Point2D[], width = 180, height = 140): string {
  return points
    .map(([x, y], index) => `${index === 0 ? 'M' : 'L'} ${x * width} ${y * height}`)
    .join(' ');
}

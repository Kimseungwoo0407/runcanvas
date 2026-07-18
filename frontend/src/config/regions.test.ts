import { describe, expect, it } from 'vitest';
import { inferRegion, isPointInRegion, regions } from './regions';

describe('supported regions', () => {
  it('recognizes Seoul and Cheongju centers', () => {
    expect(isPointInRegion(regions.seoul.center, 'seoul')).toBe(true);
    expect(isPointInRegion(regions.cheongju.center, 'cheongju')).toBe(true);
    expect(inferRegion(regions.seoul.center)).toBe('seoul');
    expect(inferRegion(regions.cheongju.center)).toBe('cheongju');
  });

  it('rejects a point from the other selected city', () => {
    expect(isPointInRegion(regions.seoul.center, 'cheongju')).toBe(false);
  });
});

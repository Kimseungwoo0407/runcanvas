import { describe, expect, it } from 'vitest';
import { formatDistance, formatDuration, formatScore } from './format';

describe('format utilities', () => {
  it('formats distance with precision appropriate to the scale', () => {
    expect(formatDistance(5123)).toBe('5.12 km');
    expect(formatDistance(12500)).toBe('12.5 km');
  });

  it('formats duration and normalized score', () => {
    expect(formatDuration(3660)).toBe('1시간 1분');
    expect(formatScore(0.846)).toBe('85점');
  });
});

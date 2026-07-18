import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MetricsGrid } from './MetricsGrid';

const metrics = {
  distanceM: 8120,
  durationS: 3340,
  shapeScore: 0.84,
  distanceScore: 0.97,
  closureScore: 1,
  overlapRatio: 0.08,
  simplicityScore: 0.9,
  totalScore: 0.88,
  waypointCount: 14,
  maxSnapDistanceM: 32.4,
};

describe('MetricsGrid', () => {
  it('renders the core candidate metrics', () => {
    render(<MetricsGrid metrics={metrics} />);
    expect(screen.getByText('8.12 km')).toBeInTheDocument();
    expect(screen.getByText('84점')).toBeInTheDocument();
    expect(screen.getByText('88점')).toBeInTheDocument();
    expect(screen.getByText('8.0%')).toBeInTheDocument();
    expect(screen.getByText('32m')).toBeInTheDocument();
  });
});

import type { CandidateMetrics } from '../types/api';
import { formatDistance, formatDuration, formatScore } from '../utils/format';

export function MetricsGrid({ metrics }: { metrics: CandidateMetrics }) {
  const items = [
    ['거리', formatDistance(metrics.distanceM)],
    ['예상 시간', formatDuration(metrics.durationS)],
    ['그림 유사도', formatScore(metrics.shapeScore)],
    ['종합 점수', formatScore(metrics.totalScore)],
    ['중복 구간', `${(metrics.overlapRatio * 100).toFixed(1)}%`],
    ['최대 스냅', `${Math.round(metrics.maxSnapDistanceM)}m`],
  ];
  return (
    <dl className="metrics-grid">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

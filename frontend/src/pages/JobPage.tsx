import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { courseApi, generationApi } from '../api/endpoints';
import { LoadingBlock } from '../components/LoadingBlock';
import { MetricsGrid } from '../components/MetricsGrid';
import { CourseMap } from '../map/CourseMap';
import type { Candidate } from '../types/api';
import { errorMessage } from '../utils/error';
import { formatDistance, formatScore } from '../utils/format';

export function JobPage() {
  const { jobId = '' } = useParams();
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [courseName, setCourseName] = useState('새 GPS 아트 코스');

  const job = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => generationApi.get(jobId),
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state === 'queued' || state === 'running' ? 1500 : false;
    },
  });
  const candidates = useQuery({
    queryKey: ['candidates', jobId],
    queryFn: () => generationApi.candidates(jobId),
    enabled: job.data?.state === 'succeeded',
  });
  const cancel = useMutation({ mutationFn: () => generationApi.cancel(jobId) });
  const save = useMutation({
    mutationFn: () => {
      if (!selected) throw new Error('후보를 선택해 주세요.');
      return courseApi.createFromCandidate(courseName.trim() || 'GPS 아트 코스', selected.candidateId);
    },
    onSuccess: (course) => navigate(`/courses/${course.id}`),
  });

  if (job.isLoading) return <LoadingBlock label="생성 작업을 확인하는 중" />;
  if (job.isError) return <div className="alert error">{errorMessage(job.error)}</div>;

  const current = job.data;
  if (!current) return null;
  const selected: Candidate | null =
    candidates.data?.items.find((candidate) => candidate.candidateId === selectedId) ??
    candidates.data?.items[0] ??
    null;

  if (current.state === 'queued' || current.state === 'running') {
    return (
      <section className="progress-page">
        <span className="eyebrow">ROUTE OPTIMIZER</span>
        <h1>도시의 도로망에 그림을 맞추고 있습니다.</h1>
        <p>회전과 크기를 바꾸며 보행 가능한 후보를 평가합니다. 페이지를 닫아도 작업은 계속됩니다.</p>
        <div className="progress-orbit" aria-hidden="true"><span>♡</span></div>
        <div className="progress-track" role="progressbar" aria-valuenow={current.progress} aria-valuemin={0} aria-valuemax={100}>
          <div style={{ width: `${current.progress}%` }} />
        </div>
        <strong>{current.progress}%</strong>
        <button type="button" className="button danger" onClick={() => cancel.mutate()} disabled={cancel.isPending}>
          작업 취소
        </button>
      </section>
    );
  }

  if (current.state === 'failed' || current.state === 'cancelled') {
    return (
      <section className="empty-state">
        <div className="empty-art">×</div>
        <h1>{current.state === 'cancelled' ? '작업이 취소되었습니다.' : '코스를 만들지 못했습니다.'}</h1>
        <p>{current.errorMessage || '위치, 거리, 도형 또는 경유점 수를 바꿔 다시 시도해 주세요.'}</p>
        <button type="button" className="button primary" onClick={() => navigate('/builder')}>설정 바꾸기</button>
      </section>
    );
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <span className="eyebrow">CANDIDATE COMPARISON</span>
          <h1>달릴 선을 고르세요.</h1>
          <p>그림 유사도, 목표 거리, 중복 구간을 함께 비교했습니다.</p>
        </div>
      </div>

      {candidates.isLoading && <LoadingBlock label="후보를 불러오는 중" />}
      {candidates.isError && <div className="alert error">{errorMessage(candidates.error)}</div>}
      {selected && (
        <div className="candidate-layout">
          <div className="candidate-map-wrap">
            <CourseMap
              route={selected.route}
              sourceShape={selected.sourceShape}
              waypoints={selected.waypoints}
            />
            <div className="map-overlay-label">후보 {selected.rank} · {Math.round(selected.rotationDeg)}°</div>
          </div>
          <aside className="candidate-sidebar">
            <MetricsGrid metrics={selected.metrics} />
            <label>
              저장할 코스 이름
              <input value={courseName} onChange={(event) => setCourseName(event.target.value)} maxLength={120} />
            </label>
            {save.isError && <div className="alert error">{errorMessage(save.error)}</div>}
            <button className="button primary wide" onClick={() => save.mutate()} disabled={save.isPending}>
              {save.isPending ? '저장 중…' : '이 후보 저장'}
            </button>
          </aside>
        </div>
      )}

      <div className="candidate-cards">
        {candidates.data?.items.map((candidate) => (
          <button
            type="button"
            key={candidate.candidateId}
            className={`candidate-card ${selected?.candidateId === candidate.candidateId ? 'active' : ''}`}
            onClick={() => setSelectedId(candidate.candidateId)}
          >
            <span>후보 {candidate.rank}</span>
            <strong>{formatScore(candidate.metrics.totalScore)}</strong>
            <small>{formatDistance(candidate.metrics.distanceM)} · 중복 {(candidate.metrics.overlapRatio * 100).toFixed(1)}%</small>
          </button>
        ))}
      </div>
    </section>
  );
}

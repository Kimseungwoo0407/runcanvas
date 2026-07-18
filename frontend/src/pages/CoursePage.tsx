import { useCallback, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { courseApi, generationApi } from '../api/endpoints';
import { downloadWithAuth } from '../api/client';
import { LoadingBlock } from '../components/LoadingBlock';
import { MetricsGrid } from '../components/MetricsGrid';
import { CourseMap } from '../map/CourseMap';
import type { CandidateMetrics, CourseDetail, GeoJSONLineString, LngLat } from '../types/api';
import { errorMessage } from '../utils/error';

interface EditableState {
  waypoints: number[][];
  route: GeoJSONLineString;
  metrics: CandidateMetrics;
}

function midpoint(a: number[], b: number[]): number[] {
  return [((a[0] ?? 0) + (b[0] ?? 0)) / 2, ((a[1] ?? 0) + (b[1] ?? 0)) / 2];
}

export function CoursePage() {
  const { courseId = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState(false);
  const [selectedWaypoint, setSelectedWaypoint] = useState<number | null>(null);
  const [editable, setEditable] = useState<EditableState | null>(null);
  const [undoStack, setUndoStack] = useState<EditableState[]>([]);
  const [redoStack, setRedoStack] = useState<EditableState[]>([]);

  const course = useQuery({
    queryKey: ['course', courseId],
    queryFn: () => courseApi.get(courseId),
  });
  const patch = useMutation({
    mutationFn: (payload: object) => courseApi.patch(courseId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(['course', courseId], data);
      queryClient.invalidateQueries({ queryKey: ['courses'] });
    },
  });
  const clone = useMutation({
    mutationFn: () => courseApi.clone(courseId),
    onSuccess: (data) => navigate(`/courses/${data.id}`),
  });
  const recalculate = useMutation({
    mutationFn: (waypoints: number[][]) => {
      if (!course.data) throw new Error('코스가 준비되지 않았습니다.');
      return generationApi.recalculate({
        sourceShape: course.data.sourceShape,
        waypoints: waypoints.map(([lng, lat]) => ({ lng, lat })),
        targetDistanceKm: course.data.targetDistanceM / 1000,
        distanceTolerancePct: 12,
        closedLoop: true,
        preferences: { avoidMajorRoads: true, preferFootways: false, preferRiverside: false },
      });
    },
    onSuccess: (result) => {
      setEditable({ waypoints: result.waypoints, route: result.route, metrics: result.metrics });
    },
  });
  const saveEdited = useMutation({
    mutationFn: () => {
      if (!course.data || !editable) throw new Error('편집 결과가 없습니다.');
      return courseApi.createEdited({
        name: `${course.data.name} 편집본`,
        shapeType: course.data.shapeType,
        targetDistanceM: course.data.targetDistanceM,
        sourceShape: course.data.sourceShape,
        waypoints: editable.waypoints,
        route: editable.route,
        metrics: editable.metrics,
      });
    },
    onSuccess: (data) => navigate(`/courses/${data.id}`),
  });

  const current = useMemo<EditableState | null>(() => {
    if (editable) return editable;
    if (!course.data) return null;
    return { waypoints: course.data.waypoints, route: course.data.route, metrics: course.data.metrics };
  }, [course.data, editable]);

  const pushUndo = useCallback((state: EditableState) => {
    setUndoStack((items) => [...items.slice(-29), structuredClone(state)]);
    setRedoStack([]);
  }, []);

  const changeWaypoints = useCallback(
    (next: number[][]) => {
      if (!current) return;
      pushUndo(current);
      setEditable({ ...current, waypoints: next });
      recalculate.mutate(next);
    },
    [current, pushUndo, recalculate],
  );

  const moveWaypoint = useCallback(
    (index: number, point: number[]) => {
      if (!current) return;
      const next = current.waypoints.map((item, itemIndex) => (itemIndex === index ? point : item));
      if (index === 0 && next.length > 1) next[next.length - 1] = point;
      if (index === next.length - 1) next[0] = point;
      changeWaypoints(next);
    },
    [changeWaypoints, current],
  );

  const addWaypointAt = useCallback(
    (point: LngLat) => {
      if (!current || current.waypoints.length >= 24) return;
      let bestIndex = 0;
      let bestDistance = Number.POSITIVE_INFINITY;
      const px = point.lng;
      const py = point.lat;
      for (let index = 0; index < current.waypoints.length - 1; index += 1) {
        const a = current.waypoints[index]!;
        const b = current.waypoints[index + 1]!;
        const ax = a[0] ?? 0;
        const ay = a[1] ?? 0;
        const bx = b[0] ?? 0;
        const by = b[1] ?? 0;
        const dx = bx - ax;
        const dy = by - ay;
        const denominator = dx * dx + dy * dy;
        const ratio = denominator === 0 ? 0 : Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / denominator));
        const closestX = ax + ratio * dx;
        const closestY = ay + ratio * dy;
        const distance = Math.hypot(px - closestX, py - closestY);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestIndex = index;
        }
      }
      const next = [...current.waypoints];
      next.splice(bestIndex + 1, 0, [point.lng, point.lat]);
      changeWaypoints(next);
    },
    [changeWaypoints, current],
  );

  const addWaypoint = () => {
    if (!current || current.waypoints.length >= 24) return;
    let bestIndex = 0;
    let bestDistance = -1;
    for (let index = 0; index < current.waypoints.length - 1; index += 1) {
      const a = current.waypoints[index]!;
      const b = current.waypoints[index + 1]!;
      const distance = Math.hypot((a[0] ?? 0) - (b[0] ?? 0), (a[1] ?? 0) - (b[1] ?? 0));
      if (distance > bestDistance) {
        bestDistance = distance;
        bestIndex = index;
      }
    }
    const next = [...current.waypoints];
    next.splice(bestIndex + 1, 0, midpoint(next[bestIndex]!, next[bestIndex + 1]!));
    changeWaypoints(next);
  };

  const deleteWaypoint = () => {
    if (!current || selectedWaypoint === null || current.waypoints.length <= 7) return;
    if (selectedWaypoint === 0 || selectedWaypoint === current.waypoints.length - 1) return;
    const next = current.waypoints.filter((_, index) => index !== selectedWaypoint);
    setSelectedWaypoint(null);
    changeWaypoints(next);
  };

  const undo = () => {
    const prior = undoStack.at(-1);
    if (!prior || !current) return;
    setRedoStack((items) => [...items.slice(-29), structuredClone(current)]);
    setEditable(prior);
    setUndoStack((items) => items.slice(0, -1));
  };

  const redo = () => {
    const next = redoStack.at(-1);
    if (!next || !current) return;
    setUndoStack((items) => [...items.slice(-29), structuredClone(current)]);
    setEditable(next);
    setRedoStack((items) => items.slice(0, -1));
  };

  const downloadGpx = async () => {
    const blob = await downloadWithAuth(`/courses/${courseId}/gpx`);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `runcanvas-${courseId.slice(0, 8)}.gpx`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (course.isLoading) return <LoadingBlock label="코스를 불러오는 중" />;
  if (course.isError) return <div className="alert error">{errorMessage(course.error)}</div>;
  if (!course.data || !current) return null;
  const data: CourseDetail = course.data;

  return (
    <section>
      <div className="page-heading course-detail-heading">
        <div>
          <span className="eyebrow">SAVED COURSE</span>
          <input
            className="title-input"
            value={data.name}
            onChange={(event) => queryClient.setQueryData(['course', courseId], { ...data, name: event.target.value })}
            onBlur={(event) => patch.mutate({ name: event.target.value })}
            aria-label="코스 이름"
          />
          <p>{data.shapeType} · 목표 {(data.targetDistanceM / 1000).toFixed(1)}km</p>
        </div>
        <div className="heading-actions">
          <button className="button secondary" onClick={() => patch.mutate({ isFavorite: !data.isFavorite })}>
            {data.isFavorite ? '★ 즐겨찾기 해제' : '☆ 즐겨찾기'}
          </button>
          <button className="button secondary" onClick={() => clone.mutate()}>복제</button>
          <button className="button primary" onClick={downloadGpx}>GPX 다운로드</button>
        </div>
      </div>

      <div className="course-detail-layout">
        <div className="candidate-map-wrap">
          <CourseMap
            route={current.route}
            sourceShape={data.sourceShape}
            waypoints={current.waypoints}
            editable={editMode}
            onWaypointMove={moveWaypoint}
            onWaypointSelect={setSelectedWaypoint}
            onRouteClick={addWaypointAt}
          />
          {recalculate.isPending && <div className="map-loading-overlay">기존 경로를 유지하며 재계산 중…</div>}
        </div>
        <aside className="course-detail-sidebar">
          <MetricsGrid metrics={current.metrics} />
          <div className="editor-controls">
            <button className="button secondary wide" onClick={() => setEditMode((value) => !value)}>
              {editMode ? '편집 종료' : '경유점 편집'}
            </button>
            {editMode && (
              <>
                <div className="button-row">
                  <button className="button ghost" onClick={addWaypoint} disabled={current.waypoints.length >= 24}>점 추가</button>
                  <button className="button ghost" onClick={deleteWaypoint} disabled={selectedWaypoint === null || current.waypoints.length <= 7}>선택 점 삭제</button>
                  <button className="button ghost" onClick={undo} disabled={!undoStack.length}>실행 취소</button>
                  <button className="button ghost" onClick={redo} disabled={!redoStack.length}>다시 실행</button>
                </div>
                <small>마커를 놓는 순간 한 번만 재라우팅합니다. 지도 선을 클릭하면 경유점이 추가되고 시작점과 마지막 점은 함께 이동합니다.</small>
                <button className="button primary wide" onClick={() => saveEdited.mutate()} disabled={!editable || recalculate.isPending}>편집본 새 코스로 저장</button>
              </>
            )}
          </div>
          <label className="check-row share-toggle">
            <input
              type="checkbox"
              checked={data.shareEnabled}
              onChange={(event) => patch.mutate({ shareEnabled: event.target.checked })}
            />
            난수 링크 공유
          </label>
          {data.shareEnabled && data.shareToken && (
            <button
              className="share-url"
              onClick={() => navigator.clipboard.writeText(`${window.location.origin}${window.location.pathname}#/shared/${data.shareToken}`)}
            >
              공유 링크 복사
            </button>
          )}
          {(recalculate.isError || saveEdited.isError || patch.isError) && (
            <div className="alert error">{errorMessage(recalculate.error || saveEdited.error || patch.error)}</div>
          )}
        </aside>
      </div>
    </section>
  );
}

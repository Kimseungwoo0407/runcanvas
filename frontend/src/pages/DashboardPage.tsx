import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { courseApi, savedPlaceApi } from '../api/endpoints';
import { LoadingBlock } from '../components/LoadingBlock';
import { errorMessage } from '../utils/error';
import { formatDate, formatDistance, formatScore } from '../utils/format';

const shapeName: Record<string, string> = {
  heart: '하트',
  star: '별',
  circle: '원',
  square: '사각형',
  dog: '강아지 얼굴',
  cat: '고양이 얼굴',
  letter: '글자',
  freehand: '자유 드로잉',
};

export function DashboardPage() {
  const [query, setQuery] = useState('');
  const queryClient = useQueryClient();
  const places = useQuery({
    queryKey: ['saved-places'],
    queryFn: savedPlaceApi.list,
    refetchInterval: 5000,
  });
  const precomputeActive = places.data?.items.some((place) => place.status.queued + place.status.running > 0) ?? false;
  const courses = useQuery({
    queryKey: ['courses', query],
    queryFn: () => courseApi.list(query),
    refetchInterval: precomputeActive ? 5000 : false,
  });
  const remove = useMutation({
    mutationFn: courseApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] }),
  });
  const favorite = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) =>
      courseApi.patch(id, { isFavorite: value }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] }),
  });

  return (
    <section>
      <div className="page-heading dashboard-heading">
        <div>
          <span className="eyebrow">YOUR ROUTES</span>
          <h1>도시 위에 남긴 선</h1>
          <p>저장한 GPS 아트 코스를 다시 열고 편집하거나 GPX로 내보내세요.</p>
        </div>
        <Link to="/builder" className="button primary">+ 새 코스 만들기</Link>
      </div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="코스 이름 검색"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="코스 검색"
        />
      </div>

      {places.data?.items.length ? (
        <div className="dashboard-precompute">
          <div>
            <strong>자주 뛰는 장소 코스</strong>
            <span>
              {places.data.items.reduce((sum, place) => sum + place.status.generatedCourses, 0)}개 준비됨
              {precomputeActive ? ' · 백그라운드 생성 중' : ''}
            </span>
          </div>
          <Link to="/settings" className="button secondary compact">장소 관리</Link>
        </div>
      ) : (
        <div className="dashboard-precompute muted-panel">
          <div><strong>집 근처 코스를 미리 준비할까요?</strong><span>장소를 등록하면 거리와 모양별 추천 코스를 자동 생성합니다.</span></div>
          <Link to="/settings" className="button secondary compact">장소 등록</Link>
        </div>
      )}

      {courses.isLoading && <LoadingBlock label="코스를 불러오는 중" />}
      {courses.isError && <div className="alert error">{errorMessage(courses.error)}</div>}
      {remove.isError && <div className="alert error">{errorMessage(remove.error)}</div>}

      {courses.data?.items.length === 0 && (
        <div className="empty-state">
          <div className="empty-art">⌁</div>
          <h2>아직 저장한 코스가 없습니다.</h2>
          <p>잠실에서 시작하는 5km 하트 코스를 첫 작품으로 만들어 보세요.</p>
          <Link to="/builder" className="button primary">첫 코스 만들기</Link>
        </div>
      )}

      <div className="course-grid">
        {courses.data?.items.map((course) => (
          <article className="course-card" key={course.id}>
            <div className="course-card-top">
              <div className="badge-row">
                <span className="shape-badge">{shapeName[course.shapeType]}</span>
                {course.isPregenerated && <span className="auto-badge">미리 생성</span>}
              </div>
              <button
                type="button"
                className={`favorite-button ${course.isFavorite ? 'active' : ''}`}
                aria-label={course.isFavorite ? '즐겨찾기 해제' : '즐겨찾기'}
                onClick={() => favorite.mutate({ id: course.id, value: !course.isFavorite })}
              >
                ★
              </button>
            </div>
            <Link to={`/courses/${course.id}`} className="course-card-link">
              <div className="course-art">{course.shapeType === 'heart' ? '♡' : '⌁'}</div>
              <h2>{course.name}</h2>
              <div className="course-stats">
                <strong>{formatDistance(course.actualDistanceM)}</strong>
                <span>{formatScore(course.totalScore)}</span>
              </div>
              <small>{formatDate(course.updatedAt)}</small>
            </Link>
            <div className="card-actions">
              <Link to={`/courses/${course.id}`} className="button secondary compact">열기</Link>
              <button
                type="button"
                className="button danger compact"
                onClick={() => {
                  if (window.confirm(`'${course.name}' 코스를 삭제할까요?`)) remove.mutate(course.id);
                }}
              >
                삭제
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

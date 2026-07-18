import { useMutation, useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { courseApi } from '../api/endpoints';
import { LoadingBlock } from '../components/LoadingBlock';
import { MetricsGrid } from '../components/MetricsGrid';
import { useAuthStore } from '../features/auth/store';
import { CourseMap } from '../map/CourseMap';
import { errorMessage } from '../utils/error';

export function SharedCoursePage() {
  const { token = '' } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const course = useQuery({
    queryKey: ['shared-course', token],
    queryFn: () => courseApi.shared(token),
    enabled: Boolean(token),
  });
  const clone = useMutation({
    mutationFn: () => courseApi.cloneShared(token),
    onSuccess: (data) => navigate(`/courses/${data.id}`),
  });

  if (course.isLoading) return <LoadingBlock label="공유 코스를 불러오는 중" />;
  if (course.isError) {
    return (
      <main className="public-page">
        <div className="alert error">{errorMessage(course.error)}</div>
        <Link className="button secondary" to="/">RunCanvas 홈</Link>
      </main>
    );
  }
  if (!course.data) return null;

  return (
    <main className="public-page">
      <header className="public-header">
        <Link to="/" className="brand" aria-label="RunCanvas 홈">
          <span className="brand-mark">R</span>
          <span><strong>RunCanvas</strong><small>SHARED COURSE</small></span>
        </Link>
      </header>
      <section>
        <div className="page-heading">
          <div>
            <span className="eyebrow">SHARED GPS ART</span>
            <h1>{course.data.name}</h1>
            <p>{course.data.shapeType} · {(course.data.actualDistanceM / 1000).toFixed(2)}km</p>
          </div>
          {user ? (
            <button className="button primary" onClick={() => clone.mutate()} disabled={clone.isPending}>
              {clone.isPending ? '복제 중…' : '내 코스로 복제'}
            </button>
          ) : (
            <Link className="button primary" to="/login">로그인 후 복제</Link>
          )}
        </div>
        <div className="course-detail-layout">
          <div className="candidate-map-wrap">
            <CourseMap
              route={course.data.route}
              sourceShape={course.data.sourceShape}
              waypoints={course.data.waypoints}
            />
          </div>
          <aside className="course-detail-sidebar">
            <MetricsGrid metrics={course.data.metrics} />
            <div className="alert warning">
              실제 달리기 전에 통행 가능 여부, 공사 구간, 도로 안전 상태를 직접 확인하세요.
            </div>
            {clone.isError && <div className="alert error">{errorMessage(clone.error)}</div>}
          </aside>
        </div>
      </section>
    </main>
  );
}

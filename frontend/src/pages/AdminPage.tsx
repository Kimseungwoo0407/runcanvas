import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';
import { adminApi, healthApi } from '../api/endpoints';
import { LoadingBlock } from '../components/LoadingBlock';
import { useAuthStore } from '../features/auth/store';
import { errorMessage } from '../utils/error';
import { formatDate } from '../utils/format';

export function AdminPage() {
  const currentUser = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [invite, setInvite] = useState<string | null>(null);
  const users = useQuery({ queryKey: ['admin-users'], queryFn: adminApi.users, enabled: currentUser?.role === 'admin' });
  const apiHealth = useQuery({ queryKey: ['api-health'], queryFn: healthApi.api, refetchInterval: 30_000 });
  const routingHealth = useQuery({ queryKey: ['routing-health'], queryFn: healthApi.routing, refetchInterval: 30_000, retry: false });
  const createInvite = useMutation({
    mutationFn: () => adminApi.createInvite(7, 1),
    onSuccess: (data) => setInvite(data.code),
  });
  const setActive = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => adminApi.setUserActive(id, active),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  if (currentUser?.role !== 'admin') return <Navigate to="/" replace />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <span className="eyebrow">SYSTEM CONTROL</span>
          <h1>소규모 운영 관리</h1>
          <p>초대 코드와 사용자 활성 상태를 관리합니다.</p>
        </div>
        <button className="button primary" onClick={() => createInvite.mutate()} disabled={createInvite.isPending}>
          새 초대 코드
        </button>
      </div>
      <div className="health-grid">
        <div className={`health-card ${apiHealth.data?.status === 'ok' ? 'ok' : 'bad'}`}>
          <small>API / DATABASE</small>
          <strong>{apiHealth.isLoading ? '확인 중' : apiHealth.data?.status === 'ok' ? '정상' : '오류'}</strong>
          <span>{apiHealth.data?.version ?? '—'}</span>
        </div>
        <div className={`health-card ${routingHealth.data?.status === 'ok' ? 'ok' : 'bad'}`}>
          <small>ROUTING ENGINE</small>
          <strong>{routingHealth.isLoading ? '확인 중' : routingHealth.data?.status === 'ok' ? '정상' : '연결 실패'}</strong>
          <span>{routingHealth.data?.provider ?? 'GraphHopper'}</span>
        </div>
      </div>
      {invite && (
        <div className="invite-banner">
          <div><small>한 번만 표시되는 초대 코드</small><strong>{invite}</strong></div>
          <button className="button secondary" onClick={() => navigator.clipboard.writeText(invite)}>복사</button>
        </div>
      )}
      {users.isLoading && <LoadingBlock />}
      {(users.isError || createInvite.isError || setActive.isError) && (
        <div className="alert error">{errorMessage(users.error || createInvite.error || setActive.error)}</div>
      )}
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead><tr><th>사용자</th><th>권한</th><th>가입일</th><th>상태</th></tr></thead>
          <tbody>
            {users.data?.items.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.role}</td>
                <td>{formatDate(user.createdAt)}</td>
                <td>
                  <button
                    className={`status-pill ${user.isActive ? 'active' : 'inactive'}`}
                    disabled={user.id === currentUser.id}
                    onClick={() => setActive.mutate({ id: user.id, active: !user.isActive })}
                  >
                    {user.isActive ? '활성' : '비활성'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

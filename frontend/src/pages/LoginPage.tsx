import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { authApi } from '../api/endpoints';
import { useAuthStore } from '../features/auth/store';
import { errorMessage } from '../utils/error';

export function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const accessToken = useAuthStore((state) => state.accessToken);
  const setSession = useAuthStore((state) => state.setSession);
  const navigate = useNavigate();
  const location = useLocation();

  const mutation = useMutation({
    mutationFn: () =>
      mode === 'login'
        ? authApi.login(username, password)
        : authApi.register(username, password, inviteCode),
    onSuccess: (session) => {
      setSession(session);
      const target = (location.state as { from?: string } | null)?.from || '/';
      navigate(target, { replace: true });
    },
  });

  if (accessToken) return <Navigate to="/" replace />;

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-visual">
          <div className="brand large">
            <span className="brand-mark">R</span>
            <span>
              <strong>RunCanvas</strong>
              <small>DRAW IT. RUN IT.</small>
            </span>
          </div>
          <h1>도시 위에<br />당신의 선을 달리세요.</h1>
          <p>그림을 실제 보행 가능한 GPS 아트 코스로 바꾸고, 편집하고, GPX로 가져갑니다.</p>
          <div className="auth-line-art" aria-hidden="true">♡</div>
        </div>
        <form
          className="auth-form"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate();
          }}
        >
          <span className="eyebrow">PRIVATE BETA</span>
          <h2>{mode === 'login' ? '다시 달릴 준비가 됐나요?' : '초대받은 러너 등록'}</h2>
          <label>
            사용자명
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              minLength={3}
              required
            />
          </label>
          <label>
            비밀번호
            <input
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={mode === 'register' ? 8 : 1}
              required
            />
          </label>
          {mode === 'register' && (
            <label>
              초대 코드
              <input value={inviteCode} onChange={(event) => setInviteCode(event.target.value)} required />
            </label>
          )}
          {mutation.isError && <div className="alert error">{errorMessage(mutation.error)}</div>}
          <button className="button primary wide" disabled={mutation.isPending}>
            {mutation.isPending ? '확인 중…' : mode === 'login' ? '로그인' : '계정 만들기'}
          </button>
          <button
            type="button"
            className="text-button"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          >
            {mode === 'login' ? '초대 코드로 가입하기' : '이미 계정이 있습니다'}
          </button>
        </form>
      </section>
    </main>
  );
}

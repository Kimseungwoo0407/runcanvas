import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { authApi } from '../api/endpoints';
import { useAuthStore } from '../features/auth/store';

export function Layout() {
  const user = useAuthStore((state) => state.user);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const clearSession = useAuthStore((state) => state.clearSession);
  const navigate = useNavigate();

  const logout = async () => {
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } finally {
      clearSession();
      navigate('/login');
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/" className="brand" aria-label="RunCanvas 홈">
          <span className="brand-mark">R</span>
          <span>
            <strong>RunCanvas</strong>
            <small>RUN THE LINE</small>
          </span>
        </NavLink>
        <nav aria-label="주 메뉴">
          <NavLink to="/">내 코스</NavLink>
          <NavLink to="/builder">새 코스</NavLink>
          <NavLink to="/settings">설정</NavLink>
          {user?.role === 'admin' && <NavLink to="/admin">관리</NavLink>}
        </nav>
        <div className="user-menu">
          <span>{user?.username}</span>
          <button type="button" className="button ghost compact" onClick={logout}>
            로그아웃
          </button>
        </div>
      </header>
      <main className="page-container">
        <Outlet />
      </main>
      <footer className="footer">
        생성 코스는 실제 주행 전에 도로·통행 제한·안전 상태를 직접 확인하세요.
      </footer>
    </div>
  );
}

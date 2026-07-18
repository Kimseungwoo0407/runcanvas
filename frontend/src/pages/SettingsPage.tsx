import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { meApi } from '../api/endpoints';
import { LoadingBlock } from '../components/LoadingBlock';
import { SavedPlacesSection } from '../components/SavedPlacesSection';
import { useAuthStore } from '../features/auth/store';
import type { UserSettings } from '../types/api';
import { errorMessage } from '../utils/error';

const defaults: UserSettings = {
  defaultPaceMinPerKm: 6,
  distanceUnit: 'km',
  mapTheme: 'default',
  showSourceShape: true,
};

export function SettingsPage() {
  const navigate = useNavigate();
  const clearSession = useAuthStore((state) => state.clearSession);
  const settings = useQuery({ queryKey: ['me-settings'], queryFn: meApi.settings });
  const [form, setForm] = useState<UserSettings | null>(null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [saved, setSaved] = useState(false);

  const currentForm = form ?? settings.data ?? defaults;

  const update = useMutation({
    mutationFn: meApi.updateSettings,
    onSuccess: (data) => {
      setForm(data);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2000);
    },
  });
  const password = useMutation({
    mutationFn: () => meApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      clearSession();
      navigate('/login', { replace: true });
    },
  });
  const remove = useMutation({
    mutationFn: () => meApi.deleteAccount(deletePassword),
    onSuccess: () => {
      clearSession();
      navigate('/login', { replace: true });
    },
  });

  if (settings.isLoading) return <LoadingBlock label="설정을 불러오는 중" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <span className="eyebrow">PREFERENCES & SECURITY</span>
          <h1>설정</h1>
          <p>자주 뛰는 장소, 미리 생성할 코스, 표시 옵션과 계정 보안을 관리합니다.</p>
        </div>
      </div>

      <SavedPlacesSection />

      <div className="settings-grid">
        <form
          className="settings-card"
          onSubmit={(event) => {
            event.preventDefault();
            update.mutate(currentForm);
          }}
        >
          <h2>러닝 기본값</h2>
          <label>
            기본 페이스 (분/km)
            <input
              type="number"
              min="2.5"
              max="15"
              step="0.1"
              value={currentForm.defaultPaceMinPerKm}
              onChange={(event) => setForm({ ...currentForm, defaultPaceMinPerKm: Number(event.target.value) })}
            />
          </label>
          <label>
            거리 단위
            <select
              value={currentForm.distanceUnit}
              onChange={(event) => setForm({ ...currentForm, distanceUnit: event.target.value as 'km' | 'mi' })}
            >
              <option value="km">킬로미터</option>
              <option value="mi">마일</option>
            </select>
          </label>
          <label>
            지도 테마
            <select
              value={currentForm.mapTheme}
              onChange={(event) => setForm({ ...currentForm, mapTheme: event.target.value as 'default' | 'contrast' })}
            >
              <option value="default">기본</option>
              <option value="contrast">고대비</option>
            </select>
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={currentForm.showSourceShape}
              onChange={(event) => setForm({ ...currentForm, showSourceShape: event.target.checked })}
            />
            원본 도형 가이드 표시
          </label>
          <button className="button primary" disabled={update.isPending}>설정 저장</button>
          {saved && <div className="alert success">설정이 저장되었습니다.</div>}
          {update.isError && <div className="alert error">{errorMessage(update.error)}</div>}
        </form>

        <form
          className="settings-card"
          onSubmit={(event) => {
            event.preventDefault();
            password.mutate();
          }}
        >
          <h2>비밀번호 변경</h2>
          <label>
            현재 비밀번호
            <input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} />
          </label>
          <label>
            새 비밀번호
            <input
              type="password"
              minLength={12}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </label>
          <small>12자 이상으로 설정합니다. 변경 후 모든 세션이 종료됩니다.</small>
          <button className="button secondary" disabled={password.isPending || newPassword.length < 12}>
            비밀번호 변경
          </button>
          {password.isError && <div className="alert error">{errorMessage(password.error)}</div>}
        </form>

        <form
          className="settings-card danger-zone"
          onSubmit={(event) => {
            event.preventDefault();
            if (window.confirm('저장된 코스와 계정을 영구 삭제할까요?')) remove.mutate();
          }}
        >
          <h2>계정 삭제</h2>
          <p>위치 정보가 포함된 저장 코스, 생성 작업, 토큰이 함께 삭제됩니다.</p>
          <label>
            비밀번호 확인
            <input type="password" value={deletePassword} onChange={(event) => setDeletePassword(event.target.value)} />
          </label>
          <button className="button danger" disabled={remove.isPending || !deletePassword}>계정 영구 삭제</button>
          {remove.isError && <div className="alert error">{errorMessage(remove.error)}</div>}
        </form>
      </div>
    </section>
  );
}

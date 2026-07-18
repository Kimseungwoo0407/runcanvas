import { beforeEach, describe, expect, it } from 'vitest';
import { useAuthStore } from './store';

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().clearSession();
  });

  it('stores and clears a token session', () => {
    useAuthStore.getState().setSession({
      accessToken: 'access',
      refreshToken: 'refresh',
      tokenType: 'bearer',
      accessExpiresAt: '2026-07-15T00:15:00Z',
      refreshExpiresAt: '2026-08-14T00:00:00Z',
      user: {
        id: 'user-1',
        username: 'runner',
        role: 'user',
        isActive: true,
        createdAt: '2026-07-15T00:00:00Z',
      },
    });
    expect(useAuthStore.getState().accessToken).toBe('access');
    expect(useAuthStore.getState().user?.username).toBe('runner');
    useAuthStore.getState().clearSession();
    expect(useAuthStore.getState().accessToken).toBeNull();
  });
});

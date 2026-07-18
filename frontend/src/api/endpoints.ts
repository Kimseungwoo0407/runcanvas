import { apiRequest } from './client';
import type {
  Candidate,
  CourseDetail,
  CourseSummary,
  GenerationJob,
  GenerationRequest,
  GeocodingResult,
  ParsedNaturalRequest,
  TokenResponse,
  User,
  UserSettings,
  RoutingHealth,
  SavedPlace,
  SavedPlaceCreateRequest,
  SupportedRegion,
} from '../types/api';

export const authApi = {
  login: (username: string, password: string) =>
    apiRequest<TokenResponse>('/auth/login', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ username, password }),
    }),
  register: (username: string, password: string, inviteCode: string) =>
    apiRequest<TokenResponse>('/auth/register', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ username, password, inviteCode }),
    }),
  logout: (refreshToken: string) =>
    apiRequest<void>('/auth/logout', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ refreshToken }),
    }),
};

export const generationApi = {
  create: (request: GenerationRequest) =>
    apiRequest<GenerationJob>('/generation-jobs', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  get: (id: string) => apiRequest<GenerationJob>(`/generation-jobs/${id}`),
  cancel: (id: string) =>
    apiRequest<GenerationJob>(`/generation-jobs/${id}/cancel`, { method: 'POST' }),
  candidates: (id: string) =>
    apiRequest<{ items: Candidate[] }>(`/generation-jobs/${id}/candidates`),
  recalculate: (payload: object) =>
    apiRequest<{
      route: { type: 'LineString'; coordinates: number[][] };
      waypoints: number[][];
      snappedPoints: number[][];
      metrics: Candidate['metrics'];
    }>('/routes/recalculate', { method: 'POST', body: JSON.stringify(payload) }),
};

export const courseApi = {
  list: (query = '') =>
    apiRequest<{ items: CourseSummary[]; nextCursor?: string | null }>(
      `/courses${query ? `?q=${encodeURIComponent(query)}` : ''}`,
    ),
  get: (id: string) => apiRequest<CourseDetail>(`/courses/${id}`),
  createFromCandidate: (name: string, candidateId: string) =>
    apiRequest<CourseDetail>('/courses', {
      method: 'POST',
      body: JSON.stringify({ name, candidateId }),
    }),
  createEdited: (payload: object) =>
    apiRequest<CourseDetail>('/courses', { method: 'POST', body: JSON.stringify(payload) }),
  patch: (id: string, payload: object) =>
    apiRequest<CourseDetail>(`/courses/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  remove: (id: string) => apiRequest<void>(`/courses/${id}`, { method: 'DELETE' }),
  clone: (id: string) => apiRequest<CourseDetail>(`/courses/${id}/clone`, { method: 'POST' }),
  shared: (token: string) =>
    apiRequest<CourseDetail>(`/shared/courses/${token}`, { auth: false }),
  cloneShared: (token: string) =>
    apiRequest<CourseDetail>(`/shared/courses/${token}/clone`, { method: 'POST' }),
};

export const geocodingApi = {
  search: (query: string, region?: SupportedRegion) =>
    apiRequest<{ items: GeocodingResult[] }>(
      `/geocoding/search?q=${encodeURIComponent(query)}${region ? `&region=${region}` : ''}`,
    ),
};

export const savedPlaceApi = {
  list: () => apiRequest<{ items: SavedPlace[] }>('/saved-places'),
  create: (payload: SavedPlaceCreateRequest) =>
    apiRequest<SavedPlace>('/saved-places', { method: 'POST', body: JSON.stringify(payload) }),
  update: (id: string, payload: Partial<SavedPlaceCreateRequest>) =>
    apiRequest<SavedPlace>(`/saved-places/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  precompute: (id: string) =>
    apiRequest<SavedPlace>(`/saved-places/${id}/precompute`, { method: 'POST' }),
  remove: (id: string) => apiRequest<void>(`/saved-places/${id}`, { method: 'DELETE' }),
};

export const aiApi = {
  parse: (text: string) =>
    apiRequest<{ result: ParsedNaturalRequest | null; source: 'rules' | 'llm' | 'form' }>(
      '/ai/parse',
      { method: 'POST', body: JSON.stringify({ text }) },
    ),
};

export const adminApi = {
  users: () => apiRequest<{ items: User[] }>('/admin/users'),
  createInvite: (expiresInDays: number, maxUses: number) =>
    apiRequest<{ id: string; code: string; expiresAt: string; maxUses: number }>(
      '/admin/invite-codes',
      { method: 'POST', body: JSON.stringify({ expiresInDays, maxUses }) },
    ),
  setUserActive: (id: string, isActive: boolean) =>
    apiRequest<User>(`/admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ isActive }),
    }),
};


export const meApi = {
  settings: () => apiRequest<UserSettings>('/me/settings'),
  updateSettings: (settings: UserSettings) =>
    apiRequest<UserSettings>('/me/settings', { method: 'PATCH', body: JSON.stringify(settings) }),
  changePassword: (currentPassword: string, newPassword: string) =>
    apiRequest<void>('/me/password', {
      method: 'POST',
      body: JSON.stringify({ currentPassword, newPassword }),
    }),
  deleteAccount: (password: string) =>
    apiRequest<void>('/me', { method: 'DELETE', body: JSON.stringify({ password }) }),
};

export const healthApi = {
  api: () => apiRequest<{ status: string; database: string; version: string }>('/health', { auth: false }),
  routing: () => apiRequest<RoutingHealth>('/health/routing', { auth: false }),
};

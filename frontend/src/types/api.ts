export type ShapeType = 'heart' | 'star' | 'circle' | 'square' | 'letter' | 'freehand';

export interface User {
  id: string;
  username: string;
  role: 'user' | 'admin';
  isActive: boolean;
  createdAt: string;
}

export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: 'bearer';
  accessExpiresAt: string;
  refreshExpiresAt: string;
  user: User;
}

export interface LngLat {
  lng: number;
  lat: number;
}

export interface GeoJSONLineString {
  type: 'LineString';
  coordinates: number[][];
}

export interface RoutePreferences {
  avoidMajorRoads: boolean;
  preferFootways: boolean;
  preferRiverside: boolean;
}

export interface GenerationRequest {
  start: LngLat;
  shapeType: ShapeType;
  targetDistanceKm: number;
  distanceTolerancePct: number;
  closedLoop: boolean;
  rotationMode: 'auto' | 'fixed';
  rotationDeg?: number | null;
  waypointCount?: number | null;
  shapeText?: string | null;
  freehandPoints?: number[][] | null;
  preferences: RoutePreferences;
  maxCandidates: number;
}

export interface GenerationJob {
  id: string;
  state: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  progress: number;
  errorCode?: string | null;
  errorMessage?: string | null;
  createdAt: string;
  startedAt?: string | null;
  finishedAt?: string | null;
}

export interface CandidateMetrics {
  distanceM: number;
  durationS: number;
  shapeScore: number;
  distanceScore: number;
  closureScore: number;
  overlapRatio: number;
  simplicityScore: number;
  totalScore: number;
  waypointCount: number;
  maxSnapDistanceM: number;
  ascendM?: number | null;
  descendM?: number | null;
}

export interface Candidate {
  candidateId: string;
  rank: number;
  rotationDeg: number;
  route: GeoJSONLineString;
  sourceShape: GeoJSONLineString;
  waypoints: number[][];
  snappedPoints: number[][];
  metrics: CandidateMetrics;
}

export interface CourseSummary {
  id: string;
  name: string;
  shapeType: ShapeType;
  targetDistanceM: number;
  actualDistanceM: number;
  status: 'draft' | 'ready' | 'archived';
  isFavorite: boolean;
  shareEnabled: boolean;
  savedPlaceId?: string | null;
  isPregenerated: boolean;
  totalScore: number;
  createdAt: string;
  updatedAt: string;
}

export interface CourseDetail extends CourseSummary {
  ownerId: string;
  shareToken?: string | null;
  sourceShape: GeoJSONLineString;
  waypoints: number[][];
  route: GeoJSONLineString;
  bbox: number[];
  metrics: CandidateMetrics;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details: Record<string, unknown>;
  requestId?: string;
}

export interface GeocodingResult {
  displayName: string;
  lat: number;
  lng: number;
  boundingBox?: number[] | null;
}

export interface ParsedNaturalRequest {
  shapeType: ShapeType;
  targetDistanceKm: number;
  avoidMajorRoads: boolean;
  preferFootways: boolean;
  preferRiverside: boolean;
  locationText?: string | null;
}


export interface UserSettings {
  defaultPaceMinPerKm: number;
  distanceUnit: 'km' | 'mi';
  mapTheme: 'default' | 'contrast';
  showSourceShape: boolean;
}

export interface RoutingHealth {
  status: string;
  provider: string;
  version?: string | null;
  bbox?: number[] | null;
  profiles?: unknown[];
}

export type PrecomputeShape = 'circle' | 'heart' | 'star' | 'square';

export interface PrecomputeStatus {
  total: number;
  queued: number;
  running: number;
  succeeded: number;
  failed: number;
  cancelled: number;
  generatedCourses: number;
}

export interface SavedPlace {
  id: string;
  name: string;
  location: LngLat;
  privacyRadiusM: number;
  preferRiverside: boolean;
  distancesKm: number[];
  shapes: PrecomputeShape[];
  precomputeRequestedAt?: string | null;
  status: PrecomputeStatus;
  createdAt: string;
  updatedAt: string;
}

export interface SavedPlaceCreateRequest {
  name: string;
  location: LngLat;
  privacyRadiusM: number;
  preferRiverside: boolean;
  distancesKm: number[];
  shapes: PrecomputeShape[];
}

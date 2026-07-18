import { ApiError } from '../api/client';

const friendly: Record<string, string> = {
  ROUTING_UNAVAILABLE: '라우팅 엔진이 준비되지 않았습니다. 잠시 후 다시 시도해 주세요.',
  NO_ROUTE_FOUND: '해당 위치와 거리에서 보행 가능한 그림 코스를 만들지 못했습니다.',
  GENERATION_TIMEOUT: '생성 시간이 초과되었습니다. 거리나 경유점 수를 줄여 주세요.',
  OUTSIDE_SUPPORTED_AREA: '출발점을 선택한 도시(서울 또는 청주)의 지원 범위 안에서 골라 주세요.',
  RATE_LIMITED: '요청이 너무 빠릅니다. 잠시 후 다시 시도해 주세요.',
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return friendly[error.code] || error.message;
  if (error instanceof Error) return error.message;
  return '알 수 없는 오류가 발생했습니다.';
}

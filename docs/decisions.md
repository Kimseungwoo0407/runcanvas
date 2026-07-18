# 설계 결정 기록

| 항목 | 결정 | 근거 |
|---|---|---|
| 프론트·API 도메인 | MVP는 `github.io` + 별도 API 도메인 | 도메인 구매를 전제로 하지 않고 즉시 배포 가능하게 한다. refresh token은 localStorage에 저장하며 XSS 위험을 명시적으로 수용한다. |
| 인증 전환 경로 | 커스텀 도메인 도입 시 HttpOnly `SameSite=Lax` 쿠키 | `run.example.com`과 `api.example.com`을 같은 사이트로 구성하면 Safari 세션 유지 문제가 사라진다. |
| GPU/LLM | 기본 비활성, `qwen3:1.7b` | GPU VRAM을 알 수 없고 상업화 가능성을 배제할 수 없어 Apache 2.0 계열을 선택한다. |
| 지도 타일 | OpenFreeMap Liberty 스타일 | API 키 없이 정적 Pages에서 사용할 수 있고 PC가 꺼져도 지도가 표시된다. |
| 경사 회피 | MVP 제외, UI에서도 숨김 | 고도 import 비용과 RAM 요구를 줄이고 조용히 무시되는 옵션을 만들지 않는다. |
| 공원 선호 | `보행로 선호`로 명칭 변경 | 공원 폴리곤 기반 custom area는 별도 프로젝트 규모이므로 PATH·PEDESTRIAN·LIVING_STREET 우선도 근사만 구현한다. |
| 라우팅 호출 상한 | 40회 | heart/letter/freehand의 거친 회전을 45도 간격 8개로 제한하고 최대 3회 스케일 보정한다. |
| OSM 범위 | 서울 bbox | 초기 검증 지역을 좁혀 GraphHopper import 시간과 메모리를 통제한다. |
| DB 저장 | Docker named volume + SQLite WAL | API와 worker의 다중 프로세스 접근 및 Windows 바인드 마운트 잠금 위험을 줄인다. |
| worker 동시성 | 1 | SQLite 단일 writer 제약과 개인 PC 자원을 고려한다. |
| 라우팅 모드 | flexible + LM | `pass_through`, 동적 custom model, edge detail 사용을 위해 CH를 끄고 LM으로 지연을 완화한다. |
| 주소 검색 | 명시적 검색 버튼 + 서버 캐시 | Nominatim 공개 서비스의 자동완성 금지와 초당 1회 정책을 준수한다. |

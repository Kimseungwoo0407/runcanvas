# RunCanvas 아키텍처

## 배포 토폴로지

```text
GitHub Pages: React + Vite + MapLibre
          │ HTTPS REST
          ▼
Cloudflare Tunnel
          │
          ▼
FastAPI API ───── SQLite named volume
    │
    ├──── worker process
    │         │
    └─────────┴──── GraphHopper 11 foot profile

Optional: Ollama AI profile
```

프론트는 정적 자산만 제공한다. 비밀 키, 사용자 데이터, GraphHopper 포트는 브라우저에 노출하지 않는다. API와 worker는 동일한 이미지와 DB를 공유하되, 라우팅 호출 중 DB 트랜잭션을 열어 두지 않는다.

## 백엔드 계층

- `routers`: HTTP 입출력, 인증·권한, 오류 코드 매핑
- `schemas`: Pydantic v2 API 계약
- `repositories`: SQLAlchemy 쿼리와 사용자별 격리
- `services`: 인증, 생성 작업, 코스 저장, GPX, 지오코딩, AI 폴백
- `services/shapes`: 프레임워크 독립 도형·자유 드로잉 함수
- `services/routing`: `RoutingProvider`와 GraphHopper/mock 구현
- `services/optimization`: 호출 예산, 회전·스케일 반복, 후보 정렬
- `services/scoring`: 형태·거리·폐합·중복·단순성 점수
- `workers`: DB queued 작업을 가져와 처리하는 단일 worker

## 핵심 데이터 흐름

1. 사용자가 출발점과 도형 옵션을 제출한다.
2. API는 요청을 검증하고 `generation_jobs`에 `queued`로 저장한다.
3. worker가 작업을 `running`으로 바꾸고 커밋한다.
4. 도형을 정규화 좌표로 만들고 누적 길이 기준으로 경유점을 샘플링한다.
5. 지역 AEQD 투영에서 미터 단위 스케일·회전·앵커 이동을 적용한다.
6. GraphHopper에 POST `/route`를 호출한다.
7. 라우팅 결과를 점수화하고 허용 거리 범위 안 후보만 저장한다.
8. API 폴링은 상태와 후보를 읽는다.
9. 사용자가 후보를 편집·저장하면 source shape, waypoints, final route를 분리 저장한다.

## 불변식

- 저장 좌표는 항상 `[longitude, latitude]`이다.
- GraphHopper GET 방식은 사용하지 않는다.
- 경유점 순서를 바꾸는 최적화 옵션은 사용하지 않는다.
- `pass_through=true`, `points_encoded=false`, `ch.disable=true`를 GraphHopper 경계에서 강제한다.
- 정확한 사용자 좌표를 로그에 남기지 않는다.
- AI는 좌표·거리·시간·도형 기하를 생성하지 않는다.
- 라우팅 호출은 전역 budget과 deadline을 모두 확인한다.

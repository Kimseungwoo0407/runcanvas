# 검증 결과

검증일: 2026-07-15

## 통과

| 영역 | 명령 | 결과 |
|---|---|---|
| Backend lint | `ruff check .` | 통과 |
| Backend types | `mypy app` | 통과, 오류 0개 |
| Backend tests | `pytest` | 24개 통과 |
| Backend dependencies | `pip check` | broken requirement 없음 |
| Frontend lint | `npm run lint` | 통과 |
| Frontend unit/component tests | `npm run test -- --run` | 4개 파일, 9개 테스트 통과 |
| Frontend production build | `GITHUB_ACTIONS=true VITE_REPOSITORY_NAME=runcanvas npm run build` | 통과, GitHub Pages base `/runcanvas/` 확인 |
| Frontend dependencies | `npm ls --depth=0` | 의존성 트리 정상 |
| Database migration | `alembic upgrade head` | 빈 SQLite DB에 초기 migration 적용 성공 |
| Seed | `python -m app.seed` | 관리자 1명과 초대 코드 생성 성공 |
| Database integrity | `python -m app.db_check` | `PRAGMA integrity_check=ok` |
| Live API smoke | Uvicorn 실행 후 `/api/v1/health`, `/openapi.json` 조회 | 200 응답, OpenAPI 25 paths |
| Configuration syntax | Compose, GraphHopper, GitHub Actions YAML parse 및 shell `bash -n` | 통과 |

## 환경상 실행하지 못한 검증

- 실제 GraphHopper import와 보행 라우팅 smoke test: 현재 실행 환경에 Docker와 `routing/data/seoul.osm.pbf`가 없어 수행하지 못했다. `scripts/download_seoul_osm.sh`와 `scripts/smoke_graphhopper.sh`를 포함했다.
- Playwright 브라우저 E2E: 테스트 코드는 준비되어 있고 CI에서 Chromium을 설치해 실행한다. 현재 환경의 시스템 Chromium에는 관리 정책 `URLBlocklist=["*"]`가 적용되어 localhost 접속이 차단되어 실행 결과를 얻지 못했다.
- Ollama 골든 입력: 선택 기능이며 기본 `AI_ENABLED=false`다. 실제 모델 다운로드와 GPU/CPU 런타임이 없는 환경에서는 실행하지 않았다. 규칙 파서와 AI 비활성 폴백은 일반 테스트 경로에 포함된다.

## 빌드 참고

MapLibre가 별도 지연 로딩 chunk로 분리되어 초기 앱 chunk와 분리된다. 지도 chunk는 라이브러리 자체 크기로 인해 Vite의 500kB 경고를 발생시키지만 빌드는 정상 완료된다.

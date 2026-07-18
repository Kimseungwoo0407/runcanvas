# RunCanvas

RunCanvas는 출발점, 목표 거리, 그림 형태를 입력받아 실제 보행 가능한 도로 위에 GPS 아트 러닝 코스를 생성하는 웹 플랫폼이다. 프론트엔드는 GitHub Pages에 정적 배포하고, FastAPI·SQLite·GraphHopper 백엔드는 개인 PC의 Docker Compose에서 운영한다. 원본 개발 명세는 `docs/RunCanvas_개발명세서_v1.1.docx`에 보존한다.

## 구현 범위

- 초대 코드 기반 가입, 로그인, access/refresh token 인증
- 하트, 별, 원, 사각형, 강아지·고양이 전신, 단선형 영문자, 자유 드로잉 도형 생성
- 회전·스케일 반복, GraphHopper 보행 라우팅, 유사도·거리·폐합·중복·단순성 점수
- 비동기 생성 작업과 폴링, 후보 비교, 경유점 드래그 재라우팅, 최대 30단계 실행 취소
- 사용자별 코스 저장·검색·즐겨찾기·복제·삭제·공유 토큰·GPX 1.1 다운로드
- 명시적 검색 버튼 방식의 Nominatim 주소 검색과 서버 캐시
- 규칙 기반 자연어 파서, 선택적 Ollama JSON Schema 강제 출력
- SQLite WAL, named volume, 일관된 온라인 백업, GitHub Actions CI와 Pages 배포

## 사전 요구사항

- Docker Desktop 또는 Docker Engine + Compose v2
- Git
- GraphHopper용 메모리 4GB 이상 권장
- 서울·청주 OSM 추출 파일 `routing/data/supported-regions.osm.pbf`

Windows에서는 Docker Desktop의 WSL2 백엔드를 사용하고, SQLite DB는 compose의 named volume에 둔다. `storage/exports`와 `storage/backups`만 호스트 바인드 마운트로 사용한다.

## 1. 환경 파일

```bash
cp .env.example .env
```

운영 전 `APP_SECRET_KEY`, `CORS_ORIGINS`, `FRONTEND_ORIGIN`, `NOMINATIM_USER_AGENT`를 실제 값으로 바꾼다. 현재 설계 결정은 `github.io` 배포를 허용하기 위해 refresh token을 브라우저 localStorage에 저장하는 방식이다. 커스텀 도메인을 도입하면 HttpOnly 쿠키 방식으로 전환한다.

## 2. 서울·청주 OSM 데이터 준비

Docker만 설치된 환경에서는 다음 스크립트를 실행한다.

```bash
./scripts/download_seoul_osm.sh
```

스크립트는 대한민국 PBF를 내려받은 뒤 서울과 청주 지원 경계를 하나의 파일로 추출한다. 원본 파일이 이미 있으면 재다운로드하지 않는다.

## 3. 실행

```bash
docker compose up -d --build
```

첫 GraphHopper import는 PC 성능에 따라 수 분 이상 걸린다.

- 프론트 개발 서버: `docker compose --profile dev up frontend`
- API 문서: `http://localhost:8000/docs`
- API 헬스: `http://localhost:8000/api/v1/health`
- 라우팅 헬스: `http://localhost:8000/api/v1/health/routing`

초기 관리자와 초대 코드를 생성한다.

```bash
docker compose run --rm backend python -m app.seed \
  --username admin \
  --password 'StrongLocalPassword123!'
```

명령은 관리자 계정과 최초 초대 코드를 출력한다. 초대 코드 원문은 DB에 저장되지 않으므로 출력 시점에 보관한다.

## 4. 로컬 개발

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

Windows PowerShell은 `.venv\Scripts\Activate.ps1`을 사용한다.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

GraphHopper 없이 UI와 API를 확인하려면 `.env`에서 `ROUTING_PROVIDER=mock`으로 설정한다. mock provider는 테스트와 로컬 화면 검증 전용이며 운영에서는 `graphhopper`를 사용한다.

## 5. 테스트와 품질 검사

```bash
make test
make lint
```

개별 명령:

```bash
cd backend
ruff check app tests
mypy app
pytest

cd ../frontend
npm run lint
npm test -- --run
npm run build
npm run e2e
```

실제 GraphHopper 연동 smoke test:

```bash
./scripts/smoke_graphhopper.sh
```

## 6. 선택 AI

기본 실행에는 Ollama가 포함되지 않는다.

```bash
docker compose --profile ai up -d ollama
docker compose exec ollama ollama pull qwen3:1.7b
```

`.env`에서 `AI_ENABLED=true`로 바꾸고 backend를 재시작한다. 자연어 해석은 규칙 파서 → Ollama → 수동 폼 순서로 폴백한다. 지명은 좌표로 직접 변환하지 않고 주소 검색 결과를 사용자에게 확인받는다.

## 7. GitHub Pages 배포

저장소 Settings에서 Pages source를 GitHub Actions로 설정하고 다음 Repository Variables를 등록한다.

- `VITE_API_BASE_URL`
- `VITE_MAP_STYLE_URL`
- `VITE_REPOSITORY_NAME`

`main` push 시 테스트와 빌드 후 Pages에 배포한다. SPA 라우팅은 `HashRouter`를 사용하므로 별도 404 rewrite가 필요 없다.

## 8. 백업과 복원

```bash
./scripts/backup_db.sh
./scripts/restore_db.sh storage/backups/app-20260715T120000Z.db
```

백업은 SQLite `.backup` API를 사용하며 최근 14개를 유지한다. 복원 스크립트는 서비스 중지, 무결성 검사, 교체, 재기동까지 수행한다.

## 9. 디렉터리

```text
runcanvas/
├── backend/          FastAPI, SQLAlchemy, Alembic, worker, tests
├── frontend/         React, Vite, TypeScript, MapLibre, tests
├── routing/          GraphHopper 설정과 OSM 데이터
├── storage/          GPX export와 DB backup
├── docs/             아키텍처, API, 알고리즘, 운영, 결정 기록
├── scripts/          OSM 준비, 백업, 복원, smoke test
└── .github/workflows CI와 Pages 배포
```

## 안전 고지

생성 코스는 OSM 데이터와 라우팅 엔진 결과에 의존한다. 실제 주행 전 사용자가 지도와 현장을 검토해야 하며, 사유지·공사·통행 제한·조명·교통량 등 실시간 안전 조건을 보장하지 않는다. 저장된 출발지와 경로는 생활 반경을 드러낼 수 있으므로 공유는 기본 비활성화되어 있다.

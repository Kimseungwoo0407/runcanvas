# 운영 절차

## 최초 배포

1. `.env.example`을 `.env`로 복사한다.
2. 32바이트 이상 무작위 `APP_SECRET_KEY`를 설정한다.
3. 실제 Pages URL과 로컬 URL만 `CORS_ORIGINS`에 넣는다.
4. `NOMINATIM_USER_AGENT`에 연락 가능한 운영자 주소를 넣는다.
5. `scripts/download_seoul_osm.sh`를 실행한다.
6. `docker compose up -d --build`를 실행한다.
7. `docker compose logs -f graphhopper`에서 import 완료를 확인한다.
8. `scripts/smoke_graphhopper.sh`와 `/api/v1/health/routing`이 성공하는지 확인한다. GraphHopper 호스트 포트는 외부 공개가 아닌 `127.0.0.1:8989`에만 바인딩된다.
9. `python -m app.seed`로 관리자와 초대 코드를 만든다.
10. Cloudflare named tunnel에서 API 호스트를 `http://backend:8000`으로 연결한다.

## 배포 갱신

```bash
git pull --ff-only
docker compose build backend worker
docker compose run --rm backend alembic upgrade head
docker compose up -d backend worker
```

GraphHopper 버전이나 OSM 파일을 바꾸면 graph-cache를 별도 경로로 새로 import한 뒤 smoke test 후 교체한다. edge ID는 import마다 달라질 수 있으므로 DB에는 저장하지 않는다.

## 장애 확인

```bash
docker compose ps
docker compose logs --tail=200 backend worker graphhopper
curl -fsS http://localhost:8000/api/v1/health
curl -fsS http://localhost:8000/api/v1/health/routing
```

- API만 실패: DB migration, 환경 변수, 포트 확인
- routing만 실패: PBF 경로, JVM heap, import 로그 확인
- 작업이 running에 멈춤: worker 로그 확인 후 재시작; 시작 시 오래된 running 작업은 queued로 복구된다
- `database is locked`: DB가 named volume인지와 worker concurrency가 1인지 확인

## 백업

매일 `scripts/backup_db.sh`를 Task Scheduler 또는 cron으로 실행한다. 스크립트는 컨테이너 내부 SQLite `.backup`을 사용하고 최근 14개만 보관한다.

복원 테스트는 월 1회 별도 프로젝트 이름으로 수행한다.

```bash
COMPOSE_PROJECT_NAME=runcanvas-restore ./scripts/restore_db.sh storage/backups/app-<timestamp>.db
```

복원 후 `PRAGMA integrity_check`, 사용자·코스 count, API 상세 조회까지 확인한다.

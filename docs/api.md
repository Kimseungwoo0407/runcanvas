# REST API

Base URL: `/api/v1`

인증이 필요한 요청은 `Authorization: Bearer <access token>`을 사용한다. 오류 응답은 다음 계약을 따른다.

```json
{
  "code": "VALIDATION_ERROR",
  "message": "입력값을 확인해 주세요.",
  "details": {},
  "requestId": "uuid"
}
```

## 인증

| Method | Path | 설명 |
|---|---|---|
| POST | `/auth/register` | 초대 코드 가입 |
| POST | `/auth/login` | access/refresh token 발급 |
| POST | `/auth/refresh` | refresh token 회전 |
| POST | `/auth/logout` | refresh token 폐기 |
| GET | `/me` | 현재 사용자 |
| GET | `/me/settings` | 사용자 기본 페이스·단위·지도 설정 |
| PATCH | `/me/settings` | 사용자 설정 변경 |
| POST | `/me/password` | 비밀번호 변경 및 refresh token 폐기 |
| DELETE | `/me` | 비밀번호 확인 후 계정·소유 데이터 삭제 |

## 생성

| Method | Path | 설명 |
|---|---|---|
| POST | `/generation-jobs` | 비동기 생성 작업 |
| GET | `/generation-jobs/{id}` | 상태·진행률 |
| POST | `/generation-jobs/{id}/cancel` | 취소 |
| GET | `/generation-jobs/{id}/candidates` | 점수순 후보 |
| POST | `/routes/recalculate` | 편집 경유점 즉시 재라우팅 |

생성 요청:

```json
{
  "start": {"lat": 37.5133, "lng": 127.1001},
  "shapeType": "heart",
  "targetDistanceKm": 8,
  "distanceTolerancePct": 12,
  "closedLoop": true,
  "rotationMode": "auto",
  "rotationDeg": null,
  "waypointCount": 12,
  "shapeText": null,
  "freehandPoints": null,
  "preferences": {
    "avoidMajorRoads": true,
    "preferFootways": false
  },
  "maxCandidates": 3
}
```

## 코스

| Method | Path | 설명 |
|---|---|---|
| POST | `/courses` | 후보 또는 편집 결과 저장 |
| GET | `/courses` | 내 코스 cursor 목록 |
| GET | `/courses/{id}` | 상세 |
| PATCH | `/courses/{id}` | 이름·즐겨찾기·상태·공유 변경 |
| DELETE | `/courses/{id}` | 삭제 |
| POST | `/courses/{id}/clone` | 복제 |
| GET | `/courses/{id}/gpx` | GPX 1.1 |
| GET | `/shared/courses/{token}` | 공유 코스 읽기 |
| POST | `/shared/courses/{token}/clone` | 로그인 사용자가 공유 코스 복제 |

## 보조 기능

| Method | Path | 설명 |
|---|---|---|
| GET | `/health` | API·DB |
| GET | `/health/routing` | GraphHopper `/info` |
| GET | `/geocoding/search?q=` | 명시적 주소 검색 |
| POST | `/ai/parse` | 규칙→Ollama→폼 폴백 |
| POST | `/admin/invite-codes` | 관리자 초대 코드 |
| GET | `/admin/users` | 사용자 상태 |
| PATCH | `/admin/users/{id}` | 활성화 변경 |

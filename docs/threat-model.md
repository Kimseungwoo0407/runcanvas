# 보안과 개인정보

## 보호 대상

- 비밀번호와 access/refresh token
- 초대 코드 원문
- 출발점, 경유점, 최종 경로
- Cloudflare tunnel token과 애플리케이션 secret

## 통제

- Argon2id 비밀번호 해시
- refresh token은 무작위 256비트 값이며 DB에는 SHA-256 hash만 저장
- access token은 15분, refresh token은 30일
- 사용자별 repository 필터와 관리자 role 검사
- CORS allowlist, credential wildcard 금지
- request ID 기반 구조화 로그, 좌표 로그 제외
- GraphHopper는 compose internal network만 사용
- 공유는 기본 비활성화, 활성화 시 192비트 난수 token 발급
- 주소 검색은 서버 proxy와 cache를 사용하고 Nominatim 호출을 초당 1회로 제한

## 수용한 위험

MVP는 커스텀 도메인을 전제로 하지 않아 refresh token을 localStorage에 저장한다. 따라서 XSS가 발생하면 token 탈취가 가능하다. 프론트에 제3자 스크립트를 넣지 않고 CSP를 배포 헤더에서 적용하며, 커스텀 도메인 도입 시 host-only HttpOnly cookie로 전환한다.

위치 데이터는 생활 반경을 노출할 수 있다. 홈 위치 자동 저장은 없고, 코스 삭제와 계정 비활성화를 제공한다. 공유 URL은 검색 불가능한 난수 token이나 URL 유출 시 접근 가능하므로 민감한 출발점은 공유하지 않는다.

# 경로 생성 알고리즘

## 1. 도형 계약

도형은 `list[[x, y]]` 형태이며 각 값은 0~1 범위다. 폐곡선은 첫 점과 마지막 점이 같다. heart, star, circle, square, letter, freehand가 모두 동일한 계약을 사용한다.

## 2. 균등 리샘플링

파라미터 간격이 아니라 누적 선 길이를 계산해 목표 거리 간격마다 보간한다. 꼭짓점은 원본 템플릿에 충분한 밀도로 포함하고 최종 경유점은 6~24개로 제한한다.

## 3. 지도 변환

출발점을 중심으로 한 AEQD 지역 투영을 만든다.

```text
normalized → center at origin → meter scale → rotate → first point anchored at start → WGS84
```

도형의 정규화 길이 `L`과 목표 거리 `D`에 대해 초기 스케일은 `D / L * 0.78`이다. 실제 도로 우회에 따라 `target / actual` 비율을 0.85~1.15로 clamp해 반복 보정한다.

## 4. 회전 전략

- circle: 0도
- square: 0, 30, 60도
- five-point star: 0, 24, 48도
- heart, letter, freehand: 0~315도, 45도 간격

각 회전에서 최대 3회 스케일을 보정한다. 전역 호출 상한 40회와 90초 deadline 중 하나가 먼저 도달하면 중단한다.

## 5. 점수

```text
total = 0.50 * shape_similarity
      + 0.25 * distance_score
      + 0.10 * closure_score
      + 0.10 * (1 - overlap_ratio)
      + 0.05 * simplicity_score
      - snap_penalty
```

- 형태 점수: 정규화 후 circular shift를 고려한 symmetric Chamfer distance
- 거리 점수: 허용 오차 안에서 선형 감소, 범위 밖 0
- 폐합 점수: 시작·종료 거리 기반
- 중복률: GraphHopper `details=edge_id`에서 동일 edge 반복 길이 비율
- 단순성: 급격한 연속 방향 전환과 매우 짧은 세그먼트 패널티
- 스냅 패널티: 경유점 최대 스냅 거리가 150m를 넘으면 증가

## 6. 자유 드로잉

1. 입력 점이 3개 이상인지 검사한다.
2. Ramer-Douglas-Peucker epsilon을 캔버스 대각선의 0.75%로 적용한다.
3. 종횡비 10:1 초과를 거부한다.
4. closed loop이면 마지막 점을 첫 점에 스냅한다.
5. 종횡비를 유지해 0~1로 정규화한다.
6. 프리셋과 같은 리샘플링·투영·라우팅 파이프라인을 사용한다.

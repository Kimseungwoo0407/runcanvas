#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${GRAPHHOPPER_PUBLIC_URL:-http://localhost:8989}"

curl -fsS "$BASE_URL/info" >/dev/null
curl -fsS -X POST "$BASE_URL/route" \
  -H 'Content-Type: application/json' \
  -d '{
    "profile":"foot",
    "points":[[127.1001,37.5133],[127.1030,37.5150],[127.1001,37.5133]],
    "points_encoded":false,
    "ch.disable":true,
    "pass_through":true,
    "details":["edge_id"],
    "instructions":false
  }' | python -c 'import json,sys; p=json.load(sys.stdin)["paths"][0]; assert p["distance"]>0; print({"distance":p["distance"],"points":len(p["points"]["coordinates"])})'

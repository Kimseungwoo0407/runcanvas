#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/routing/data"
KOREA_PBF="$DATA_DIR/south-korea-latest.osm.pbf"
SEOUL_PBF="$DATA_DIR/seoul.osm.pbf"
KOREA_URL="https://download.geofabrik.de/asia/south-korea-latest.osm.pbf"
SEOUL_BBOX="126.76,37.41,127.18,37.70"

mkdir -p "$DATA_DIR"

if [[ ! -f "$KOREA_PBF" ]]; then
  docker run --rm -v "$DATA_DIR:/data" curlimages/curl:8.16.0 \
    -fL --retry 5 --output /data/south-korea-latest.osm.pbf "$KOREA_URL"
fi

docker run --rm -v "$DATA_DIR:/data" debian:bookworm-slim \
  sh -c "apt-get update \
    && apt-get install -y --no-install-recommends osmium-tool \
    && osmium extract --bbox '$SEOUL_BBOX' --strategy complete_ways \
      --overwrite --output /data/seoul.osm.pbf /data/south-korea-latest.osm.pbf"

ls -lh "$SEOUL_PBF"

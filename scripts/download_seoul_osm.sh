#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/routing/data"
KOREA_PBF="$DATA_DIR/south-korea-latest.osm.pbf"
SUPPORTED_PBF="$DATA_DIR/supported-regions.osm.pbf"
KOREA_URL="https://download.geofabrik.de/asia/south-korea-latest.osm.pbf"
SEOUL_BBOX="126.76,37.41,127.18,37.70"
CHEONGJU_BBOX="127.25,36.45,127.75,36.85"

mkdir -p "$DATA_DIR"

if [[ ! -f "$KOREA_PBF" ]]; then
  docker run --rm -v "$DATA_DIR:/data" curlimages/curl:8.16.0 \
    -fL --retry 5 --output /data/south-korea-latest.osm.pbf "$KOREA_URL"
fi

docker run --rm -v "$DATA_DIR:/data" debian:bookworm-slim \
  sh -c "apt-get update \
    && apt-get install -y --no-install-recommends osmium-tool \
    && osmium extract --bbox '$SEOUL_BBOX' --strategy complete_ways \
      --overwrite --output /tmp/seoul.osm.pbf /data/south-korea-latest.osm.pbf \
    && osmium extract --bbox '$CHEONGJU_BBOX' --strategy complete_ways \
      --overwrite --output /tmp/cheongju.osm.pbf /data/south-korea-latest.osm.pbf \
    && osmium merge --overwrite --output /data/supported-regions.osm.pbf \
      /tmp/seoul.osm.pbf /tmp/cheongju.osm.pbf"

ls -lh "$SUPPORTED_PBF"

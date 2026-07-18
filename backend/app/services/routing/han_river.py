from __future__ import annotations

from typing import Any

# Deliberately broad corridors around the Han River in Seoul and Musimcheon in Cheongju.
# GraphHopper uses these request-scoped custom areas only when riverside preference is enabled.
RIVERSIDE_CORRIDORS: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "han_river_corridor",
            "properties": {"id": "han_river_corridor", "name": "한강 강변 권역"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [126.755, 37.595],
                        [126.800, 37.585],
                        [126.840, 37.575],
                        [126.880, 37.565],
                        [126.910, 37.548],
                        [126.940, 37.540],
                        [126.970, 37.530],
                        [127.000, 37.528],
                        [127.040, 37.540],
                        [127.080, 37.542],
                        [127.120, 37.558],
                        [127.180, 37.570],
                        [127.180, 37.540],
                        [127.120, 37.525],
                        [127.080, 37.512],
                        [127.040, 37.510],
                        [127.000, 37.498],
                        [126.970, 37.498],
                        [126.940, 37.505],
                        [126.910, 37.515],
                        [126.880, 37.540],
                        [126.840, 37.550],
                        [126.800, 37.560],
                        [126.755, 37.570],
                        [126.755, 37.595],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "id": "musimcheon_corridor",
            "properties": {"id": "musimcheon_corridor", "name": "청주 무심천 강변 권역"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [127.466, 36.480],
                        [127.468, 36.535],
                        [127.474, 36.585],
                        [127.480, 36.625],
                        [127.486, 36.665],
                        [127.493, 36.710],
                        [127.502, 36.775],
                        [127.526, 36.772],
                        [127.516, 36.708],
                        [127.509, 36.663],
                        [127.503, 36.622],
                        [127.497, 36.582],
                        [127.491, 36.532],
                        [127.490, 36.480],
                        [127.466, 36.480],
                    ]
                ],
            },
        },
    ],
}

# Backward-compatible import name for older callers.
HAN_RIVER_CORRIDOR = RIVERSIDE_CORRIDORS

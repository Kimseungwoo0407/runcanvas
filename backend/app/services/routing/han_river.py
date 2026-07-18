from __future__ import annotations

from typing import Any

# A deliberately broad corridor around the Han River and its riverside parks in Seoul.
# GraphHopper uses this request-scoped custom area only when the user enables riverside preference.
HAN_RIVER_CORRIDOR: dict[str, Any] = {
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
        }
    ],
}

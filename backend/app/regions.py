from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RegionCode = Literal["seoul", "cheongju"]


@dataclass(frozen=True)
class SupportedRegion:
    code: RegionCode
    label: str
    center_lng: float
    center_lat: float
    bbox: tuple[float, float, float, float]

    def contains(self, lng: float, lat: float) -> bool:
        min_lng, min_lat, max_lng, max_lat = self.bbox
        return min_lng <= lng <= max_lng and min_lat <= lat <= max_lat


SUPPORTED_REGIONS: dict[RegionCode, SupportedRegion] = {
    "seoul": SupportedRegion(
        code="seoul",
        label="서울",
        center_lng=127.1001,
        center_lat=37.5133,
        bbox=(126.76, 37.41, 127.18, 37.70),
    ),
    "cheongju": SupportedRegion(
        code="cheongju",
        label="청주",
        center_lng=127.4890,
        center_lat=36.6424,
        bbox=(127.25, 36.45, 127.75, 36.85),
    ),
}


def get_region(code: RegionCode) -> SupportedRegion:
    return SUPPORTED_REGIONS[code]


def region_for_point(lng: float, lat: float) -> SupportedRegion | None:
    return next((region for region in SUPPORTED_REGIONS.values() if region.contains(lng, lat)), None)


def supported_region_details() -> list[dict[str, object]]:
    return [
        {
            "code": region.code,
            "label": region.label,
            "center": {"lng": region.center_lng, "lat": region.center_lat},
            "bbox": list(region.bbox),
        }
        for region in SUPPORTED_REGIONS.values()
    ]

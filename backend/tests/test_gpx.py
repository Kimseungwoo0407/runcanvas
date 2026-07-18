from __future__ import annotations

import gpxpy

from app.services.gpx import build_gpx


def test_gpx_round_trip() -> None:
    coordinates = [[127.0, 37.0], [127.001, 37.001, 12.5], [127.0, 37.0]]
    xml = build_gpx(name="Heart 5K", coordinates=coordinates, waypoints=coordinates[:2])
    parsed = gpxpy.parse(xml)
    assert parsed.version == "1.1"
    assert len(parsed.tracks[0].segments[0].points) == len(coordinates)
    assert parsed.tracks[0].segments[0].points[1].elevation == 12.5

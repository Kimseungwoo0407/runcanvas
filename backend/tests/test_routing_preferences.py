from __future__ import annotations

from app.services.routing.base import RouteOptions
from app.services.routing.graphhopper import GraphHopperRoutingProvider


def test_riverside_custom_model_adds_seoul_and_cheongju_areas_and_safer_edges() -> None:
    model = GraphHopperRoutingProvider._custom_model(RouteOptions(prefer_riverside=True))

    assert model is not None
    assert model["areas"]["type"] == "FeatureCollection"  # type: ignore[index]
    priority = model["priority"]
    assert isinstance(priority, list)
    conditions = [rule["if"] for rule in priority]
    feature_ids = {feature["id"] for feature in model["areas"]["features"]}  # type: ignore[index]
    assert feature_ids == {"han_river_corridor", "musimcheon_corridor"}
    assert "!in_han_river_corridor && !in_musimcheon_corridor" in conditions
    assert "road_environment == TUNNEL" in conditions
    assert "road_class == TRACK" in conditions

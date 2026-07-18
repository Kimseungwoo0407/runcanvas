from __future__ import annotations

from app.services.routing.base import RouteOptions
from app.services.routing.graphhopper import GraphHopperRoutingProvider


def test_riverside_custom_model_adds_han_river_area_and_safer_edges() -> None:
    model = GraphHopperRoutingProvider._custom_model(RouteOptions(prefer_riverside=True))

    assert model is not None
    assert model["areas"]["type"] == "FeatureCollection"  # type: ignore[index]
    priority = model["priority"]
    assert isinstance(priority, list)
    conditions = [rule["if"] for rule in priority]
    assert "!in_han_river_corridor" in conditions
    assert "road_environment == TUNNEL" in conditions
    assert "road_class == TRACK" in conditions

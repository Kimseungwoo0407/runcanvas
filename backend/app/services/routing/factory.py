from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.services.routing.base import RoutingProvider
from app.services.routing.graphhopper import GraphHopperRoutingProvider
from app.services.routing.mock import MockRoutingProvider


@lru_cache
def get_routing_provider() -> RoutingProvider:
    settings = get_settings()
    if settings.ROUTING_PROVIDER == "mock":
        return MockRoutingProvider()
    return GraphHopperRoutingProvider(settings.GRAPHHOPPER_URL)

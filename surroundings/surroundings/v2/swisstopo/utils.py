from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import (
    SWISSTOPO_BRIDGE_TYPES,
    SWISSTOPO_TUNNEL_TYPES,
)


def is_tunnel(geometry: Geometry) -> bool:
    """Returns true if the railway tracks or streets are in a tunnel"""
    return geometry.properties["KUNSTBAUTE"] in SWISSTOPO_TUNNEL_TYPES


def is_bridge(geometry: Geometry) -> bool:
    """Returns true if the railway tracks or streets are on a bridge"""
    return geometry.properties["KUNSTBAUTE"] in SWISSTOPO_BRIDGE_TYPES

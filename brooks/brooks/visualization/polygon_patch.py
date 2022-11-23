"""Copied from the unmaintained descartes python package"""
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from numpy import asarray, concatenate, ones
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry.base import BaseGeometry

from common_utils.exceptions import InvalidShapeException


class Polygon:
    # Adapt Shapely or GeoJSON/geo_interface polygons to a common interface
    def __init__(self, context):
        if hasattr(context, "interiors"):
            self.context = context
        else:
            self.context = getattr(context, "__geo_interface__", context)

    @property
    def geom_type(self):
        return getattr(self.context, "geom_type", None) or self.context["type"]

    @property
    def exterior(self):
        return getattr(self.context, "exterior", None) or self.context["coordinates"][0]

    @property
    def interiors(self):
        value = getattr(self.context, "interiors", None)
        if value is None:
            value = self.context["coordinates"][1:]
        return value


def PolygonPath(polygon: BaseGeometry):
    """Constructs a compound matplotlib path from a Shapely or GeoJSON-like
    geometric object"""
    if not isinstance(polygon, ShapelyPolygon):
        raise InvalidShapeException(
            f"Geometry should have type 'Polygon' but has '{polygon.geom_type}'"
        )
    this = Polygon(polygon)

    def coding(ob):
        # The codes will be all "LINETO" commands, except for "MOVETO"s at the
        # beginning of each subpath
        n = len(getattr(ob, "coords", None) or ob)
        vals = ones(n, dtype=Path.code_type) * Path.LINETO
        vals[0] = Path.MOVETO
        return vals

    vertices = concatenate(
        [asarray(this.exterior.coords)[:, :2]]
        + [asarray(r.coords)[:, :2] for r in this.interiors]
    )
    codes = concatenate([coding(this.exterior)] + [coding(r) for r in this.interiors])
    return Path(vertices, codes)


class PolygonPatch(PathPatch):
    """
    [This is not the original descartes PolygonPatch anymore!!!!]

    Constructs a matplotlib patch from a geometric object

    The `polygon` may be a Shapely or GeoJSON-like object with or without holes.
    The `kwargs` are those supported by the matplotlib.patches.Polygon class
    constructor. Returns an instance of matplotlib.patches.PathPatch

    """

    def __init__(self, polygon, **kwargs):
        super().__init__(PolygonPath(polygon), **kwargs)

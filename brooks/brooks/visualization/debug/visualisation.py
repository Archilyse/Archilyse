import random
from typing import Any, Dict, Iterable, List, Union

import matplotlib.pyplot as plt
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from brooks.visualization.polygon_patch import PolygonPatch

BACKGROUND_C = "#000000"
POINT_FACE_C = "#0B5F67"
POINT_EDGE_C = "#70C0C7"
POINT_ALPHA = 0.5
POLYGON_FACE_C = "#133C70"
POLYGON_EDGE_C = "#5073A1"
POLYGON_ALPHA = 0.5
LINESTRING_FACE_C = "#7F0000"
LINESTRING_EDGE_C = "#ff0000"
LINESTRING_ALPHA = 0.5


class Plotter:
    class PlotGeometry:
        def __init__(self, polygon, patch, raw):
            self.polygon = polygon
            self.patch = patch
            self.raw = raw

    def __init__(
        self,
        geometries: Iterable[Union[Polygon, Point, LineString, MultiPolygon]],
        patch_arguments: List[Dict] = None,
        title=None,
        save_fig=False,
    ):
        self._geometries = geometries
        self._patch_arguments = patch_arguments
        self._plot_geometries: List[Any] = []
        self._selected_patches: List[Any] = []
        self._save_fig = save_fig
        self._title = title
        self._fig, self._ax = plt.subplots()
        self.plot()
        plt.close()

    def plot(self):
        for i, geometry in enumerate(self._geometries):
            if isinstance(geometry, Point):
                self._plot_point(geometry, i)

            elif isinstance(geometry, LineString):
                self._plot_linestring(geometry, i)

            elif isinstance(geometry, Polygon):
                self._plot_polygon(geometry, i)

            elif isinstance(geometry, MultiPolygon):
                self._plot_multipolygon(geometry, i)

            elif isinstance(geometry, MultiPoint):
                self._plot_multipoint(geometry, i)

            elif isinstance(geometry, MultiLineString):
                for sub_geometry in geometry:
                    self._plot_linestring(sub_geometry, i)

        self._ax.autoscale()
        self._ax.get_xaxis().get_major_formatter().set_useOffset(False)
        self._ax.get_yaxis().get_major_formatter().set_useOffset(False)
        self._ax.set_aspect("equal")
        if self._title:
            plt.title(self._title)
        if self._save_fig:
            plt.savefig(str(self._title) + ".jpg")
        else:
            plt.show()

    def _plot_polygon(self, polygon: Polygon, index: int, raw=None):
        patch_args = {
            "facecolor": "#%02X%02X%02X"
            % (
                random.randint(0, 220),  # To avoid white colors
                random.randint(0, 220),
                random.randint(0, 220),
            ),
            "alpha": POLYGON_ALPHA,
        }
        if self._patch_arguments:
            patch_args.update(self._patch_arguments[index])
        patch = self._ax.add_patch(PolygonPatch(polygon.buffer(0), **patch_args))

        if raw is None:
            raw = polygon
        plot_geometry = self.PlotGeometry(polygon, patch, raw)
        self._plot_geometries.append(plot_geometry)

    def _plot_linestring(self, linestring: LineString, index: int):
        self._plot_polygon(linestring.buffer(0.01), index)

    def _plot_multipolygon(self, multipolygon: MultiPolygon, index: int):
        for polygon in multipolygon:
            self._plot_polygon(polygon, index)

    def _plot_multipoint(self, multipoint: MultiPoint, index: int):
        for point in multipoint:
            self._plot_point(point, index)

    def _plot_point(self, point: Point, index: int):
        polygon = point.buffer(1)
        self._plot_polygon(polygon, index=index, raw=point)


def draw(
    geometries: Union[
        Iterable[Union[Polygon, Point, LineString, MultiPolygon]],
        Union[Polygon, Point, LineString, MultiPolygon],
    ],
    patch_args: List[Dict] = None,
    title=None,
    save_fig=None,
):
    if isinstance(geometries, MultiPolygon):
        geometries = [e for e in geometries.geoms]
    else:
        if not hasattr(geometries, "__iter__"):
            geometries = [geometries]

    Plotter(geometries, patch_arguments=patch_args, title=title, save_fig=save_fig)

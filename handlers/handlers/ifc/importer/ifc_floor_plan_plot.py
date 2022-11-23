from typing import DefaultDict, Dict, Iterator, List, Union

from matplotlib import pyplot as plt
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.strtree import STRtree

from brooks.models import SimOpening
from brooks.visualization.utils import get_visual_center
from dufresne.polygon.parameters_minimum_rotated_rectangle import (
    get_parameters_of_minimum_rotated_rectangle,
)
from handlers.ifc.constants import IFC_ELEMENTS_PLOT_TEXT_WHITELIST
from ifc_reader.constants import (
    IFC_CURTAIN_WALL,
    IFC_DOOR,
    IFC_WALL,
    IFC_WALL_STANDARD_CASE,
    IFC_WINDOW,
)
from ifc_reader.types import Ifc2DEntity, IfcSpaceProcessed


class IfcFloorPlanPlot:
    DEFAULT_GEOMETRY_STYLE: Dict = {
        "fill": True,
        "facecolor": "#FFFFFF00",
        "linewidth": 2,
        "edgecolor": "#000000FF",
    }

    GEOMETRY_STYLES: Dict = {
        IFC_WALL: {**DEFAULT_GEOMETRY_STYLE, "facecolor": "#F0F0F0FF"},
        IFC_WALL_STANDARD_CASE: {**DEFAULT_GEOMETRY_STYLE, "facecolor": "#F0F0F0FF"},
        IFC_CURTAIN_WALL: {**DEFAULT_GEOMETRY_STYLE, "facecolor": "#F0F0F0FF"},
        IFC_WINDOW: {
            **DEFAULT_GEOMETRY_STYLE,
            "facecolor": "#22208DFF",
        },
        IFC_DOOR: {**DEFAULT_GEOMETRY_STYLE, "facecolor": "#FFFFFFFF"},
        "spaces": {
            "linewidth": 1,
            "linestyle": "--",
            "facecolor": "#FFFFFF00",
            "edgecolor": "#000000B3",
        },
    }

    # for openings we plot another geometry (the footprint) to produce
    # orthogonal lines for windows / white fill for doors
    EXTRA_OPENING_GEOMETRY_STYLES: Dict = {
        IFC_WINDOW: {
            **GEOMETRY_STYLES[IFC_WINDOW],
            "facecolor": "#FFFFFF00",
            "edgecolor": "#000000FF",
            "linewidth": 1,
        },
        IFC_DOOR: {
            **GEOMETRY_STYLES[IFC_DOOR],
            "edgecolor": "#000000FF",
            "linewidth": 1,
        },
    }

    DEFAULT_GEOMETRY_Z_ORDER: int = 0

    GEOMETRY_ZORDER: Dict = {
        IFC_WALL: 1,
        IFC_WALL_STANDARD_CASE: 1,
        IFC_CURTAIN_WALL: 1,
        IFC_WINDOW: 2,
        IFC_DOOR: 2,
    }

    def __init__(
        self,
        storey_entities: DefaultDict[str, List[Union[Ifc2DEntity, IfcSpaceProcessed]]],
        width: float,
        height: float,
    ):
        self.storey_entities: DefaultDict[
            str, List[Union[Ifc2DEntity, IfcSpaceProcessed]]
        ] = storey_entities
        self.figure = plt.Figure(figsize=(width / 100, height / 100))

        self.axis = self.figure.add_axes([0, 0, 1, 1])
        self.axis.set_facecolor("#FFFFFF00")
        self.axis.set_alpha(1.0)

        self.axis.margins(x=0.0, y=0.0)
        for attr in (
            self.axis.axes.get_xaxis(),
            self.axis.axes.get_yaxis(),
            self.axis.spines["top"],
            self.axis.spines["left"],
            self.axis.spines["bottom"],
            self.axis.spines["right"],
        ):
            attr.set_visible(False)

    @staticmethod
    def _plot_extra_opening_geometry(
        geometry: MultiPolygon, wall_strtree: STRtree
    ) -> Iterator[Polygon]:
        """For openings we plot another geometry (the footprint) to produce
        orthogonal lines for windows / white fill for doors
        """
        polygon = geometry.minimum_rotated_rectangle
        intersecting_walls = sorted(
            [wall for wall in wall_strtree.query(polygon) if wall.intersects(polygon)],
            key=lambda z: z.intersection(polygon).area,
        )

        if intersecting_walls:
            wall: Polygon = intersecting_walls.pop()
            # HACK: Because adjust_opening_geometry does not work for square-shaped walls.
            (
                _,
                _,
                wall_length,
                wall_width,
                _,
            ) = get_parameters_of_minimum_rotated_rectangle(
                polygon=wall, rotation_axis_convention="lower_left"
            )
            if min(wall_length, wall_width) / max(wall_length, wall_width) < 0.6:
                yield SimOpening.adjust_geometry_to_wall(
                    opening=polygon, wall=wall, buffer_width=1.05
                )

    def create_plot(self, scale_factor: float) -> plt.Figure:
        wall_strtree = STRtree(
            [
                polygon.minimum_rotated_rectangle
                for ifc_type, entities in self.storey_entities.items()
                for entity in entities
                for polygon in entity.geometry.geoms
                if ifc_type
                in (
                    IFC_WALL,
                    IFC_WALL_STANDARD_CASE,
                    IFC_CURTAIN_WALL,
                )
            ]
        )
        for ifc_type, entries in sorted(
            self.storey_entities.items(),
            key=lambda z: (
                self.GEOMETRY_ZORDER.get(z[0], self.DEFAULT_GEOMETRY_Z_ORDER),
                z[0],
            ),
        ):
            style = self.GEOMETRY_STYLES.get(ifc_type, self.DEFAULT_GEOMETRY_STYLE)

            for entity in sorted(entries, key=lambda e: e.geometry.area):
                if ifc_type in {
                    IFC_WINDOW,
                    IFC_DOOR,
                }:
                    for opening in self._plot_extra_opening_geometry(
                        geometry=entity.geometry,
                        wall_strtree=wall_strtree,
                    ):
                        extra_geometry_style = self.EXTRA_OPENING_GEOMETRY_STYLES[
                            ifc_type
                        ]
                        self.add_polygon(shape=opening, **extra_geometry_style)
                    # Doors geometry it's just a line in the Steiner case, but we should create our own geometry if
                    # we don't want to keep adding exceptions here
                    if ifc_type == IFC_DOOR:
                        continue
                if isinstance(entity.geometry, Polygon):
                    self.add_polygon(shape=entity.geometry, **style)
                elif isinstance(entity.geometry, MultiPolygon):
                    for polygon in entity.geometry.geoms:
                        self.add_polygon(shape=polygon, **style)

                if ifc_type in IFC_ELEMENTS_PLOT_TEXT_WHITELIST:
                    self.add_text(
                        text=entity.text,
                        position=get_visual_center(entity.geometry),
                        scale_factor=scale_factor,
                    )

        return self.figure

    def add_text(self, text: str, position: Point, scale_factor: float):
        fontsize = scale_factor / 5

        self.axis.annotate(
            text,
            xycoords="data",
            xy=(position.x, position.y),
            xytext=(position.x, position.y),
            fontsize=fontsize,
            fontfamily="Courier New, monospace",
            color="black",
            va="center",
            ha="center",
            bbox=dict(boxstyle="square,pad=0.1", fc="#FFFFFF00", ec="black"),
            alpha=0.8,
        )

    def add_polygon(self, shape: Polygon, **kwargs):
        from matplotlib.patches import Polygon as PolygonPatch
        from numpy import array

        patch = PolygonPatch(array(shape.exterior.coords), **kwargs)
        self.axis.add_patch(patch)

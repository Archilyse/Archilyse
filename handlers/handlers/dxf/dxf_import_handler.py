from contextlib import redirect_stdout
from functools import cached_property
from io import BytesIO, StringIO
from math import sqrt
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, Union

import matplotlib.pyplot as plt
from ezdxf import bbox, recover, units
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import LayoutProperties
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace
from matplotlib.figure import Figure
from pygeos import Geometry, from_shapely, intersects
from shapely.affinity import scale, translate
from shapely.geometry import CAP_STYLE, JOIN_STYLE, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from brooks.constants import SuperTypes
from brooks.models import SimOpening
from common_utils.constants import DXF_IMPORT_DEFAULT_SCALE_FACTOR, LENGTH_SI_UNITS
from common_utils.exceptions import DXFImportException
from dufresne.polygon.utils import as_multipolygon
from handlers.dxf.dxf_constants import (
    AREA_IS_SHAFT_THRESHOLD_IN_M2,
    BUFFER_DOOR_WINDOW_DIFFERENCE_IN_CM,
    LAYERS_INCLUDED_IN_IMAGE,
    OPENING_DISCARDING_AREA_THRESHOLD_IN_CM_2,
    WALL_LAYERS_HATCHES,
)
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_mapper import (
    DXFClassificationInfo,
    DXFtoShapelyMapper,
)
from handlers.dxf.polylines_to_rectangles import rectangles_from_skeleton
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.schema import (
    ReactPlannerArea,
    ReactPlannerData,
    ReactPlannerHole,
    ReactPlannerLayer,
    ReactPlannerName,
)
from handlers.shapely_to_react.editor_ready_entity import EditorReadyEntity
from handlers.shapely_to_react.shapely_to_react_mapper import (
    ShapelyToReactPlannerMapper,
)


class DXFImportHandler:
    dxf_document: Drawing = None

    # --------- Image Attributes --------- #

    DPI: float = 300.0  # NOTE: This value could also be anything,
    # doesn't matter since we control the image size based on the intended scale factor
    scale_factor: float = DXF_IMPORT_DEFAULT_SCALE_FACTOR

    def __init__(
        self, dxf_file_path: Path, scale_factor: float = DXF_IMPORT_DEFAULT_SCALE_FACTOR
    ):
        self.dxf_document, auditor = recover.readfile(dxf_file_path)
        self.scale_factor = scale_factor

        if auditor.has_errors:
            raise DXFImportException(
                f"DXF Import failed due to unresolvable errors om DXF {dxf_file_path}."
            )
        self.mapper = DXFtoShapelyMapper(dxf_modelspace=self.dxf_modelspace)

    # --------- Image Properties --------- #

    @cached_property
    def pixels_per_meter(self):
        return 1 / sqrt(self.scale_factor)

    @cached_property
    def scale_pixels_to_cm(self) -> float:
        return 100 / self.pixels_per_meter

    @cached_property
    def image_size(self) -> Tuple[float, float]:
        factor = self.pixels_per_meter / self.DPI
        return factor * self.dxf_size_meters[0], factor * self.dxf_size_meters[1]

    # --------- DXF Properties --------- #

    @cached_property
    def dxf_size_meters(self) -> Tuple[float, float]:
        return (
            self.dxf_unit_to_meters(
                self.dxf_data_extents[1][0] - self.dxf_data_extents[0][0]
            ),
            self.dxf_unit_to_meters(
                self.dxf_data_extents[1][1] - self.dxf_data_extents[0][1]
            ),
        )

    @cached_property
    def dxf_data_extents(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        dxf_bbox = bbox.extents(self.dxf_document.modelspace(), cache=bbox.Cache())
        return (dxf_bbox.extmin[0], dxf_bbox.extmin[1]), (
            dxf_bbox.extmax[0],
            dxf_bbox.extmax[1],
        )

    @cached_property
    def dxf_modelspace(self) -> Modelspace:
        return self.dxf_document.modelspace()

    # --------- Export --------- #

    def export_image(
        self, output_stream: BytesIO, image_format: str = "jpeg"
    ) -> BytesIO:
        # To avoid annoying invisible items print messages from ezdxf
        self._draw_dxf_matplotlib(
            dxf_document=self.dxf_document, dpi=self.DPI, figsize=self.image_size
        ).savefig(output_stream, format=image_format, bbox_inches="tight", pad_inches=0)

        return output_stream

    # --------- DXF Drawing --------- #

    def _draw_dxf_matplotlib(
        self, dxf_document: Drawing, dpi: float, figsize: Tuple[float, float]
    ) -> Figure:
        fig = plt.figure(dpi=dpi, figsize=figsize, frameon=False)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.margins(0)
        ax.set_xlim(self.dxf_data_extents[0][0], self.dxf_data_extents[1][0])
        ax.set_ylim(self.dxf_data_extents[0][1], self.dxf_data_extents[1][1])

        self._draw_with_dxf_backend(
            dxf_document=dxf_document,
            backend=MatplotlibBackend(ax=ax, adjust_figure=False, use_text_cache=False),
        )

        return fig

    def export_react_annotation(self) -> ReactPlannerData:
        wall_polygons = self.mapper.get_wall_polygons()
        if not wall_polygons:
            raise DXFImportException(
                f"Document has no walls defined as hatches in layers {WALL_LAYERS_HATCHES}"
            )

        railing_polygons = self.mapper.get_railing_polygons()

        window_polygons = self.mapper.get_window_polygons()
        door_polygons: List[EditorReadyEntity] = self.mapper.get_door_polygons(
            wall_polygons=wall_polygons
        )
        door_entities = self._map_doors_to_pixel_coordinates(doors=door_polygons)

        bathtub_polygons = self.mapper.get_sanitary_element_polygons(
            wall_polygons=wall_polygons, react_planner_name=ReactPlannerName.BATHTUB
        )
        shower_polygons = self.mapper.get_sanitary_element_polygons(
            wall_polygons=wall_polygons, react_planner_name=ReactPlannerName.SHOWER
        )
        sink_polygons = self.mapper.get_sanitary_element_polygons(
            wall_polygons=wall_polygons, react_planner_name=ReactPlannerName.SINK
        )
        toilet_polygons = self.mapper.get_sanitary_element_polygons(
            wall_polygons=wall_polygons, react_planner_name=ReactPlannerName.TOILET
        )
        kitchen_polygons = self.mapper.get_kitchen_polygons(wall_polygons=wall_polygons)

        wall_polygons = self._remove_overlap_with_windows(
            windows_polygons=window_polygons, separator_polygons=wall_polygons
        )
        railing_polygons = self._remove_overlap_with_windows(
            windows_polygons=window_polygons, separator_polygons=railing_polygons
        )
        (elevator_polygons) = self.mapper.get_elevators_as_polygons()
        stairs_polygons = self.mapper.get_stairs_polygons(wall_polygons=wall_polygons)

        classifications = list(self.mapper.get_area_classifications())
        for classification in classifications:
            classification.position = self._dxf_geometry_to_react_geometry(
                geom=classification.position
            )

        items: Mapping[ReactPlannerName, Iterable[EditorReadyEntity]] = {}
        separators: Mapping[ReactPlannerName, Iterable[EditorReadyEntity]] = {}
        openings: Mapping[ReactPlannerName, Iterable[EditorReadyEntity]] = {
            ReactPlannerName.DOOR: door_entities
        }
        for structure, name, polygons in (
            (items, ReactPlannerName.KITCHEN, kitchen_polygons),
            (items, ReactPlannerName.BATHTUB, bathtub_polygons),
            (items, ReactPlannerName.SHOWER, shower_polygons),
            (items, ReactPlannerName.SINK, sink_polygons),
            (items, ReactPlannerName.TOILET, toilet_polygons),
            (items, ReactPlannerName.ELEVATOR, elevator_polygons),
            (items, ReactPlannerName.STAIRS, stairs_polygons),
            (separators, ReactPlannerName.RAILING, railing_polygons),
            (separators, ReactPlannerName.WALL, wall_polygons),
            (openings, ReactPlannerName.WINDOW, window_polygons),
        ):
            structure[name] = [  # type: ignore
                EditorReadyEntity(
                    geometry=self._dxf_geometry_to_react_geometry(geom=geom)
                )
                for geom in polygons
            ]

        (
            planner_vertices,
            planner_lines,
        ) = ShapelyToReactPlannerMapper.create_vertices_and_lines_of_separators(
            geometries=separators, scale_to_cm=self.scale_pixels_to_cm
        )

        layer = ReactPlannerLayer(
            vertices=planner_vertices,
            lines=planner_lines,
        )

        planner_data = ReactPlannerData(
            width=round(self.image_size[0] * self.DPI),
            height=round(self.image_size[1] * self.DPI),
            scale=self.scale_factor * units.conversion_factor(units.M, units.CM) ** 2,
            layers={"layer-1": layer},
        )

        layer.holes = self.create_holes_assigned_to_walls(
            planner_data=planner_data,
            all_opening_elements=openings,
            scale_to_cm=self.scale_pixels_to_cm,
        )
        layer.areas = ReactPlannerElementFactory.create_areas_from_separators(
            planner_data=planner_data,
            area_splitter_polygons=[],
            length_si_unit=LENGTH_SI_UNITS.CENTIMETRE,
        )
        layer.areas = self._classify_areas(
            areas=layer.areas, classifications=classifications
        )

        items[ReactPlannerName.SHAFT] = self.create_shafts_for_small_areas(  # type: ignore
            areas=[area for area in layer.areas.values()],
            pixels_per_meter=self.pixels_per_meter,
        )

        layer.items = ShapelyToReactPlannerMapper.get_planner_items(
            geometries={
                SuperTypes.SEPARATORS: separators,
                SuperTypes.ITEMS: items,
            },
            scale_to_cm=self.scale_pixels_to_cm,
        )

        return planner_data

    @classmethod
    def create_shafts_for_small_areas(
        cls, areas: List[ReactPlannerArea], pixels_per_meter: float
    ) -> List[EditorReadyEntity]:
        area_is_shaft_threshold = pixels_per_meter**2 * AREA_IS_SHAFT_THRESHOLD_IN_M2
        shafts = []
        for area in areas:
            if area.polygon.area < area_is_shaft_threshold:
                area_rectangles = sorted(
                    rectangles_from_skeleton(geometry=area.polygon),
                    key=lambda rectangle: rectangle.area,
                    reverse=True,
                )
                if not area_rectangles:
                    continue

                shaft_polygon = (
                    area_rectangles[0]
                    .buffer(distance=-pixels_per_meter * 0.01)
                    .minimum_rotated_rectangle
                )  # corresponds to -1cm

                if (
                    isinstance(shaft_polygon, Polygon)
                    and shaft_polygon.is_valid
                    and not shaft_polygon.is_empty
                    and shaft_polygon.within(area.polygon)
                ):
                    shafts.append(shaft_polygon)

        return [EditorReadyEntity(geometry=geom) for geom in shafts]

    @staticmethod
    def _draw_with_dxf_backend(dxf_document: Drawing, backend: MatplotlibBackend):
        dxf_layout = dxf_document.modelspace()

        for layer in dxf_layout.doc.layers:
            if layer.dxf.name in LAYERS_INCLUDED_IN_IMAGE:
                layer.unlock()
                layer.on()
                layer.thaw()
            else:
                layer.off()
                layer.freeze()

        layout_properties = LayoutProperties.from_layout(dxf_layout)
        layout_properties.set_colors("#FFFFFF", "#000000")

        with StringIO() as buf, redirect_stdout(buf):
            Frontend(
                ctx=RenderContext(dxf_document, export_mode=False), out=backend
            ).draw_layout(
                dxf_layout, finalize=False, layout_properties=layout_properties
            )

    # --------- Utils --------- #

    def dxf_unit_to_meters(self, value: float) -> float:
        return (
            units.conversion_factor(self.dxf_document.header["$INSUNITS"], units.M)
            * value
        )

    def dxf_unit_to_pixels(self, value: float) -> float:
        return self.dxf_unit_to_meters(value) * self.pixels_per_meter

    def _dxf_geometry_to_react_geometry(
        self, geom: Union[Point, Polygon, MultiPolygon]
    ) -> Union[Point, Polygon, MultiPolygon]:
        pixel_per_dxf_unit = self.pixels_per_meter * units.conversion_factor(
            self.dxf_document.header["$INSUNITS"], units.M
        )

        translated_geom = translate(
            geom, xoff=-self.dxf_data_extents[0][0], yoff=-self.dxf_data_extents[0][1]
        )
        return scale(
            translated_geom,
            xfact=pixel_per_dxf_unit,
            yfact=pixel_per_dxf_unit,
            origin=Point(0, 0),
        )

    def _map_doors_to_pixel_coordinates(
        self, doors: List[EditorReadyEntity]
    ) -> List[EditorReadyEntity]:
        doors_in_pixels = []
        for door in doors:
            door.geometry = self._dxf_geometry_to_react_geometry(geom=door.geometry)
            door.properties.door_sweeping_points.angle_point = self._coords_to_pixel(
                door.properties.door_sweeping_points.angle_point
            )
            door.properties.door_sweeping_points.closed_point = self._coords_to_pixel(
                door.properties.door_sweeping_points.closed_point
            )
            door.properties.door_sweeping_points.opened_point = self._coords_to_pixel(
                door.properties.door_sweeping_points.opened_point
            )
            doors_in_pixels.append(door)
        return doors_in_pixels

    def _coords_to_pixel(self, coords: List[float]) -> List[float]:
        as_point = self._dxf_geometry_to_react_geometry(geom=Point(coords))
        return [as_point.x, as_point.y]

    @staticmethod
    def _classify_areas(
        areas: Dict[str, ReactPlannerArea],
        classifications: List[DXFClassificationInfo],
    ) -> Dict[str, ReactPlannerArea]:
        for area in areas.values():
            for classification in classifications:
                if classification.position.within(area.polygon):
                    area.properties.areaType = classification.area_type.name
                    break
        return areas

    def get_georef_parameters(self):
        rotation_in_degrees = [
            entity.dxf.rotation
            for entity in self.dxf_modelspace.query("*[name=='Nordpfeil']")
        ][0]
        rotation_in_degrees = 360 - rotation_in_degrees

        return {
            "georef_scale": 1.0,
            "georef_rot_angle": rotation_in_degrees,
        }

    @staticmethod
    def _remove_overlap_with_windows(
        windows_polygons: List[Polygon], separator_polygons: List[Polygon]
    ) -> List[Polygon]:
        """
        - Some windows have non rectangular geometries leading to an overlap with walls
        - Some windows simply overlap with railings
        """
        openings_as_union = unary_union(windows_polygons)
        polygons_without_overlap = []
        for polygon in separator_polygons:
            opening_difference = polygon.difference(openings_as_union)
            if not opening_difference.is_empty:
                polygons_without_overlap.append(
                    opening_difference.minimum_rotated_rectangle
                )

        return polygons_without_overlap

    @classmethod
    def create_holes_assigned_to_walls(
        cls,
        planner_data: ReactPlannerData,
        all_opening_elements: Mapping[ReactPlannerName, Iterable[EditorReadyEntity]],
        scale_to_cm: float,
    ) -> Dict[str, ReactPlannerHole]:
        react_planner_holes: Dict[str, ReactPlannerHole] = {}
        doors = list(all_opening_elements.get(ReactPlannerName.DOOR, []))
        windows = list(all_opening_elements.get(ReactPlannerName.WINDOW, []))
        pygeos_windows_geometries = [
            from_shapely(window.geometry) for window in windows
        ]

        for door_element in doors:
            wall_geometry = door_element.geometry

            index = cls._get_overlapping_window_index(
                door=from_shapely(door_element.geometry),
                windows=pygeos_windows_geometries,
            )
            if index is not None:
                wall_geometry = cls._wall_covering_both_door_and_window(
                    door_element=door_element, window_element=windows[index]
                )
                adjusted_door_geometry = SimOpening.adjust_geometry_to_wall(
                    opening=door_element.geometry,
                    wall=wall_geometry,
                )
                door_element.geometry = adjusted_door_geometry

                new_windows_geometries = cls._remaing_window_geometries(
                    wall_geometry=wall_geometry,
                    adjusted_door_geometry=adjusted_door_geometry,
                )
                windows.extend(
                    [
                        EditorReadyEntity(geometry=geom)
                        for geom in new_windows_geometries
                    ]
                )
                pygeos_windows_geometries.extend(
                    [from_shapely(geometry=geom) for geom in new_windows_geometries]
                )

                del windows[index]
                del pygeos_windows_geometries[index]

            if hole := ShapelyToReactPlannerMapper._create_react_hole(
                planner_data=planner_data,
                editor_ready_entity=door_element,
                opening_name=ReactPlannerName.DOOR,
                scale_to_cm=scale_to_cm,
                required_underlying_wall_geometry=wall_geometry,
            ):
                react_planner_holes[hole.id] = hole

        for window in windows:
            if hole := ShapelyToReactPlannerMapper._create_react_hole(
                planner_data=planner_data,
                editor_ready_entity=window,
                opening_name=ReactPlannerName.WINDOW,
                scale_to_cm=scale_to_cm,
            ):
                react_planner_holes[hole.id] = hole

        return react_planner_holes

    @staticmethod
    def _get_overlapping_window_index(
        door: Geometry, windows: List[Geometry]
    ) -> Optional[int]:
        """
        In some dxf files transparent doors leading for example to a balcony are represented as
        a door + a window overlapping each other
        """
        intersects_index = intersects(
            a=door,
            b=windows,
        )
        for i, does_intersect in enumerate(intersects_index):
            if does_intersect:
                return i
        return None

    @staticmethod
    def _wall_covering_both_door_and_window(
        door_element: EditorReadyEntity, window_element: EditorReadyEntity
    ) -> Polygon:
        return unary_union(
            [door_element.geometry, window_element.geometry]
        ).minimum_rotated_rectangle

    @staticmethod
    def _remaing_window_geometries(
        wall_geometry: Polygon,
        adjusted_door_geometry: Polygon,
    ) -> List[Polygon]:
        return [
            geom.minimum_rotated_rectangle
            for geom in as_multipolygon(
                wall_geometry.difference(
                    adjusted_door_geometry.buffer(
                        distance=BUFFER_DOOR_WINDOW_DIFFERENCE_IN_CM,
                        join_style=JOIN_STYLE.mitre,
                        cap_style=CAP_STYLE.square,
                    )
                )
            ).geoms
            if geom.area > OPENING_DISCARDING_AREA_THRESHOLD_IN_CM_2
        ]

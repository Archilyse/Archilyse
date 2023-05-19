import copy
from functools import cached_property
from itertools import groupby
from tempfile import NamedTemporaryFile
from typing import Dict, List, Tuple

import ifcopenshell
from methodtools import lru_cache
from shapely.geometry import MultiPoint, Point, Polygon

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimLayout
from brooks.types import SeparatorType
from brooks.util.geometry_ops import remove_small_holes_and_lines
from brooks.util.projections import project_geometry
from brooks.utils import get_default_element_height, get_default_element_upper_edge
from common_utils.constants import REGION
from dufresne.polygon.utils import as_multipolygon
from handlers import FloorHandler
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    FloorDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from handlers.ifc.constants import (
    ELEMENT_IFC_TYPES,
    SURFACE_MODEL_MATRICES,
    SURFACE_MODELS,
)
from handlers.ifc.types import (
    IfcBuilding,
    IfcBuildingElement,
    IfcBuildingStorey,
    IfcProject,
    IfcRepresentationContext,
    IfcSite,
    IfcSlabStandardCase,
    IfcSpace,
    IfcSpatialZone,
)
from ifc_reader.utils import from_lat_lon_to_deg_min_sec
from simulations.basic_features import CustomValuatorBasicFeatures2
from simulations.view.meshes import GeoreferencingTransformation

from ...plan_layout_handler import PlanLayoutHandlerIDCacheMixin
from .mappers import EntityIfcMapper
from .utils import default_ifc_template


class IfcExportHandler:
    """Database & Brooks logic, agnostic to IFC internals"""

    def __init__(self, site_id: int):
        self._site_id = site_id

    def export_site(self, output_filename: str):
        ifc_site = self.add_site()
        ifc_buildings_by_id = self.add_buildings(ifc_site=ifc_site)
        ifc_floors_by_id = self.add_floors(ifc_buildings_by_id=ifc_buildings_by_id)
        ifc_units_by_id = self.add_units(ifc_floors_by_id=ifc_floors_by_id)
        ifc_areas_by_id_and_floor_id = self.add_areas(
            ifc_floors_by_id=ifc_floors_by_id, ifc_units_by_id=ifc_units_by_id
        )
        self.add_elements(
            ifc_floors_by_id=ifc_floors_by_id,
            ifc_areas_by_id_and_floor_id=ifc_areas_by_id_and_floor_id,
        )
        self.add_floor_slabs(ifc_floors_by_id=ifc_floors_by_id)
        self.add_ceiling_slabs(
            ifc_floors_by_id=ifc_floors_by_id, ifc_buildings_by_id=ifc_buildings_by_id
        )
        self.current_ifc_file.write(output_filename)

    def add_site(self) -> IfcSite:
        return EntityIfcMapper.add_site(
            ifc_file=self.current_ifc_file,
            ifc_project=self.project,
            longitude=from_lat_lon_to_deg_min_sec(value=self.site_centroid_long_lat.x),
            latitude=from_lat_lon_to_deg_min_sec(value=self.site_centroid_long_lat.y),
            client_site_id=self.site_info["client_site_id"],
            site_name=self.site_info["name"],
        )

    def add_buildings(self, ifc_site: IfcSite) -> Dict[int, IfcBuilding]:
        ifc_buildings_by_id = {
            building_info["id"]: EntityIfcMapper.add_building(
                ifc_file=self.current_ifc_file,
                ifc_site=ifc_site,
                street=building_info["street"],
                housenumber=building_info["housenumber"],
            )
            for building_info in self.building_infos
        }

        EntityIfcMapper.add_buildings_to_site(
            ifc_file=self.current_ifc_file,
            buildings=list(ifc_buildings_by_id.values()),
            site=ifc_site,
        )

        return ifc_buildings_by_id

    def add_floors(
        self, ifc_buildings_by_id: Dict[int, IfcBuilding]
    ) -> Dict[int, IfcBuildingStorey]:
        all_floors_by_id: Dict[int, IfcBuildingStorey] = {}
        for building_id, floor_infos in groupby(
            self.floor_infos, key=lambda z: z["building_id"]
        ):
            ifc_floors_by_id = {
                floor_info["id"]: EntityIfcMapper.add_floor(
                    ifc_file=self.current_ifc_file,
                    ifc_building=ifc_buildings_by_id[building_id],
                    floor_number=floor_info["floor_number"],
                    elevation=self.get_floor_altitude(floor_id=floor_info["id"]),
                )
                for floor_info in floor_infos
            }

            EntityIfcMapper.add_floors_to_building(
                ifc_file=self.current_ifc_file,
                building=ifc_buildings_by_id[building_id],
                floors=list(ifc_floors_by_id.values()),
            )

            all_floors_by_id = {**all_floors_by_id, **ifc_floors_by_id}

        return all_floors_by_id

    def add_units(
        self, ifc_floors_by_id: Dict[int, IfcBuildingStorey]
    ) -> Dict[int, IfcSpatialZone]:
        ifc_units_by_id = {
            unit_info["id"]: EntityIfcMapper.add_unit(
                ifc_file=self.current_ifc_file, client_id=unit_info["client_id"]
            )
            for unit_info in self.unit_infos
        }

        for floor_id, unit_infos in groupby(
            self.unit_infos, key=lambda z: z["floor_id"]
        ):
            EntityIfcMapper.add_units_to_floor(
                ifc_file=self.current_ifc_file,
                floor=ifc_floors_by_id[floor_id],
                units=[ifc_units_by_id[unit_info["id"]] for unit_info in unit_infos],
            )

        return ifc_units_by_id

    def add_areas(
        self,
        ifc_floors_by_id: Dict[int, IfcBuildingStorey],
        ifc_units_by_id: Dict[int, IfcSpatialZone],
    ) -> Dict[Tuple[int, int], IfcSpace]:
        areas_by_id_and_floor_id = {
            (floor_id, area.db_area_id): EntityIfcMapper.add_area(
                ifc_file=self.current_ifc_file,
                ifc_floor=ifc_floors_by_id[floor_id],
                context=self.context,
                polygon=area.footprint,
                area_type=area.type.name,
                area_number_in_floor=i,
                start_elevation_relative_to_floor=self.get_floor_slab_height(
                    floor_id=floor_id
                ),
                height=get_default_element_upper_edge(
                    element_type=SeparatorType.WALL,
                    default=layout.default_element_heights,
                ),
                floor_number=self._floor_id_to_floor_info[floor_id]["floor_number"],
                is_public=area.db_area_id in self.public_area_ids,
                building_code_type=self.area_building_code_type_by_id.get(
                    area.db_area_id
                ),
            )
            for floor_id, layout in self.floor_layouts_relative_by_floor_id.items()
            for i, area in enumerate(
                sorted(layout.areas, key=lambda x: x.footprint.area)
            )
        }

        # Add areas to floors
        for floor_id, floor_id_area_db_id in groupby(
            areas_by_id_and_floor_id.keys(), lambda z: z[0]
        ):
            EntityIfcMapper.add_areas_to_floor(
                ifc_file=self.current_ifc_file,
                floor=ifc_floors_by_id[floor_id],
                spaces=[
                    areas_by_id_and_floor_id[(floor_id, area_db_id)]
                    for (_, area_db_id) in floor_id_area_db_id
                ],
            )

        # Add areas to units
        unit_infos_by_id = {unit_info["id"]: unit_info for unit_info in self.unit_infos}
        for unit_id, unit_area_info in groupby(
            self.unit_area_infos, lambda z: z["unit_id"]
        ):
            unit_areas = [
                areas_by_id_and_floor_id[
                    (unit_infos_by_id[unit_id]["floor_id"], unit_area_info["area_id"])
                ]
                for unit_area_info in unit_area_info
            ]

            if ifc_units_by_id and unit_areas:
                EntityIfcMapper.add_areas_to_unit(
                    ifc_file=self.current_ifc_file,
                    unit=ifc_units_by_id[unit_id],
                    areas=unit_areas,
                )

        return areas_by_id_and_floor_id

    def add_elements(
        self,
        ifc_floors_by_id: Dict[int, IfcBuildingStorey],
        ifc_areas_by_id_and_floor_id: Dict[Tuple[int, int], IfcSpace],
    ):
        for floor_id, ifc_floor in ifc_floors_by_id.items():
            floor_elements = []
            floor_layout = self.floor_layouts_relative_by_floor_id[floor_id]

            # Separators
            for separator in floor_layout.non_overlapping_separators:
                ifc_separator = EntityIfcMapper.add_generic_element(
                    ifc_file=self.current_ifc_file,
                    ifc_floor=ifc_floor,
                    context=self.context,
                    polygon=separator.footprint,
                    start_elevation_relative_to_floor=self.get_floor_slab_height(
                        floor_id=floor_id
                    )
                    + separator.height[0],
                    height=separator.height[1] - separator.height[0],
                    element_type=ELEMENT_IFC_TYPES[separator.type],
                    Name=separator.type.name.capitalize(),
                )

                # Openings
                for opening in separator.openings:
                    ifc_opening, ifc_hole = EntityIfcMapper.add_door_window(
                        ifc_file=self.current_ifc_file,
                        context=self.context,
                        polygon=opening.footprint,
                        start_elevation_relative_to_floor=opening.height[0],
                        height=opening.height[1] - opening.height[0],
                        element_type=ELEMENT_IFC_TYPES[opening.type],
                        ifc_wall=ifc_separator,
                        Name=opening.type.name.capitalize(),
                    )

                    floor_elements.extend([ifc_opening])
                floor_elements.append(ifc_separator)

            # Features
            for area in floor_layout.areas:
                ifc_area = ifc_areas_by_id_and_floor_id[(floor_id, area.db_area_id)]

                area_elements = []
                for feature in area.features:
                    feature_type = feature.type
                    if feature_type not in ELEMENT_IFC_TYPES:
                        continue

                    if feature_type in SURFACE_MODELS.keys():
                        axes, scales, translation = feature.axes_scales_translation(
                            walls=[w.footprint for w in floor_layout.separators],
                            altitude=0,
                        )

                        surface_model_matrix = SURFACE_MODEL_MATRICES.get(
                            feature_type, None
                        )

                        ifc_feature = EntityIfcMapper.add_sanitary_terminal(
                            ifc_file=self.current_ifc_file,
                            ifc_floor=ifc_floor,
                            context=self.context,
                            axes=axes,
                            scales=scales,
                            translation=translation,
                            surface_model_path=SURFACE_MODELS[feature_type],
                            surface_model_matrix=surface_model_matrix,
                            ifc_element_type=ELEMENT_IFC_TYPES[feature.type],
                            Name=feature_type.name.capitalize(),
                        )
                    else:
                        ifc_feature = EntityIfcMapper.add_generic_element(
                            ifc_file=self.current_ifc_file,
                            ifc_floor=ifc_floor,
                            context=self.context,
                            polygon=feature.footprint,
                            start_elevation_relative_to_floor=self.get_floor_slab_height(
                                floor_id=floor_id
                            )
                            + feature.height[0],
                            height=feature.height[1] - feature.height[0],
                            element_type=ELEMENT_IFC_TYPES[feature.type],
                            Name=feature_type.name.capitalize(),
                        )

                    area_elements.append(ifc_feature)

                if area_elements:
                    EntityIfcMapper.add_elements_to_area(
                        ifc_file=self.current_ifc_file,
                        area=ifc_area,
                        elements=area_elements,
                    )

            if floor_elements:
                EntityIfcMapper.add_elements_to_floor(
                    ifc_file=self.current_ifc_file,
                    floor=ifc_floor,
                    elements=floor_elements,
                )

    @cached_property
    def floor_layout_by_building_id_and_floor_number(self):
        layouts = {}
        for building_id, building_floors_info in groupby(
            sorted(self.floor_infos, key=lambda z: z["building_id"]),
            key=lambda z: z["building_id"],
        ):
            floor_info_by_id = {
                floor_info["floor_number"]: floor_info
                for floor_info in building_floors_info
            }

            layouts[building_id] = {
                floor_info["floor_number"]: self.floor_layouts_relative_by_floor_id[
                    floor_info["id"]
                ]
                for floor_info in floor_info_by_id.values()
            }

        return layouts

    def add_floor_slabs(self, ifc_floors_by_id: Dict[int, IfcBuildingStorey]):
        for building_id, building_floors_info in groupby(
            sorted(self.floor_infos, key=lambda z: z["building_id"]),
            key=lambda z: z["building_id"],
        ):
            floor_info_by_id = {
                floor_info["floor_number"]: floor_info
                for floor_info in building_floors_info
            }

            layout_by_floor_number = self.floor_layout_by_building_id_and_floor_number[
                building_id
            ]

            ifc_floor_by_floor_number = {
                floor_info["floor_number"]: ifc_floors_by_id[floor_info["id"]]
                for floor_info in floor_info_by_id.values()
            }

            # Here we are adding the floors
            for floor_number in sorted(layout_by_floor_number.keys()):
                floor_id = floor_info_by_id[floor_number]["id"]
                floor_layout = layout_by_floor_number[floor_number]
                lower_floor_layout = layout_by_floor_number.get(floor_number - 1)
                slab_height = self.get_floor_slab_height(floor_id=floor_id)

                slab_type = "FLOOR" if lower_floor_layout else "BASESLAB"
                slab_name = (
                    f"Floor Slab {floor_number}" if lower_floor_layout else "Base Slab"
                )

                floor_polygon = floor_layout.footprint_ex_areas_without_floor
                if lower_floor_layout:
                    floor_polygon = floor_polygon.difference(
                        lower_floor_layout.footprint_areas_without_ceiling
                    )
                floor_polygon = remove_small_holes_and_lines(
                    geometry=floor_polygon, allow_empty=True
                )

                ifc_slabs = [
                    self._add_slab(
                        ifc_floor=ifc_floors_by_id[floor_id],
                        polygon=polygon,
                        name=slab_name,
                        predefined_type=slab_type,
                        start_elevation_relative_to_floor=0,
                        height=slab_height,
                    )
                    for polygon in as_multipolygon(floor_polygon).geoms
                    if not polygon.is_empty
                ]

                EntityIfcMapper.add_elements_to_floor(
                    ifc_file=self.current_ifc_file,
                    floor=ifc_floor_by_floor_number[floor_number],
                    elements=ifc_slabs,
                )

    def add_ceiling_slabs(
        self,
        ifc_floors_by_id: Dict[int, IfcBuildingStorey],
        ifc_buildings_by_id: Dict[int, IfcBuilding],
    ):
        for building_id, building_floors_info in groupby(
            sorted(self.floor_infos, key=lambda z: z["building_id"]),
            key=lambda z: z["building_id"],
        ):
            floor_info_by_floor_number = {
                floor_info["floor_number"]: floor_info
                for floor_info in building_floors_info
            }

            layout_by_floor_number = self.floor_layout_by_building_id_and_floor_number[
                building_id
            ]

            for floor_number in sorted(layout_by_floor_number.keys()):
                floor_id = floor_info_by_floor_number[floor_number]["id"]
                floor_layout = layout_by_floor_number[floor_number]
                upper_floor_layout = layout_by_floor_number.get(floor_number + 1)

                roof_geometries = floor_layout.footprint_ex_areas_without_ceiling
                if upper_floor_layout:
                    roof_geometries = roof_geometries.difference(
                        upper_floor_layout.footprint
                    )
                roof_geometries = remove_small_holes_and_lines(
                    geometry=roof_geometries, allow_empty=True
                )

                # Only the upmost floor is creating a roof slab actually.
                # other ceiling slabs are created as floors of the floor above
                if upper_floor_layout:
                    upper_floor_id = floor_info_by_floor_number[floor_number + 1]["id"]
                    slab_type = "FLOOR"
                    slab_name = f"Floor Slab {floor_number + 1}"
                    slab_height = self.get_floor_slab_height(floor_id=upper_floor_id)
                else:
                    slab_type = "ROOF"
                    slab_name = "Roof Slab"
                    slab_height = self.get_ceiling_slab_height(floor_id=floor_id)

                ifc_slabs = [
                    self._add_slab(
                        ifc_floor=ifc_floors_by_id[floor_id],
                        polygon=polygon,
                        name=slab_name,
                        predefined_type=slab_type,
                        start_elevation_relative_to_floor=get_default_element_height(
                            element_type=SeparatorType.WALL,
                            default=floor_layout.default_element_heights,
                        )
                        + self.get_floor_slab_height(floor_id=floor_id),
                        height=slab_height,
                    )
                    for polygon in as_multipolygon(roof_geometries).geoms
                    if not polygon.is_empty
                ]

                # The roof is added to the building while the generated slabs
                # of type FLOOR are added to the floor above
                if upper_floor_layout:
                    upper_floor_id = floor_info_by_floor_number[floor_number + 1]["id"]
                    EntityIfcMapper.add_elements_to_floor(
                        ifc_file=self.current_ifc_file,
                        floor=ifc_floors_by_id[upper_floor_id],
                        elements=ifc_slabs,
                    )
                else:
                    EntityIfcMapper.add_elements_to_building(
                        ifc_file=self.current_ifc_file,
                        building=ifc_buildings_by_id[building_id],
                        elements=ifc_slabs,
                    )

    def _add_slab(
        self,
        polygon: Polygon,
        ifc_floor: IfcBuildingStorey,
        name: str,
        predefined_type: str,
        height: float,
        start_elevation_relative_to_floor: float,
    ) -> IfcBuildingElement:
        return EntityIfcMapper.add_generic_element(
            ifc_file=self.current_ifc_file,
            ifc_floor=ifc_floor,
            context=self.context,
            polygon=polygon,
            start_elevation_relative_to_floor=start_elevation_relative_to_floor,
            height=height,
            element_type=IfcSlabStandardCase,
            Name=name,
            PredefinedType=predefined_type,
        )

    # Util

    @cached_property
    def current_ifc_file(self) -> ifcopenshell.file:
        # Write the template to a temporary file
        with NamedTemporaryFile(suffix=".ifc") as temp_file:
            with open(temp_file.name, "wb") as fh:
                fh.write(
                    str.encode(
                        default_ifc_template(project_name=f"Site {self._site_id}")
                    )
                )
            # Obtain references to instances defined in template
            return ifcopenshell.open(temp_file.name)

    @cached_property
    def project(self) -> IfcProject:
        return self.current_ifc_file.by_type("IfcProject")[0]

    @cached_property
    def context(self) -> IfcRepresentationContext:
        return self.current_ifc_file.by_type("IfcGeometricRepresentationContext")[0]

    # DB
    @cached_property
    def site_info(self) -> Dict:
        return SiteDBHandler.get_by(
            id=self._site_id,
            output_columns=["georef_region", "name", "client_site_id"],
        )

    @cached_property
    def building_infos(self) -> List[Dict]:
        return list(
            BuildingDBHandler.find(
                site_id=self._site_id, output_columns=["id", "street", "housenumber"]
            )
        )

    @cached_property
    def floor_infos(self) -> List[Dict]:
        return [
            floor_info
            for floor_info in FloorDBHandler.find_in(
                building_id=[
                    building_info["id"] for building_info in self.building_infos
                ],
                output_columns=["id", "building_id", "floor_number", "plan_id"],
            )
        ]

    @cached_property
    def _floor_id_to_floor_info(self) -> Dict[int, Dict]:
        return {floor_info["id"]: floor_info for floor_info in self.floor_infos}

    @cached_property
    def area_infos(self) -> List[Dict]:
        return list(
            AreaDBHandler.find_in(
                plan_id=[floor_info["plan_id"] for floor_info in self.floor_infos],
                output_columns=["id", "plan_id", "area_type"],
            )
        )

    @cached_property
    def area_building_code_type_by_id(self) -> Dict[int, str]:
        basic_features = CustomValuatorBasicFeatures2()
        classification_scheme = UnifiedClassificationScheme()

        area_db_id_to_sia416_area_type: Dict[int, str] = {}
        for sia_category, areas in basic_features.get_areas_by_area_type_groups(
            layouts=self.floor_layouts_relative_by_floor_id.values(),
            groups={
                sia_category.name: set(
                    classification_scheme.get_children(parent_type=sia_category),
                )
                for sia_category in classification_scheme.SIA_CATEGORIES
            },
        ).items():
            for area in areas:
                area_db_id_to_sia416_area_type[area.db_area_id] = sia_category

        return area_db_id_to_sia416_area_type

    @cached_property
    def public_area_ids(self):
        assigned_area_ids = {
            unit_area_info["area_id"] for unit_area_info in self.unit_area_infos
        }
        return {
            area_info["id"]
            for area_info in self.area_infos
            if area_info["id"] not in assigned_area_ids
        }

    @cached_property
    def unit_area_infos(self) -> List[Dict]:
        return list(
            UnitAreaDBHandler.find_in(
                unit_id=[unit_info["id"] for unit_info in self.unit_infos],
                output_columns=["unit_id", "area_id"],
            )
        )

    @cached_property
    def unit_infos(self) -> List[Dict]:
        return list(
            UnitDBHandler.find(
                site_id=self._site_id,
                output_columns=["id", "client_id", "floor_id"],
            )
        )

    # Layouts

    @cached_property
    def site_centroid_long_lat(self) -> Point:
        return project_geometry(
            geometry=self._site_centroid,
            crs_from=REGION[self.site_info["georef_region"]],
            crs_to=REGION.LAT_LON,
        )

    @cached_property
    def floor_layouts_relative_by_floor_id(self) -> Dict[int, SimLayout]:
        georeferencing_transformation = GeoreferencingTransformation()
        georeferencing_transformation.set_translation(
            x=-self._site_centroid.x, y=-self._site_centroid.y, z=0
        )

        layouts = {
            floor_id: layout.apply_georef_transformation(
                georeferencing_transformation=georeferencing_transformation
            )
            for floor_id, layout in self._floor_layouts_by_floor_id.items()
        }

        return layouts

    @lru_cache()
    def get_floor_altitude(self, floor_id: int) -> float:
        return FloorHandler.get_level_baseline(
            floor_id=floor_id
        ) - self.get_floor_slab_height(floor_id=floor_id)

    @lru_cache()
    def get_floor_slab_height(self, floor_id: int) -> float:
        floor_info = self._floor_id_to_floor_info[floor_id]
        building_id, floor_number = (
            floor_info["building_id"],
            floor_info["floor_number"],
        )

        floor_layout = self.floor_layout_by_building_id_and_floor_number[building_id][
            floor_number
        ]
        lower_floor_layout = self.floor_layout_by_building_id_and_floor_number[
            building_id
        ].get(floor_number - 1)

        if lower_floor_layout is None:
            return get_default_element_height(
                "FLOOR_SLAB", default=floor_layout.default_element_heights
            )

        return get_default_element_height(
            "CEILING_SLAB", default=lower_floor_layout.default_element_heights
        )

    @lru_cache()
    def get_ceiling_slab_height(self, floor_id: int) -> float:
        floor_info = self._floor_id_to_floor_info[floor_id]
        building_id, floor_number = (
            floor_info["building_id"],
            floor_info["floor_number"],
        )

        floor_layout = self.floor_layout_by_building_id_and_floor_number[building_id][
            floor_number
        ]
        return get_default_element_height(
            "CEILING_SLAB", default=floor_layout.default_element_heights
        )

    # Util

    @cached_property
    def _floor_layouts_by_floor_id(self) -> Dict[int, SimLayout]:
        plan_cache = PlanLayoutHandlerIDCacheMixin()

        return {
            floor_info["id"]: copy.deepcopy(
                plan_cache.layout_handler_by_id(
                    plan_id=floor_info["plan_id"]
                ).get_layout(
                    scaled=True,
                    georeferenced=True,
                    classified=True,
                    postprocessed=False,
                )
            )
            for floor_info in self.floor_infos
        }

    @cached_property
    def _site_centroid(self) -> Point:
        return MultiPoint(
            [
                layout.footprint.centroid
                for layout in self._floor_layouts_by_floor_id.values()
            ]
        ).centroid

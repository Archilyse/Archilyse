from collections import defaultdict
from functools import cached_property
from operator import attrgetter
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

import numpy as np
from ifcopenshell import entity_instance
from ifcopenshell import open as ifc_open
from methodtools import lru_cache
from shapely.geometry import Point

from common_utils.constants import LENGTH_SI_UNITS
from common_utils.exceptions import InvalidShapeException
from common_utils.logger import logger
from ifc_reader.constants import (
    IFC_DEF_LENGTHUNIT,
    IFC_GEOMETRIC_REPR_CONTEXT,
    IFC_RAILING,
    IFC_SITE,
    IFC_SPACE,
    IFC_STAIR,
    IFC_STOREY,
    IFC_TRANSPORT_ELEMENT,
    IFC_UNIT,
)
from ifc_reader.exceptions import (
    IfcGeoreferencingException,
    IfcMapperException,
    IfcReaderException,
    IfcUncoveredGeometricalRepresentation,
    IfcValidationException,
)
from ifc_reader.ifc_mapper import IfcToSpatialEntityMapper
from ifc_reader.utils import from_deg_min_sec_to_degrees

from .types import Ifc2DEntity, IfcSpaceProcessed


class IfcReader:
    """
    Generates an entity containing geometry data describing the loaded IFC file, which
    can be used for further processing, such as conversion to a Brooks model.
    """

    _M_TO_CM_MULTIPLIER = 100

    def __init__(self, filepath: Path):
        self.filepath = filepath

    @property
    def site(self):
        return self.wrapper.by_type(IFC_SITE)[0]

    @cached_property
    def ifc_mapper(self):
        return IfcToSpatialEntityMapper(reader=self)

    @cached_property
    def wrapper(self):
        try:
            wrapper = ifc_open(self.filepath.as_posix())
            for storey in wrapper.by_type(IFC_STOREY):
                if storey.Elevation is None:
                    raise IfcReaderException(
                        f"Storey with id {storey.id} has no elevation"
                    )
            site = wrapper.by_type(IFC_SITE)[0]
            if site.RefLatitude is None or site.RefLongitude is None:
                raise IfcReaderException("Site is not georeferenced")

        except IOError:
            raise IfcReaderException(f"Could not load the IFC file {self.filepath}")

        return wrapper

    def get_items_of_type(self, ifc_type: str):
        return self.wrapper.by_type(ifc_type)

    @property
    def georef_rotation(self) -> Tuple[Point, float]:
        if geometric_representation_context := self.wrapper.by_type(
            IFC_GEOMETRIC_REPR_CONTEXT
        ):
            # one instance of IfcGeometricRepresentationContext to represent the model (3D) view is mandatory
            model_context = [
                c
                for c in geometric_representation_context
                if c.ContextType == "Model" and c.WorldCoordinateSystem is not None
            ][0]

            # WorldCoordinateSystem provides unit vector data, i.e. x(1.,0.,0.), y(0.,1.,0.), z(0.,0.,1.) which is
            # then used to define directions of x, y, z axes.
            if wcs := model_context.WorldCoordinateSystem:
                try:
                    origin_x, origin_y, _ = wcs[0][0]
                    origin_point = Point(origin_x, origin_y)
                except IndexError:
                    origin_point = Point(0.0, 0.0)
                for dimension_orientation in list(wcs)[1:]:
                    x, y, _ = dimension_orientation[0]
                    if all(dimension != 0.0 for dimension in [x, y]):
                        return origin_point, float(np.degrees(np.arctan(x / y)))

                # TrueNorth attribute must be provided, if the y axis of the WorldCoordinateSystem does not point to the
                # global north or if WorldCoordinateSystem attribute is None.
                x, y, *_ = model_context.TrueNorth[0]
                return origin_point, float(np.degrees(np.arctan(x / y)))
            raise IfcGeoreferencingException(
                "No georeferencing data provided in the IFC model."
            )

    @property
    def reference_point(self) -> Point:
        longitude_time = iter(self.site.RefLongitude)
        latitude_time = iter(self.site.RefLatitude)
        try:
            longitude_degree = from_deg_min_sec_to_degrees(
                degrees=next(longitude_time),
                min=next(longitude_time),
                sec=next(longitude_time),
                micro_sec=next(longitude_time, 0),
            )
            latitute_degree = from_deg_min_sec_to_degrees(
                degrees=next(latitude_time),
                min=next(latitude_time),
                sec=next(latitude_time),
                micro_sec=next(latitude_time, 0),
            )
            return Point(longitude_degree, latitute_degree)
        except StopIteration:
            logger.error(
                f"File {self.filepath.name} should have at minimum hour, minute and second DMS data in RefLongitude and"
                f" RefLatitude."
            )
            raise IfcValidationException("Incomplete georeferencing data")

    @property
    def length_si_unit(self) -> float:
        """
        Retrieves the SI unit of measuring length.
        """
        for si_unit in self.wrapper.by_type(IFC_UNIT):
            if si_unit.UnitType == IFC_DEF_LENGTHUNIT:
                if unit_name := si_unit.Name:
                    if unit_prefix := si_unit.Prefix:
                        unit_name = unit_prefix + unit_name
                    try:
                        return LENGTH_SI_UNITS[unit_name].value
                    except ValueError:
                        raise IfcValidationException(
                            f"IFC file contains an unsupported SI unit {unit_name}"
                        )
        raise IfcValidationException(
            "IFC file does not contain a valid SI length unit."
        )

    @staticmethod
    def get_relating_type_info(relating_type) -> Dict:
        relating_type_info = {}
        if hasattr(relating_type, "Name"):
            relating_type_info["Name"] = relating_type.Name
        if hasattr(relating_type, "OperationType"):
            relating_type_info["OperationType"] = relating_type.OperationType

            for properties in getattr(relating_type, "HasPropertySets", []) or []:
                sub_properties: Dict[
                    str, Union[str, int, float, entity_instance]
                ] = properties.get_info()
                filtered_properties = {
                    k: v
                    for (k, v) in sub_properties.items()
                    if not isinstance(v, entity_instance)
                    and k not in ("id", "GlobalId")
                }
                relating_type_info[
                    filtered_properties.pop("type")
                ] = filtered_properties

        return relating_type_info

    @staticmethod
    def get_quantities(property_definition) -> Dict:
        quantities = {}
        for quantity in property_definition.Quantities:
            name = f"{property_definition.Name.strip().rstrip()}_{quantity.Name.strip().rstrip()}"
            if "IfcQuantityArea" == quantity.is_a():
                quantities[name] = quantity.AreaValue
            if "IfcQuantityVolume" == quantity.is_a():
                quantities[name] = quantity.VolumeValue
            if "IfcQuantityLength" == quantity.is_a():
                quantities[name] = quantity.LengthValue
        return quantities

    @staticmethod
    def get_properties(property_definition) -> Dict:
        properties = {}
        for ifc_property in property_definition.HasProperties:
            if hasattr(ifc_property, "NominalValue"):
                value = ifc_property.NominalValue.wrappedValue
            elif hasattr(ifc_property, "EnumerationValues"):
                value = ifc_property.EnumerationValues[0].wrappedValue
            else:
                value = f"Could not convert, options: {ifc_property.__dict__}"

            properties[
                f"{property_definition.Name.strip().rstrip()}_{ifc_property.Name.strip().rstrip()}"
            ] = value
        return properties

    @classmethod
    def get_all_properties(cls, ifc_element: entity_instance) -> Dict:
        properties = {
            "quantities": {},
            "properties": {"name": ifc_element.Name},
            "related": {},
        }
        for definition in getattr(ifc_element, "IsDefinedBy", []) or []:
            if hasattr(definition, "RelatingPropertyDefinition"):
                property_definition = definition.RelatingPropertyDefinition
                if "IfcElementQuantity" == property_definition.is_a():
                    properties["quantities"].update(
                        cls.get_quantities(property_definition=property_definition)
                    )
                else:
                    properties["properties"].update(
                        cls.get_properties(property_definition=property_definition)
                    )
            elif hasattr(definition, "RelatingType"):
                properties["related"].update(
                    cls.get_relating_type_info(relating_type=definition.RelatingType)
                )

        return properties

    @cached_property
    def get_space_geometry_and_properties_by_storey_id(
        self,
    ) -> Dict[int, List[IfcSpaceProcessed]]:
        from handlers.ifc.importer.ifc_reader_space_classifiers import (
            get_area_type_for_ifc_space,
        )

        space_properties_by_storey_id = defaultdict(list)
        for ifc_space in self.wrapper.by_type(IFC_SPACE):
            # To understand the hierarchy traversed to find the floor id:
            # https://standards.buildingsmart.org/IFC/RELEASE/IFC4_1/FINAL/HTML/figures/ifcspace-spatialstructure.png
            properties = self.get_all_properties(ifc_element=ifc_space)
            # Looks like something cumbersome Steiner uses to define the apartments
            if properties["properties"].get("PSet_BiG_Element") in {"NUE", "GFL"}:
                continue

            storey_id = ifc_space.ObjectPlacement.PlacementRelTo.PlacesObject[0].id()
            ifc_2d_entity = self.get_ifc_2d_entity_if_valid(ifc_element=ifc_space)
            if not ifc_2d_entity:
                continue

            space_properties_by_storey_id[storey_id].append(
                IfcSpaceProcessed(
                    properties=properties["properties"],
                    quantities=properties["quantities"],
                    related=properties["related"],
                    area_type=get_area_type_for_ifc_space(
                        ifc_space=ifc_space, space_properties=properties["properties"]
                    ),
                    geometry=ifc_2d_entity.geometry,
                )
            )
        return space_properties_by_storey_id

    def get_valid_storeys(self) -> List:
        return [
            storey
            for storey in self.wrapper.by_type(IFC_STOREY)
            if isinstance(storey.ContainsElements, Tuple)
            and len(storey.ContainsElements)
        ]

    @property
    def storeys_by_building(self) -> Dict[str, List[int]]:
        building_storeys_index = defaultdict(list)
        for storey in self.get_valid_storeys():
            building_storeys_index[storey.Decomposes[0].RelatingObject.GlobalId].append(
                storey.id()
            )
        return building_storeys_index

    @property
    def storey_floor_numbers(self) -> Dict[int, int]:
        storey_floor_number_index = {}
        for storey_ids in self.storeys_by_building.values():
            storey_sorted_by_elevation = sorted(
                [self.wrapper.by_id(storey_id) for storey_id in storey_ids],
                key=attrgetter("Elevation"),
            )
            starting_storey_number = -len(
                [
                    storey
                    for storey in storey_sorted_by_elevation
                    if storey.Elevation < 0.0
                ]
            )
            for i, storey in enumerate(storey_sorted_by_elevation):
                storey_floor_number_index[storey.id()] = i + starting_storey_number
        return storey_floor_number_index

    @classmethod
    def _children_recursive(cls, parent):
        if not isinstance(parent, entity_instance):
            return []

        children = []
        if hasattr(parent, "ContainsElements"):
            for relation in parent.ContainsElements:
                for child in relation.RelatedElements:
                    children += cls._children_recursive(child)

        if hasattr(parent, "IsDecomposedBy"):
            for relation in parent.IsDecomposedBy:
                for child in relation.RelatedObjects:
                    children += cls._children_recursive(child)

        return [parent, *children]

    def storey_elements(
        self, storey_id: int, element_types: Optional[Iterable[str]] = None
    ) -> Iterator:
        storey = self.wrapper.by_id(storey_id)
        for element in self._children_recursive(storey):
            if (element_types and element.is_a() not in element_types) or getattr(
                element, "LongName", ""
            ) == "Galerie":
                # it is not possible to extract the geometry for galleries
                continue
            yield element

    @lru_cache()
    def element_ids_in_floor(self, storey_id: int) -> Set[int]:
        return {element.id() for element in self.storey_elements(storey_id=storey_id)}

    @classmethod
    def get_address_info(cls, ifc_building, ifc_filename: str) -> Dict:
        address = dict(
            city="N/A",
            street="N/A",
            zipcode="N/A",
            housenumber=ifc_building.GlobalId,
            client_building_id=ifc_filename,
        )
        if building_address := ifc_building.BuildingAddress:
            if city := building_address.Town:
                address["city"] = city
            if street := building_address.AddressLines:
                address["street"] = " ".join(street)
            if zipcode := building_address.PostalCode:
                address["zipcode"] = zipcode
        return address

    @staticmethod
    def get_decomposed_elements(element) -> Iterator:
        """
        Some ifc elements are a group of subelements e.g. Stairs which are a combination of slabs and stair flights.
        This method is returning all subelements of an element with the exception of railings that compose IfcStairs
        elements, since they falsify their 2D footprint.
        """
        for aggregation in element.IsDecomposedBy:
            for related_object in aggregation.RelatedObjects:
                if element.is_a() == IFC_STAIR and related_object.is_a() == IFC_RAILING:
                    continue
                yield related_object

    def get_elevators(self) -> List:
        return [
            element
            for element in self.get_items_of_type(IFC_TRANSPORT_ELEMENT)
            if getattr(element, "OperationType", "") == "ELEVATOR"
        ]

    def ifc_2d_sub_entities_from_element(self, element) -> Iterator[Ifc2DEntity]:
        if element.IsDecomposedBy:
            ifc_elements = (
                sub_element for sub_element in self.get_decomposed_elements(element)
            )
        else:
            ifc_elements = [element]

        for sub_element in ifc_elements:
            if ifc_2d_entity := self.get_ifc_2d_entity_if_valid(
                ifc_element=sub_element
            ):
                yield ifc_2d_entity
            else:
                logger.debug(
                    f"Error reading a geometry from IFC file {self.filepath}: {sub_element}"
                )

    def get_ifc_2d_entity_if_valid(self, ifc_element) -> Union[Ifc2DEntity, bool]:
        try:
            return self.ifc_mapper.get_ifc_2d_entity(ifc_element=ifc_element)
        except (
            IfcUncoveredGeometricalRepresentation,
            IfcMapperException,
            InvalidShapeException,
        ):
            return False

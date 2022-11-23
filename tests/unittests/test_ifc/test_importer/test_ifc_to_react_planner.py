from collections import Counter
from typing import Dict
from unittest.mock import ANY

import pytest
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from brooks.constants import SuperTypes
from brooks.types import AreaType
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerHole,
    ReactPlannerItem,
    ReactPlannerLine,
    ReactPlannerName,
    ReactPlannerVertex,
)
from handlers.ifc.importer.ifc_react_mappings import (
    get_ifc_entity_supertype_and_planner_type,
    get_ifc_item_planner_type_based_on_keywords,
)
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from handlers.ifc.importer.ifc_to_react_planner_mapper import IfcToReactPlannerMapper
from handlers.shapely_to_react.shapely_to_react_mapper import (
    ShapelyToReactPlannerMapper,
)
from ifc_reader.constants import (
    IFC_DISTRIBUTION_FLOW_ELEMENT,
    IFC_FLOW_CONTROLLER,
    IFC_FURNISHING_ELEMENT,
    IFC_FURNITURE,
    IFC_SPACE,
    IFC_STAIR,
)
from ifc_reader.types import Ifc2DEntity


class TestIfcToReactPlannerMapper:
    @staticmethod
    @pytest.mark.parametrize(
        "ifc_reader, storey_id, expected_line_number, expected_vertex_number, expected_area_types, "
        "expected_item_number, expected_opening_number, expected_area_size",
        [
            (
                pytest.lazy_fixture("ac20_fzk_haus_ifc_reader"),
                479,
                15,
                90,
                6,
                1,
                14,
                101.268,
            ),
            (
                pytest.lazy_fixture("ac20_fzk_haus_ifc_reader"),
                35065,
                6,
                36,
                1,
                0,
                2,
                106.602,
            ),
            (
                pytest.lazy_fixture("ifc_file_reader_steiner_example"),
                128054,
                190,
                1140,
                54,
                0,
                76,
                611.91,
            ),
        ],
    )
    def test_get_react_planner_data_from_ifc_storey(
        ifc_reader,
        storey_id,
        expected_line_number,
        expected_vertex_number,
        expected_area_types,
        expected_item_number,
        expected_opening_number,
        expected_area_size,
    ):

        react_planner: ReactPlannerData = IfcToReactPlannerMapper(
            ifc_storey_handler=IfcStoreyHandler(ifc_reader=ifc_reader)
        ).get_react_planner_data_from_ifc_storey(
            storey_id=storey_id,
        )

        vertices: Dict[str, ReactPlannerVertex] = react_planner.layers[
            "layer-1"
        ].vertices
        lines: Dict[str, ReactPlannerLine] = react_planner.layers["layer-1"].lines
        holes: Dict[str, ReactPlannerHole] = react_planner.layers["layer-1"].holes
        items: Dict[str, ReactPlannerItem] = react_planner.layers["layer-1"].items

        assert len(lines) == expected_line_number
        assert len(vertices) == expected_vertex_number
        assert len(items) == expected_item_number
        assert len(holes) == expected_opening_number

        # vertices should contain wall ids and vice versa
        assert all(
            [line_id in lines.keys() for v in vertices.values() for line_id in v.lines]
        )

        # lines should contain hole ids and vice versa
        assert all(
            [
                vertex_id in vertices.keys()
                for line in lines.values()
                for vertex_id in line.vertices
            ]
        )

        # all wall widths should be rounded
        assert all(
            [
                wall.properties.width.value - round(wall.properties.width.value) == 0
                for wall in lines.values()
                if wall.name != ReactPlannerName.AREA_SPLITTER.value
            ]
        )

        for line in lines.values():
            assert line.coordinates

        for hole in holes.values():
            assert hole.coordinates

        assert all(
            [
                hole_id in holes.keys() and holes[hole_id] is not None
                for line in lines.values()
                for hole_id in line.holes
            ]
        )

        assert all([item_id == item.id for item_id, item in items.items()])

        plan_layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=react_planner,
            scaled=True,
        )
        all_areas_wo_overlap = unary_union(
            [area.footprint for area in plan_layout.areas]
        )
        assert all_areas_wo_overlap.area == pytest.approx(
            expected_area_size, abs=10**-3
        )
        assert len(plan_layout.areas) == expected_area_types

    @staticmethod
    def test_get_react_planner_data_from_ifc_storey_should_translate_origin_point(
        mocker, ac20_fzk_haus_ifc_reader
    ):
        # if there are IFC geometries which minx, miny is not equal (0, 0), then they need to be translated to that
        # point, so that there's common origin to guarantee correct placement over the floorplan image
        mocker.patch.object(
            IfcStoreyHandler, "storey_footprint", return_value=box(5, 5, 10, 10)
        )

        from handlers.ifc.importer import ifc_to_react_planner_mapper

        translate_spy = mocker.spy(ifc_to_react_planner_mapper, "translate")
        IfcToReactPlannerMapper(
            ifc_storey_handler=IfcStoreyHandler(ifc_reader=ac20_fzk_haus_ifc_reader)
        ).get_react_planner_data_from_ifc_storey(
            storey_id=479,
        )

        wall_count = 9
        opening_count = 14
        feature_count = 1
        space_count = 6
        assert (
            translate_spy.call_count
            == wall_count + opening_count + feature_count + space_count
        )
        translate_spy.assert_called_with(geom=ANY, xoff=-5.0, yoff=-5.0)

    @pytest.fixture
    def implenia_item_properties(self):
        return {
            "Pset_ManufacturerOccurrence_SerialNumber": "",
            "Pset_ManufacturerTypeInformation_Manufacturer": "",
            "Pset_ManufacturerTypeInformation_ProductionYear": "",
            "FABRICACIÓN_Sitio Web del Producto": "www.graphisoft.com",
            "DESCRIPCIÓN DEL PRODUCTO (Expresión)_ID Dinámico por Clasificación": "Elemento de Flujo de Distribución - 003",
            "DESCRIPCIÓN DEL PRODUCTO (Expresión)_ID de Clasificación": "Elemento",
            "DESCRIPCIÓN DEL PRODUCTO (Expresión)_Nombre de Clasificación": "de Flujo de Distribución",
            "AC_Pset_RenovationAndPhasing_Renovation Status": "New",
        }

    @staticmethod
    @pytest.mark.parametrize(
        "related_type, ifc_type, expected_planner_name",
        [
            (
                "Bañera 25",
                IFC_DISTRIBUTION_FLOW_ELEMENT,
                ReactPlannerName.BATHTUB,
            ),
            ("WC 25", IFC_DISTRIBUTION_FLOW_ELEMENT, ReactPlannerName.TOILET),
            (
                "Lavabo Doble 25",
                IFC_DISTRIBUTION_FLOW_ELEMENT,
                ReactPlannerName.SINK,
            ),
            ("Lavabo 25", IFC_DISTRIBUTION_FLOW_ELEMENT, ReactPlannerName.SINK),
            (
                "Plato Ducha Rect 25",
                IFC_DISTRIBUTION_FLOW_ELEMENT,
                ReactPlannerName.SHOWER,
            ),
            (
                "Plato Ducha Rect 25",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.SHOWER,
            ),
            (
                "Plato Ducha Della Tua Madre",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.SHOWER,
            ),
            (
                "Plato Ducha Rect 25",
                IFC_DISTRIBUTION_FLOW_ELEMENT,
                ReactPlannerName.SHOWER,
            ),
            (
                "Montaje Cocina 25",
                IFC_FURNISHING_ELEMENT,
                ReactPlannerName.KITCHEN,
            ),
            (
                "urinal",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.TOILET,
            ),
            (
                "wc",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.TOILET,
            ),
            (
                "basin",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.SINK,
            ),
            (
                "bathtub",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.BATHTUB,
            ),
            (
                "shower",
                IFC_FLOW_CONTROLLER,
                ReactPlannerName.SHOWER,
            ),
        ],
    )
    def test_match_keywords_implenia_file_properties(
        implenia_item_properties,
        related_type,
        ifc_type,
        expected_planner_name,
    ):
        implenia_item_properties["Name"] = related_type
        assert expected_planner_name == get_ifc_item_planner_type_based_on_keywords(
            ifc_entity=Ifc2DEntity(
                properties=implenia_item_properties,
                geometry=Polygon(),
                ifc_type=ifc_type,
            ),
        ), implenia_item_properties["Name"]

    @staticmethod
    @pytest.mark.parametrize(
        "raumtyp, expected_area_type",
        [
            ({"RG-DWB_Raumtyp": "BWC"}, AreaType.BATHROOM),
            ({"RG-DWB_Raumtyp": "BLK"}, AreaType.LOGGIA),
            ({"RG-DWB_Raumtyp": "(.)"}, AreaType.NOT_DEFINED),
            ({"entero somewhere elso": "ok"}, AreaType.NOT_DEFINED),
        ],
    )
    def test_get_spaces_classified(mocker, raumtyp, expected_area_type):
        origin = Point(0, 0)
        multiplier = 1
        from handlers.ifc.importer import ifc_to_react_planner_mapper

        translate_spy = mocker.spy(ifc_to_react_planner_mapper, "translate")
        scale_spy = mocker.spy(ifc_to_react_planner_mapper, "scale")
        get_space_classification_spy = mocker.spy(
            IfcToReactPlannerMapper,
            "get_area_type_from_space_classification",
        )
        space_geometry = box(0, 0, 1, 1)
        storey_handler = mocker.Mock()
        ifc_entity = Ifc2DEntity(geometry=space_geometry, properties=raumtyp)
        storey_handler.get_storey_entities_by_ifc_type.return_value = {
            IFC_SPACE: [ifc_entity]
        }
        spaces_classified = IfcToReactPlannerMapper(
            ifc_storey_handler=storey_handler
        ).adapt_spaces_geometries_to_new_editor(
            storey_id=123,
            origin=origin,
            multiplier=multiplier,
        )
        assert len(spaces_classified) == 1
        geometry, classification = spaces_classified[0]
        assert classification == expected_area_type
        translate_spy.assert_called_once_with(
            geom=space_geometry, xoff=-origin.x, yoff=-origin.y
        )
        translated_geom = translate_spy.spy_return
        scale_spy.assert_called_once_with(
            geom=translated_geom,
            xfact=multiplier,
            yfact=multiplier,
            origin=Point(0, 0),  # not the same as origin!
        )
        get_space_classification_spy.assert_called_once_with(ifc_space=ifc_entity)

    @staticmethod
    def test_get_vertices_and_lines_different_separators(
        ifc_file_reader_steiner_example,
    ):
        from ifc_reader.constants import IFC_STOREY

        storey = ifc_file_reader_steiner_example.wrapper.by_type(IFC_STOREY)[1]
        from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
        from handlers.ifc.importer.ifc_to_react_planner_mapper import (
            IfcToReactPlannerMapper,
        )

        geometries = IfcToReactPlannerMapper(
            ifc_storey_handler=IfcStoreyHandler(
                ifc_reader=ifc_file_reader_steiner_example
            )
        )._geometries_n_metadata_for_react_planner(
            origin=Point(0, 0),
            storey_id=storey.id(),
        )

        (
            planner_vertices,
            planner_lines,
        ) = ShapelyToReactPlannerMapper.create_vertices_and_lines_of_separators(
            geometries=geometries[SuperTypes.SEPARATORS], scale_to_cm=1
        )

        assert Counter([x.name for x in planner_lines.values()]) == {
            ReactPlannerName.WALL.value: 89,
            ReactPlannerName.COLUMN.value: 6,
        }

    @staticmethod
    @pytest.mark.parametrize(
        "related_type, expected",
        [
            ({"OperationType": None}, None),
            ({"OperationType": "SLIDING"}, ReactPlannerName.SLIDING_DOOR),
        ],
    )
    def test_get_editor_ready_entity_door_subtype(mocker, related_type, expected):
        mocker.patch.object(
            IfcToReactPlannerMapper,
            "_translate_rectangle_from_ifc_entity",
            return_value=Polygon(),
        )
        ready_entity = IfcToReactPlannerMapper._get_editor_ready_entity(
            origin=Point(0, 0),
            ifc_entity=Ifc2DEntity(geometry=Polygon(), related=related_type),
        )
        assert ready_entity.properties.door_subtype == expected


@pytest.mark.parametrize(
    "related_type, ifc_type, expected_super_type, expected_planner_name",
    [
        ("", IFC_STAIR, SuperTypes.ITEMS, ReactPlannerName.STAIRS),
        ("", IFC_FURNISHING_ELEMENT, SuperTypes.ITEMS, ReactPlannerName.KITCHEN),
        ("", IFC_FURNITURE, SuperTypes.ITEMS, ReactPlannerName.KITCHEN),
        ("cocina", IFC_FURNITURE, SuperTypes.ITEMS, ReactPlannerName.KITCHEN),
        ("cocina", IFC_FLOW_CONTROLLER, None, None),
    ],
)
def test_get_ifc_entity_supertype_and_planner_type(
    related_type, ifc_type, expected_planner_name, expected_super_type
):
    assert (
        expected_super_type,
        expected_planner_name,
    ) == get_ifc_entity_supertype_and_planner_type(
        ifc_entity=Ifc2DEntity(
            related={"name": related_type},
            geometry=Polygon(),
            ifc_type=ifc_type,
        ),
    )

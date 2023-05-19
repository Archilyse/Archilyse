import pytest

from handlers.ifc.types import (
    IfcBuilding,
    IfcBuildingStorey,
    IfcDoor,
    IfcFurniture,
    IfcLocalPlacement,
    IfcOpeningElement,
    IfcRailing,
    IfcRelAggregates,
    IfcRelContainedInSpatialStructure,
    IfcSanitaryTerminal,
    IfcSite,
    IfcSlabStandardCase,
    IfcSpace,
    IfcSpatialZone,
    IfcWallStandardCase,
    IfcWindow,
)


@pytest.fixture
def add_ifc_spatial_element_mock(mocker):
    from handlers.ifc.exporter.generators import IfcProductGenerator

    return mocker.patch.object(
        IfcProductGenerator,
        "add_ifc_spatial_element",
        side_effect=mocker.MagicMock(
            side_effect=lambda *args, **kwargs: f"dummy_{kwargs['ifc_spatial_element_type'].__name__}"
        ),
    )


@pytest.fixture
def add_ifc_element_mock(mocker):
    from handlers.ifc.exporter.generators import IfcProductGenerator

    return mocker.patch.object(
        IfcProductGenerator,
        "add_ifc_element",
        side_effect=mocker.MagicMock(
            side_effect=lambda *args, **kwargs: f"dummy_{kwargs['ifc_element_type'].__name__}"
        ),
    )


@pytest.fixture
def add_ifc_axis2_placement3d_mock(mocker):
    from handlers.ifc.exporter.generators import IfcGeometricRepresentationItemGenerator

    return mocker.patch.object(
        IfcGeometricRepresentationItemGenerator,
        "_add_ifc_axis2_placement3d",
        return_value="dummy_ifc_axis2_placement3d",
    )


@pytest.fixture
def add_children_to_element_mock(mocker):
    from handlers.ifc.exporter.generators import IfcRelationshipGenerator

    return mocker.patch.object(
        IfcRelationshipGenerator,
        "add_children_to_object",
        return_value="dummy_ifc_relationship",
    )


def test_entity_ifc_mapper_add_site(
    mocker,
    ifc_file_dummy,
    add_ifc_axis2_placement3d_mock,
    add_ifc_spatial_element_mock,
    add_children_to_element_mock,
):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    EntityIfcMapper.add_site(
        ifc_file=ifc_file_dummy,
        ifc_project="dummy_ifc_project",
        longitude="dummy_longitude",
        latitude="dummy_latitude",
        client_site_id="dummy_client_site_id",
        site_name="dummy_site_name",
    )

    add_ifc_axis2_placement3d_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy, Location=(0, 0, 0)
    )

    ifc_file_dummy.create_entity.assert_called_once_with(
        IfcLocalPlacement.__name__,
        RelativePlacement=add_ifc_axis2_placement3d_mock.return_value,
    )

    add_ifc_spatial_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_spatial_element_type=IfcSite,
        RefLongitude="dummy_longitude",
        RefLatitude="dummy_latitude",
        Name="dummy_client_site_id",
        LongName="dummy_site_name",
        ObjectPlacement="dummy_IfcLocalPlacement",
    )

    add_children_to_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_object="dummy_ifc_project",
        children=["dummy_IfcSite"],
        relationship_type=IfcRelAggregates,
    )


def test_entity_ifc_mapper_add_building(
    mocker, ifc_file_dummy, add_ifc_axis2_placement3d_mock, add_ifc_spatial_element_mock
):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    ifc_site_dummy = mocker.MagicMock(ObjectPlacement="ifc_site_dummy_placement")

    EntityIfcMapper.add_building(
        ifc_file=ifc_file_dummy,
        ifc_site=ifc_site_dummy,
        street="dummy_street",
        housenumber="dummy_housenumber",
    )

    add_ifc_axis2_placement3d_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy, Location=(0, 0, 0)
    )

    ifc_file_dummy.create_entity.assert_called_once_with(
        IfcLocalPlacement.__name__,
        RelativePlacement=add_ifc_axis2_placement3d_mock.return_value,
        PlacementRelTo="ifc_site_dummy_placement",
    )

    add_ifc_spatial_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_spatial_element_type=IfcBuilding,
        Name="dummy_street dummy_housenumber",
        LongName="dummy_street dummy_housenumber",
        ObjectPlacement="dummy_IfcLocalPlacement",
    )


def test_entity_ifc_mapper_add_floor(
    mocker, ifc_file_dummy, add_ifc_axis2_placement3d_mock, add_ifc_spatial_element_mock
):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    ifc_building_dummy = mocker.MagicMock(
        ObjectPlacement="ifc_building_dummy_placement"
    )

    EntityIfcMapper.add_floor(
        ifc_file=ifc_file_dummy,
        ifc_building=ifc_building_dummy,
        floor_number=42,
        elevation=1337.5,
    )

    add_ifc_axis2_placement3d_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy, Location=(0, 0, 1337.5)
    )

    ifc_file_dummy.create_entity.assert_called_once_with(
        IfcLocalPlacement.__name__,
        RelativePlacement=add_ifc_axis2_placement3d_mock.return_value,
        PlacementRelTo="ifc_building_dummy_placement",
    )

    add_ifc_spatial_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_spatial_element_type=IfcBuildingStorey,
        Name="Floor 42",
        LongName="Floor 42",
        Elevation=1337.5,
        CompositionType="ELEMENT",
        ObjectPlacement="dummy_IfcLocalPlacement",
    )


def test_entity_ifc_mapper_add_unit(mocker, add_ifc_spatial_element_mock):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    EntityIfcMapper.add_unit(ifc_file="ifc_file_dummy", client_id="dummy_client_id")

    add_ifc_spatial_element_mock.assert_called_once_with(
        ifc_file="ifc_file_dummy",
        ifc_spatial_element_type=IfcSpatialZone,
        Name="dummy_client_id",
        LongName="dummy_client_id",
    )


def test_entity_ifc_mapper_add_area(
    mocker, ifc_file_dummy, add_ifc_axis2_placement3d_mock, add_ifc_spatial_element_mock
):
    from handlers.ifc.exporter.mappers import (
        EntityIfcMapper,
        GeometryIfcMapper,
        PropertyIfcMapper,
        QuantityIfcMapper,
    )

    add_area_quantities_mock = mocker.patch.object(
        QuantityIfcMapper, "add_area_quantities"
    )
    add_area_properties_mock = mocker.patch.object(
        PropertyIfcMapper, "add_area_properties"
    )
    mocker.patch.object(
        GeometryIfcMapper,
        "polygon_to_footprint",
        return_value="dummy_shape_representation",
    )

    ifc_floor_dummy = mocker.MagicMock(ObjectPlacement="ifc_floor_dummy_placement")

    EntityIfcMapper.add_area(
        ifc_file=ifc_file_dummy,
        ifc_floor=ifc_floor_dummy,
        context="dummy_context",
        polygon="dummy_polygon",
        start_elevation_relative_to_floor=1.1,
        height=1.2,
        area_type="dummy_area_type",
        area_number_in_floor=12,
        floor_number=15,
        is_public="dummy_is_public",
        building_code_type="dummy_building_code_type",
    )

    add_ifc_spatial_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_spatial_element_type=IfcSpace,
        Name="dummy_area_type-15.12",
        LongName=None,
        Representation="dummy_IfcProductDefinitionShape",
        ObjectPlacement="dummy_IfcLocalPlacement",
    )

    add_ifc_axis2_placement3d_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        Location=(0, 0, 1.1),
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcLocalPlacement",
        RelativePlacement="dummy_ifc_axis2_placement3d",
        PlacementRelTo="ifc_floor_dummy_placement",
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcProductDefinitionShape", Representations=["dummy_shape_representation"]
    )

    add_area_quantities_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_space="dummy_IfcSpace",
        polygon="dummy_polygon",
        height=1.2,
    )
    add_area_properties_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_space="dummy_IfcSpace",
        building_code_type="dummy_building_code_type",
        is_public="dummy_is_public",
    )


@pytest.mark.parametrize(
    "element_type", [IfcWallStandardCase, IfcRailing, IfcSlabStandardCase, IfcFurniture]
)
def test_entity_ifc_mapper_add_generic_element(
    mocker,
    ifc_file_dummy,
    add_ifc_axis2_placement3d_mock,
    add_ifc_element_mock,
    element_type,
):
    from handlers.ifc.exporter.mappers import EntityIfcMapper, GeometryIfcMapper

    polygon_to_extruded_solid_mock = mocker.patch.object(
        GeometryIfcMapper,
        "polygon_to_extruded_solid",
        return_value="dummy_shape_representation",
    )

    ifc_floor_dummy = mocker.MagicMock(ObjectPlacement="ifc_floor_dummy_placement")

    EntityIfcMapper.add_generic_element(
        ifc_file=ifc_file_dummy,
        ifc_floor=ifc_floor_dummy,
        context="dummy_context",
        polygon="dummy_polygon",
        start_elevation_relative_to_floor=1.1,
        height=1.2,
        element_type=element_type,
        some_kwarg="some_kwarg_value",
    )

    polygon_to_extruded_solid_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        polygon="dummy_polygon",
        context="dummy_context",
        start_altitude=0.0,
        end_altitude=1.2,
    )

    add_ifc_axis2_placement3d_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        Location=(0, 0, 1.1),
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcLocalPlacement",
        RelativePlacement="dummy_ifc_axis2_placement3d",
        PlacementRelTo="ifc_floor_dummy_placement",
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcProductDefinitionShape", Representations=["dummy_shape_representation"]
    )

    add_ifc_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_element_type=element_type,
        Representation="dummy_IfcProductDefinitionShape",
        ObjectPlacement="dummy_IfcLocalPlacement",
        some_kwarg="some_kwarg_value",
    )


def test_entity_ifc_mapper_add_sanitary_terminal(
    mocker, ifc_file_dummy, add_ifc_axis2_placement3d_mock, add_ifc_element_mock
):
    from handlers.ifc.exporter.mappers import EntityIfcMapper, GeometryIfcMapper

    transformed_surface_model_mock = mocker.patch.object(
        GeometryIfcMapper,
        "transformed_surface_model",
        return_value="dummy_shape_representation",
    )

    ifc_floor_dummy = mocker.MagicMock(ObjectPlacement="ifc_floor_dummy_placement")

    EntityIfcMapper.add_sanitary_terminal(
        ifc_file=ifc_file_dummy,
        ifc_floor=ifc_floor_dummy,
        context="dummy_context",
        ifc_element_type=IfcSanitaryTerminal,
        axes="dummy_axes_array",
        scales="dummy_scales_array",
        translation="dummy_translation_array",
        surface_model_path="dummy_surface_model_path",
        surface_model_matrix="dummy_surface_model_matrix",
        some_kwarg="some_kwarg_value",
    )

    transformed_surface_model_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        context="dummy_context",
        axes="dummy_axes_array",
        scales="dummy_scales_array",
        translation="dummy_translation_array",
        surface_model_path="dummy_surface_model_path",
        surface_model_matrix="dummy_surface_model_matrix",
    )

    add_ifc_axis2_placement3d_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        Location=(0, 0, 0),
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcLocalPlacement",
        RelativePlacement="dummy_ifc_axis2_placement3d",
        PlacementRelTo="ifc_floor_dummy_placement",
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcProductDefinitionShape", Representations=["dummy_shape_representation"]
    )

    add_ifc_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_element_type=IfcSanitaryTerminal,
        Representation="dummy_IfcProductDefinitionShape",
        ObjectPlacement="dummy_IfcLocalPlacement",
        some_kwarg="some_kwarg_value",
    )


@pytest.mark.parametrize("element_type", [IfcDoor, IfcWindow])
def test_entity_ifc_mapper_add_door_window(
    mocker,
    ifc_file_dummy,
    add_ifc_axis2_placement3d_mock,
    add_ifc_element_mock,
    element_type,
):
    from handlers.ifc.exporter.generators import IfcRelationshipGenerator
    from handlers.ifc.exporter.mappers import (
        EntityIfcMapper,
        GeometryIfcMapper,
        QuantityIfcMapper,
    )

    add_opening_to_element_mock = mocker.patch.object(
        IfcRelationshipGenerator, "add_opening_to_element"
    )
    add_filling_to_opening_mock = mocker.patch.object(
        IfcRelationshipGenerator, "add_filling_to_opening"
    )
    add_quantities_mock = mocker.patch.object(
        QuantityIfcMapper,
        "add_door_quantities" if element_type == IfcDoor else "add_window_quantities",
    )

    polygon_to_extruded_solid_mock = mocker.patch.object(
        GeometryIfcMapper,
        "polygon_to_extruded_solid",
        return_value="dummy_shape_representation",
    )

    ifc_wall_dummy = mocker.MagicMock(ObjectPlacement="ifc_wall_dummy_placement")

    EntityIfcMapper.add_door_window(
        ifc_file=ifc_file_dummy,
        ifc_wall=ifc_wall_dummy,
        context="dummy_context",
        polygon="dummy_polygon",
        start_elevation_relative_to_floor=1.1,
        height=1.2,
        element_type=element_type,
        some_kwarg="some_kwarg_value",
    )

    polygon_to_extruded_solid_mock.assert_has_calls(
        [
            mocker.call(
                ifc_file=ifc_file_dummy,
                polygon="dummy_polygon",
                context="dummy_context",
                start_altitude=0.0,
                end_altitude=1.2,
            )
            for _ in range(2)
        ]
    )

    add_ifc_axis2_placement3d_mock.assert_has_calls(
        [mocker.call(ifc_file=ifc_file_dummy, Location=(0, 0, 1.1)) for _ in range(2)]
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcLocalPlacement",
        RelativePlacement="dummy_ifc_axis2_placement3d",
        PlacementRelTo="ifc_wall_dummy_placement",
    )

    ifc_file_dummy.create_entity.assert_any_call(
        "IfcProductDefinitionShape", Representations=["dummy_shape_representation"]
    )

    assert ifc_file_dummy.create_entity.call_count == 4

    add_ifc_element_mock.assert_has_calls(
        [
            mocker.call(
                ifc_file=ifc_file_dummy,
                ifc_element_type=element_type,
                Representation="dummy_IfcProductDefinitionShape",
                ObjectPlacement="dummy_IfcLocalPlacement",
                some_kwarg="some_kwarg_value",
            ),
            mocker.call(
                ifc_file=ifc_file_dummy,
                ifc_element_type=IfcOpeningElement,
                Representation="dummy_IfcProductDefinitionShape",
                ObjectPlacement="dummy_IfcLocalPlacement",
            ),
        ]
    )

    add_opening_to_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        element=ifc_wall_dummy,
        opening="dummy_IfcOpeningElement",
    )

    add_filling_to_opening_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        opening="dummy_IfcOpeningElement",
        element=f"dummy_{element_type.__name__}",
    )

    if element_type == IfcDoor:
        add_quantities_mock.assert_called_once_with(
            ifc_file=ifc_file_dummy,
            ifc_door="dummy_IfcDoor",
            polygon="dummy_polygon",
            height=1.2,
        )
    else:
        add_quantities_mock.assert_called_once_with(
            ifc_file=ifc_file_dummy,
            ifc_window="dummy_IfcWindow",
            polygon="dummy_polygon",
            height=1.2,
        )


@pytest.mark.parametrize(
    "method, expected_relationship_type",
    [
        ("add_buildings_to_site", IfcRelAggregates),
        ("add_floors_to_building", IfcRelAggregates),
        ("add_units_to_floor", IfcRelContainedInSpatialStructure),
        ("add_areas_to_floor", IfcRelAggregates),
        ("add_elements_to_floor", IfcRelContainedInSpatialStructure),
        ("add_areas_to_unit", IfcRelAggregates),
        ("add_elements_to_area", IfcRelContainedInSpatialStructure),
    ],
)
def test_entity_ifc_mapper_relations(
    mocker,
    add_children_to_element_mock,
    ifc_file_dummy,
    method,
    expected_relationship_type,
):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    getattr(EntityIfcMapper, method)(ifc_file_dummy, "dummy_parent", "dummy_children")

    add_children_to_element_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ifc_object="dummy_parent",
        children="dummy_children",
        relationship_type=expected_relationship_type,
    )

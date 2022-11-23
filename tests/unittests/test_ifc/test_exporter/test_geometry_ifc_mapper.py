import pytest


@pytest.fixture
def add_ifc_extruded_area_solid_mock(mocker):
    from handlers.ifc.exporter.generators import IfcGeometricRepresentationItemGenerator

    return mocker.patch.object(
        IfcGeometricRepresentationItemGenerator,
        "add_ifc_extruded_area_solid",
        return_value="dummy_extruded_area_solid",
    )


@pytest.fixture
def add_shape_representation_mock(mocker):
    from handlers.ifc.exporter.generators import IfcGeometricRepresentationItemGenerator

    return mocker.patch.object(
        IfcGeometricRepresentationItemGenerator,
        "add_shape_representation",
        side_effect=lambda *args, **kwargs: f"dummy_shape_representation({kwargs['Items']})",
    )


@pytest.mark.parametrize(
    "polygon_fixture_name,expected_exterior,expected_holes",
    [
        (
            "polygon_with_holes",
            (
                (0.0, 0.0, 1.1),
                (0.0, 2.0, 1.1),
                (2.0, 2.0, 1.1),
                (2.0, 0.0, 1.1),
                (0.0, 0.0, 1.1),
            ),
            (
                (
                    (1.0, 0.1, 1.1),
                    (1.5, 0.5, 1.1),
                    (1.0, 1.0, 1.1),
                    (0.5, 0.5, 1.1),
                    (1.0, 0.1, 1.1),
                ),
            ),
        )
    ],
)
def test_geometry_ifc_mapper_polygon_to_footprint(
    mocker,
    request,
    ifc_file_dummy,
    add_ifc_extruded_area_solid_mock,
    add_shape_representation_mock,
    polygon_fixture_name,
    expected_exterior,
    expected_holes,
):
    from handlers.ifc.exporter.mappers import GeometryIfcMapper

    GeometryIfcMapper.polygon_to_footprint(
        ifc_file=ifc_file_dummy,
        context="dummy_context",
        polygon=request.getfixturevalue(polygon_fixture_name),
        start_altitude=1.1,
        end_altitude=2.5,
    )

    assert (
        tuple(add_ifc_extruded_area_solid_mock.call_args.kwargs["exterior"])
        == expected_exterior
    )
    assert (
        tuple(map(tuple, add_ifc_extruded_area_solid_mock.call_args.kwargs["holes"]))
        == expected_holes
    )
    assert add_ifc_extruded_area_solid_mock.call_args.kwargs["extrusion_height"] == 1.4

    add_shape_representation_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ContextOfItems="dummy_context",
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=["dummy_extruded_area_solid"],
    )


@pytest.mark.parametrize(
    "polygon_fixture_name,expected_exterior,expected_holes",
    [
        (
            "polygon_with_holes",
            (
                (0.0, 0.0, 1.1),
                (0.0, 2.0, 1.1),
                (2.0, 2.0, 1.1),
                (2.0, 0.0, 1.1),
                (0.0, 0.0, 1.1),
            ),
            (
                (
                    (1.0, 0.1, 1.1),
                    (1.5, 0.5, 1.1),
                    (1.0, 1.0, 1.1),
                    (0.5, 0.5, 1.1),
                    (1.0, 0.1, 1.1),
                ),
            ),
        ),
        (
            "polygon_with_tiny_holes",
            (
                (0.0, 0.0, 1.1),
                (0.0, 2.0, 1.1),
                (2.0, 2.0, 1.1),
                (2.0, 0.0, 1.1),
                (0.0, 0.0, 1.1),
            ),
            tuple(),
        ),
    ],
)
def test_geometry_ifc_mapper_polygon_to_extruded_solid(
    mocker,
    request,
    ifc_file_dummy,
    add_ifc_extruded_area_solid_mock,
    add_shape_representation_mock,
    polygon_fixture_name,
    expected_exterior,
    expected_holes,
):
    from handlers.ifc.exporter.mappers import GeometryIfcMapper

    GeometryIfcMapper.polygon_to_extruded_solid(
        ifc_file=ifc_file_dummy,
        context="dummy_context",
        polygon=request.getfixturevalue(polygon_fixture_name),
        start_altitude=1.1,
        end_altitude=2.5,
    )

    assert (
        tuple(add_ifc_extruded_area_solid_mock.call_args.kwargs["exterior"])
        == expected_exterior
    )
    assert (
        tuple(map(tuple, add_ifc_extruded_area_solid_mock.call_args.kwargs["holes"]))
        == expected_holes
    )
    assert add_ifc_extruded_area_solid_mock.call_args.kwargs["extrusion_height"] == 1.4

    add_shape_representation_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        ContextOfItems="dummy_context",
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=["dummy_extruded_area_solid"],
    )


def test_geometry_ifc_mapper_transformed_surface_model(
    mocker,
    ifc_file_dummy,
    add_shape_representation_mock,
):
    from handlers.ifc.exporter.generators import IfcGeometricRepresentationItemGenerator
    from handlers.ifc.exporter.mappers import GeometryIfcMapper

    add_ifc_face_based_surface_model_mock = mocker.patch.object(
        IfcGeometricRepresentationItemGenerator,
        "add_ifc_face_based_surface_model",
        return_value="dummy_IfcFaceBasedSurfaceModel",
    )
    add_mapping_mock = mocker.patch.object(
        IfcGeometricRepresentationItemGenerator,
        "add_mapping",
        return_value="dummy_IfcMappedItem",
    )

    GeometryIfcMapper.transformed_surface_model(
        ifc_file=ifc_file_dummy,
        context="dummy_context",
        axes="dummy_axes_array",
        scales="dummy_scales_array",
        translation="dummy_translation_array",
        surface_model_path="dummy_surface_model_path",
        surface_model_matrix="dummy_surface_model_matrix",
    )

    add_ifc_face_based_surface_model_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        file_path="dummy_surface_model_path",
        model_matrix="dummy_surface_model_matrix",
    )

    add_shape_representation_mock.assert_has_calls(
        [
            mocker.call(
                ifc_file=ifc_file_dummy,
                ContextOfItems="dummy_context",
                RepresentationIdentifier="Body",
                RepresentationType="SurfaceModel",
                Items=["dummy_IfcFaceBasedSurfaceModel"],
            ),
            mocker.call(
                ifc_file=ifc_file_dummy,
                ContextOfItems="dummy_context",
                RepresentationIdentifier="Body",
                RepresentationType="MappedRepresentation",
                Items=["dummy_IfcMappedItem"],
            ),
        ]
    )

    add_mapping_mock.assert_called_once_with(
        ifc_file=ifc_file_dummy,
        MappedRepresentation="dummy_shape_representation(['dummy_IfcFaceBasedSurfaceModel'])",
        axes="dummy_axes_array",
        scales="dummy_scales_array",
        translation="dummy_translation_array",
    )

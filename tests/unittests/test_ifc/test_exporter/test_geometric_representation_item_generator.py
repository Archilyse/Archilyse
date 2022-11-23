from pathlib import Path

import pytest
from numpy import array, identity
from numpy.testing import assert_array_almost_equal

from handlers.ifc.exporter.generators.ifc_geometric_representation_item import (
    IfcGeometricRepresentationItemGenerator,
)


def test_geometric_representation_item_generator_add_ifc_polyline(
    mocker, ifc_file_dummy
):
    points = [(0, 0, 0), (0, 1, 2), (0, 1, 3), (0, 1, 4), (0, 1, 5)]
    IfcGeometricRepresentationItemGenerator.add_ifc_polyline(
        ifc_file=ifc_file_dummy, Points=points
    )

    assert ifc_file_dummy.create_entity.call_args_list == [
        mocker.call("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
        mocker.call("IfcCartesianPoint", Coordinates=(0.0, 1.0, 2.0)),
        mocker.call("IfcCartesianPoint", Coordinates=(0.0, 1.0, 3.0)),
        mocker.call("IfcCartesianPoint", Coordinates=(0.0, 1.0, 4.0)),
        mocker.call("IfcCartesianPoint", Coordinates=(0.0, 1.0, 5.0)),
        mocker.call(
            "IfcPolyline",
            Points=[
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
            ],
        ),
    ]

    # Make sure caching works
    ifc_file_dummy.create_entity.reset_mock()
    IfcGeometricRepresentationItemGenerator.add_ifc_polyline(
        ifc_file=ifc_file_dummy, Points=points
    )
    assert ifc_file_dummy.create_entity.call_args_list == [
        mocker.call(
            "IfcPolyline",
            Points=[
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
            ],
        )
    ]


@pytest.mark.parametrize(
    "exterior,holes",
    [
        (
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
def test_geometric_representation_item_generator_add_ifc_extruded_area_solid(
    mocker, ifc_file_dummy, exterior, holes
):
    add_polyline_mock = mocker.patch.object(
        IfcGeometricRepresentationItemGenerator,
        "add_ifc_polyline",
        return_value="dummy_polyline",
    )

    IfcGeometricRepresentationItemGenerator.add_ifc_extruded_area_solid(
        ifc_file=ifc_file_dummy, exterior=exterior, holes=holes, extrusion_height=42
    )

    add_polyline_mock.assert_has_calls(
        [mocker.call(ifc_file=ifc_file_dummy, Points=exterior)]
        + [mocker.call(ifc_file=ifc_file_dummy, Points=points) for points in holes]
    )

    if holes:
        expected_profile_call = mocker.call(
            "IfcArbitraryProfileDefWithVoids",
            ProfileType="AREA",
            ProfileName=None,
            OuterCurve="dummy_polyline",
            InnerCurves=["dummy_polyline"] * len(holes),
        )
        expected_solid_call = mocker.call(
            "IfcExtrudedAreaSolid",
            SweptArea="dummy_IfcArbitraryProfileDefWithVoids",
            Position="dummy_IfcAxis2Placement3d",
            Depth=42,
            ExtrudedDirection="dummy_IfcDirection",
        )
    else:
        expected_profile_call = mocker.call(
            "IfcArbitraryClosedProfileDef",
            ProfileType="AREA",
            ProfileName=None,
            OuterCurve="dummy_polyline",
        )
        expected_solid_call = mocker.call(
            "IfcExtrudedAreaSolid",
            SweptArea="dummy_IfcArbitraryClosedProfileDef",
            Position="dummy_IfcAxis2Placement3d",
            Depth=42,
            ExtrudedDirection="dummy_IfcDirection",
        )

    ifc_file_dummy.create_entity.assert_has_calls([expected_profile_call])
    ifc_file_dummy.create_entity.assert_has_calls([expected_solid_call])


@pytest.mark.parametrize(
    "model_matrix,normalize,expected_points",
    [
        (
            identity(3),
            True,
            [(-2 / 3, -1 / 3, -2 / 3), (1 / 3, -1 / 3, 1 / 3), (1 / 3, 2 / 3, 1 / 3)],
        ),
        (identity(3), False, [(0, 0, 0), (1, 0, 1), (1, 1, 1)]),
        (
            array(((0, 1, 0), (1, 0, 0), (0, 0, 1))),
            False,
            [(0, 0, 0), (0, 1, 1), (1, 1, 1)],
        ),
    ],
)
def test_geometric_representation_item_generator_add_ifc_face_based_surface_model(
    mocker, ifc_file_dummy, model_matrix, normalize, expected_points
):
    import collada

    class FakeTriangleSet(collada.triangleset.TriangleSet):
        @property
        def vertex(self):
            return [(0, 0, 0), (1, 0, 1), (1, 1, 1)]

        @property
        def vertex_index(self):
            return [(0, 1, 2)]

        def __init__(self, *args, **kwargs):
            pass

    fake_collada_file = mocker.MagicMock()
    fake_collada_file.geometries = [
        mocker.MagicMock(primitives=[FakeTriangleSet(), FakeTriangleSet()])
    ]
    mocker.patch.object(collada, "Collada", return_value=fake_collada_file)

    IfcGeometricRepresentationItemGenerator.add_ifc_face_based_surface_model(
        ifc_file=ifc_file_dummy,
        file_path=Path("/some/random_path/"),
        model_matrix=model_matrix,
        normalize=normalize,
    )

    model_points = [
        call.kwargs["Coordinates"]
        for call in ifc_file_dummy.create_entity.call_args_list
        if call.args[0] == "IfcCartesianPoint"
    ]
    assert_array_almost_equal(model_points, expected_points)

    assert ifc_file_dummy.create_entity.call_args_list[3:] == [
        mocker.call(
            "IfcPolyLoop",
            Polygon=[
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
            ],
        ),
        mocker.call("IfcFaceOuterBound", Bound="dummy_IfcPolyLoop", Orientation=False),
        mocker.call("IfcFace", Bounds=["dummy_IfcFaceOuterBound"]),
        mocker.call("IfcConnectedFaceSet", CfsFaces=["dummy_IfcFace"]),
        mocker.call(
            "IfcPolyLoop",
            Polygon=[
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
                "dummy_IfcCartesianPoint",
            ],
        ),
        mocker.call("IfcFaceOuterBound", Bound="dummy_IfcPolyLoop", Orientation=False),
        mocker.call("IfcFace", Bounds=["dummy_IfcFaceOuterBound"]),
        mocker.call("IfcConnectedFaceSet", CfsFaces=["dummy_IfcFace"]),
        mocker.call(
            "IfcFaceBasedSurfaceModel",
            FbsmFaces=["dummy_IfcConnectedFaceSet", "dummy_IfcConnectedFaceSet"],
        ),
    ]

    # Make sure caching is working (loaded model is being reused)
    ifc_file_dummy.create_entity.reset_mock()
    IfcGeometricRepresentationItemGenerator.add_ifc_face_based_surface_model(
        ifc_file=ifc_file_dummy,
        file_path=Path("/some/random_path/"),
        model_matrix=model_matrix,
        normalize=normalize,
    )
    assert ifc_file_dummy.create_entity.call_args_list == [
        mocker.call(
            "IfcFaceBasedSurfaceModel",
            FbsmFaces=["dummy_IfcConnectedFaceSet", "dummy_IfcConnectedFaceSet"],
        )
    ]


def test_geometric_representation_item_generator_add_mapping(
    mocker, ifc_file_dummy_with_parameters
):
    IfcGeometricRepresentationItemGenerator.add_mapping(
        ifc_file=ifc_file_dummy_with_parameters,
        MappedRepresentation="MappedRepresentation_dummy",
        axes=[(1, 2, 3), (4, 5, 6), (7, 8, 9)],
        scales=(1.1, 1.2, 1.3),
        translation=(42, 43, 44),
        MappingOrigin=(0, 1, 2),
    )

    assert ifc_file_dummy_with_parameters.create_entity.call_args_list[
        -1
    ] == mocker.call(
        "IfcMappedItem",
        MappingSource="dummy_IfcRepresentationMap({'MappingOrigin': (0, 1, 2), 'MappedRepresentation': 'MappedRepresentation_dummy'})",
        MappingTarget="dummy_IfcCartesianTransformationOperator3dNonUniform({'Axis1': \"dummy_IfcDirection({'DirectionRatios': (1.0, 2.0, 3.0)})\", 'Axis2': \"dummy_IfcDirection({'DirectionRatios': (4.0, 5.0, 6.0)})\", 'LocalOrigin': \"dummy_IfcCartesianPoint({'Coordinates': (42.0, 43.0, 44.0)})\", 'Scale': 1.1, 'Axis3': \"dummy_IfcDirection({'DirectionRatios': (7.0, 8.0, 9.0)})\", 'Scale2': 1.2, 'Scale3': 1.3})",
    )

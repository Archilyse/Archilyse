import json

import pytest
from shapely.geometry import Polygon

from ifc_reader.constants import IFC_STAIR
from ifc_reader.exceptions import IfcMapperException
from ifc_reader.ifc_mapper import IfcToSpatialEntityMapper


def test_get_geometry_from_ifc_shape_should_return_polygon(
    mocker,
    ac20_fzk_haus_ifc_reader,
    fixtures_path,
):

    ifc_mapper = IfcToSpatialEntityMapper(reader=ac20_fzk_haus_ifc_reader)
    with fixtures_path.joinpath("ifc/linestring_shape.json").open() as f:
        shape_parameters = json.load(f)
    ifc_shape = mocker.Mock()
    ifc_shape.geometry.verts = shape_parameters["verts"]
    ifc_shape.geometry.faces = shape_parameters["faces"]
    ifc_2d_entity = ifc_mapper._get_geometry_from_ifc_shape(
        ifc_shape=ifc_shape, ifc_type=IFC_STAIR
    )
    assert ifc_2d_entity.max_height == pytest.approx(2.5, abs=1e-3)
    assert ifc_2d_entity.min_height == pytest.approx(0.0, abs=1e-3)
    assert ifc_2d_entity.geometry.minimum_rotated_rectangle.area == pytest.approx(
        2.26e-9, abs=1e-3
    )


def test_get_geometry_from_ifc_shape_should_raise_if_no_vertices_of_faces(
    mocker,
    ac20_fzk_haus_ifc_reader,
    fixtures_path,
):

    with pytest.raises(
        IfcMapperException, match="does not have a valid mesh to generate a geometry"
    ):
        ifc_mapper = IfcToSpatialEntityMapper(reader=ac20_fzk_haus_ifc_reader)
        ifc_shape = mocker.Mock()
        ifc_shape.geometry.verts = []
        ifc_shape.geometry.faces = []
        ifc_mapper._get_geometry_from_ifc_shape(ifc_shape=ifc_shape, ifc_type=IFC_STAIR)


def test_get_geometry_from_ifc_shape_should_raise_if_geometry_empty(
    mocker,
    ac20_fzk_haus_ifc_reader,
    fixtures_path,
):
    mocker.patch.object(
        IfcToSpatialEntityMapper,
        "get_polygons_from_vertices_and_faces",
        return_value=[Polygon()],
    )
    with pytest.raises(
        IfcMapperException, match="is generating a polygon with no area"
    ):
        ifc_mapper = IfcToSpatialEntityMapper(reader=ac20_fzk_haus_ifc_reader)
        ifc_shape = mocker.Mock()
        ifc_shape.geometry.verts = [1, 2, 3]
        ifc_shape.geometry.faces = [0]
        ifc_mapper._get_geometry_from_ifc_shape(ifc_shape=ifc_shape, ifc_type=IFC_STAIR)

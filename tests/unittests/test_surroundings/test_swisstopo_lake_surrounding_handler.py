import json
import os

import pytest
from shapely.geometry import Point

from common_utils.constants import SurroundingType
from surroundings.swisstopo import SwissTopoLakeSurroundingHandler
from tests.utils import check_surr_triangles, random_simulation_version


@pytest.mark.parametrize(
    "filename,number_of_triangles,area,lv95_location",
    [
        ("vierwaldstaettersee.wkt", 105, 485766.693, Point(2672698, 1212023)),
        ("brienzersee.wkt", 186, 509160.7141, Point(2645577, 1176633)),
    ],
)
def test_missing_lakes(
    mocker,
    fixtures_swisstopo_path,
    mocked_gcp_download,
    mock_elevation,
    filename,
    number_of_triangles,
    area,
    lv95_location,
):
    from surroundings.swisstopo import SwissTopoExtraLakesSurroundingHandler

    mock_elevation(100)
    mocker.patch.object(os, "listdir", return_value=[filename])

    lsh = SwissTopoExtraLakesSurroundingHandler(
        location=lv95_location,
        bounding_box_extension=500,
        simulation_version=random_simulation_version(),
    )
    lsh._ENTITIES_FILE_PATH = (
        fixtures_swisstopo_path.joinpath("lakes/MISSING_LAKES").joinpath(filename),
    )

    triangles = list(lsh.get_triangles())

    check_surr_triangles(
        expected_area=area,
        first_elem_height=100.0,
        expected_num_triangles=number_of_triangles,
        surr_triangles=triangles,
        expected_surr_type={SurroundingType.LAKES},
    )


def test_lake_zurich(
    mocker, fixtures_swisstopo_path, mocked_gcp_download, mock_elevation
):

    LOCATION = Point(2682799.7836149014, 1246372.9172727354)

    mock_elevation(100)
    with fixtures_swisstopo_path.joinpath(
        "lakes/mocked_fiona_zuerichsee.json"
    ).open() as f:
        mocked_fiona_lake_entities = mocker.patch.object(
            SwissTopoLakeSurroundingHandler,
            "load_entities",
            return_value=json.load(f),
        )

    triangles = list(
        SwissTopoLakeSurroundingHandler(
            location=LOCATION,
            bounding_box_extension=500,
            simulation_version=random_simulation_version(),
        ).get_triangles()
    )

    assert mocked_fiona_lake_entities.call_count == 1

    check_surr_triangles(
        expected_area=263956.4356259643,
        first_elem_height=100.0,
        expected_num_triangles=7053,
        surr_triangles=triangles,
        expected_surr_type={SurroundingType.LAKES},
    )

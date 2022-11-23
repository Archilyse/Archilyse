import json

import pytest
from shapely.geometry import Point

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from tests.utils import check_surr_triangles, random_simulation_version


@pytest.mark.parametrize(
    "detailed_rivers_path, line_rivers_path, sim_version, lv95_location, expected_triangles, expected_area, bounding_box_extension, elevation",
    [
        (
            "detailed_rivers.json",
            "line_rivers.json",
            random_simulation_version(),
            Point(2612953.4424275705, 1267306.2163103924),
            177,
            77809.97787068681,
            200,
            250.0,
        ),
        (
            "",
            "line_rivers_invalid.json",
            SIMULATION_VERSION.PH_01_2021,
            Point(2674469.3530939496, 1209108.1068535496),
            262,
            7591.895680590974,
            1000,
            500.0,
        ),
        (
            "",
            "line_rivers_invalid.json",
            SIMULATION_VERSION.EXPERIMENTAL,
            Point(2674469.3530939496, 1209108.1068535496),
            270,
            7591.895680590974,
            1000,
            500.0,
        ),
    ],
)
def test_generate_rivers(
    mocker,
    surr_river_path,
    detailed_rivers_path,
    sim_version,
    line_rivers_path,
    lv95_location,
    expected_triangles,
    expected_area,
    bounding_box_extension,
    elevation,
    mock_elevation,
):
    from surroundings.swisstopo import SwissTopoRiverSurroundingHandler

    river_handler = SwissTopoRiverSurroundingHandler(
        location=lv95_location,
        bounding_box_extension=bounding_box_extension,
        simulation_version=sim_version,
    )

    if detailed_rivers_path:
        with surr_river_path.joinpath(detailed_rivers_path).open() as f:
            surr_river_detailed = json.load(f)
    else:
        surr_river_detailed = []

    mocker.patch.object(
        river_handler, "read_detailed_entities", return_value=surr_river_detailed
    )

    if line_rivers_path:
        with surr_river_path.joinpath(line_rivers_path).open() as f:
            surr_river_lines = json.load(f)
    else:
        surr_river_lines = []

    mocker.patch.object(river_handler, "load_entities", return_value=surr_river_lines)
    mock_elevation(elevation)

    river_triangles = list(river_handler.get_triangles())
    assert (
        min([point[2] for _, triangle in river_triangles for point in triangle])
        == elevation
    )
    assert (
        max([point[2] for _, triangle in river_triangles for point in triangle])
        == elevation
    )

    check_surr_triangles(
        expected_area=expected_area,
        first_elem_height=elevation,
        expected_num_triangles=expected_triangles,
        surr_triangles=river_triangles,
        expected_surr_type={SurroundingType.RIVERS},
    )

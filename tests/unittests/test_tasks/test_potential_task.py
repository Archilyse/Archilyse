from pathlib import Path

import pytest
from shapely.geometry import CAP_STYLE, Point, Polygon, box

from common_utils.constants import GOOGLE_CLOUD_BUCKET, GOOGLE_CLOUD_POTENTIAL_DATASET
from surroundings.base_building_handler import Building
from tasks.potential_view_tasks import (
    generate_potential_tile,
    get_building_footprints_to_simulate,
)


@pytest.mark.parametrize(
    "bounding_box_extension, expected",
    [
        (25, 3),
        (11, 2),
        (4, 1),
        (2, 0),
    ],
)
def test_get_building_footprints_to_simulate(bounding_box_extension, expected):
    center_point = Point(0, 0)

    building_1 = Point(0, 0).buffer(5, cap_style=CAP_STYLE.square)
    building_2 = Point(10.5, 0).buffer(5, cap_style=CAP_STYLE.square)
    building_3 = Point(21, 0).buffer(5, cap_style=CAP_STYLE.square)
    buildings = [
        Building(geometry=b, footprint=b) for b in [building_1, building_2, building_3]
    ]

    assert (
        len(
            list(
                get_building_footprints_to_simulate(
                    location=center_point,
                    buildings=buildings,
                    bounding_box_extension=bounding_box_extension,
                )
            )
        )
        == expected
    )


def test_get_building_footprints_to_simulate_filters_small_interior_holes():
    center_point = Point(0, 0)

    building_1 = Polygon(
        [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)],
        [[(5, 5), (5, 5.1), (5.1, 5.1), (5.1, 5), (5, 5)]],
    )
    buildings = [Building(geometry=building_1, footprint=building_1)]
    result = list(
        get_building_footprints_to_simulate(
            location=center_point,
            buildings=buildings,
            bounding_box_extension=100,
        )
    )
    assert len(result) == 1
    assert not bool(result[0].interiors)


def test_get_building_footprints_to_simulate_too_small_building():
    center_point = Point(0, 0)

    building_1 = Polygon(
        [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)],
    )
    buildings = [Building(geometry=building_1, footprint=building_1)]
    result = list(
        get_building_footprints_to_simulate(
            location=center_point,
            buildings=buildings,
            bounding_box_extension=100,
        )
    )
    assert len(result) == 0


def test_get_building_footprints_to_simulate_repeated_vertices():
    center_point = Point(0, 0)

    building_1 = Polygon(
        [(0, 0), (0, 20), (20, 20), (20, 20), (20, 0), (0, 0)],
    )
    buildings = [Building(geometry=building_1, footprint=building_1)]
    result = list(
        get_building_footprints_to_simulate(
            location=center_point,
            buildings=buildings,
            bounding_box_extension=100,
        )
    )
    assert len(result) == 1
    assert len(result[0].exterior.coords[:]) == len(building_1.exterior.coords[:]) - 1
    assert result[0].exterior.coords[3] == pytest.approx(
        building_1.exterior.coords[4], abs=0.01
    )


def test_upload_tile_to_gcs(mocker, mocked_gcp_upload_file_to_bucket):
    import tasks.potential_view_tasks as pvt
    from handlers.simulations.potential_tile_exporter import PotentialTileExporter

    mocker.patch.object(
        PotentialTileExporter,
        PotentialTileExporter._get_filtered_entities.__name__,
        return_value=[],
    )
    directory = mocker.spy(pvt.TemporaryDirectory, "__enter__")

    generate_potential_tile(
        tile_bounds=(0, 0, 0.01, 0.01), dump_shape=box(0, 0, 0.01, 0.01).wkt
    )

    mocked_gcp_upload_file_to_bucket.assert_has_calls(
        [
            mocker.call(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                destination_folder=GOOGLE_CLOUD_POTENTIAL_DATASET,
                local_file_path=Path(directory.spy_return).joinpath(
                    "view_N00000_E00000.zip"
                ),
            ),
            mocker.call(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                destination_folder=GOOGLE_CLOUD_POTENTIAL_DATASET,
                local_file_path=Path(directory.spy_return).joinpath(
                    "sun_N00000_E00000.zip"
                ),
            ),
        ],
        any_order=True,
    )

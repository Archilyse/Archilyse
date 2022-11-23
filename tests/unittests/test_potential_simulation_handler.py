from pathlib import Path

import pytest
from pathvalidate import is_valid_filename
from shapely.geometry import MultiPolygon, box

from common_utils.constants import REGION, SIMULATION_VERSION, SURROUNDING_SOURCES
from handlers import PotentialSimulationHandler


@pytest.mark.parametrize(
    "region, source_surr, simulation_version, building_footprint",
    [
        (
            region,
            source_surr,
            simulation_version,
            building_footprint,
        )
        for region in REGION
        for source_surr in SURROUNDING_SOURCES
        for simulation_version in SIMULATION_VERSION
        for building_footprint in [
            box(6.0, 46.0, 8.0, 48.0).wkt,
            MultiPolygon([box(6.0, 46.0, 8.0, 48.0), box(1, 0, 2, 2)]).wkt,
        ]
    ],
)
def test_get_surroundings_path(
    region, source_surr, simulation_version, building_footprint
):
    path = PotentialSimulationHandler.get_surroundings_path(
        region=region,
        source_surr=source_surr,
        simulation_version=simulation_version,
        building_footprint_wkt=building_footprint,
    )
    assert is_valid_filename(path.name)


def test_upload_view_surr(
    mocked_gcp_upload_file_to_bucket,
):
    # todo change
    PotentialSimulationHandler.upload_view_surroundings(
        triangles=[], path=Path("jan-the-fav.csv")
    )
    assert mocked_gcp_upload_file_to_bucket.assert_called_once

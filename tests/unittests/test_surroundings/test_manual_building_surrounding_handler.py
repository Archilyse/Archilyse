import json

import pytest
from shapely.geometry import Point, Polygon

from common_utils.constants import REGION, ManualSurroundingTypes, SurroundingType
from handlers.db import ManualSurroundingsDBHandler
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.manual_surroundings import (
    ManualBuildingSurroundingHandler,
    ManualExclusionSurroundingHandler,
)
from surroundings.manual_surroundings.utils import FeatureProviderMixin


@pytest.fixture
def get_manually_created_surroundings_from_db(mocker, manually_created_surroundings):
    return mocker.patch.object(
        ManualSurroundingsDBHandler,
        "try_get_by",
        return_value={"surroundings": manually_created_surroundings},
    )


class TestManualBuildingSurroundingHandler:
    @pytest.fixture
    def manually_created_building_footprint_triangulated(self, fixtures_path):
        with open(
            fixtures_path.joinpath(
                "manually_created_building_footprint_triangulated.json"
            ),
            "r",
        ) as f:
            return [(SurroundingType.BUILDINGS, triangle) for triangle in json.load(f)]

    def test_get_triangles(
        self,
        mocker,
        get_manually_created_surroundings_from_db,
        manually_created_building_footprint_triangulated,
    ):
        fake_site_id = -999
        dummy_location = Point(-999, -999)
        region = REGION.CH
        assert (
            list(
                ManualBuildingSurroundingHandler(
                    site_id=fake_site_id,
                    region=region,
                    elevation_handler=ZeroElevationHandler(
                        location=dummy_location,
                        region=region,
                        simulation_version=mocker.ANY,
                    ),
                ).get_triangles()
            )
            == manually_created_building_footprint_triangulated
        )
        get_manually_created_surroundings_from_db.assert_called_once_with(
            site_id=fake_site_id
        )


class TestManualExclusionSurroundingHandler:
    expected_footprint_lat_lon = Polygon(
        [
            (7.522558212280273, 47.375685893433115),
            (7.526248931884766, 47.36219950880962),
            (7.540925979614258, 47.36981508949069),
            (7.522558212280273, 47.375685893433115),
        ]
    )
    expected_footprint_ch = Polygon(
        [
            (2606338.975388542, 1247208.9499421772),
            (2606619.370075448, 1245709.8114741081),
            (2607727.023172711, 1246557.8535303373),
            (2606338.975388542, 1247208.9499421772),
        ]
    )

    @pytest.mark.parametrize(
        "region,expected_exclusion_footprint",
        [
            (REGION.LAT_LON, expected_footprint_lat_lon),
            (REGION.CH, expected_footprint_ch),
        ],
    )
    def test_get_exclusion_footprint(
        self,
        region,
        expected_exclusion_footprint,
        get_manually_created_surroundings_from_db,
    ):
        fake_site_id = -999

        footprint = ManualExclusionSurroundingHandler(
            site_id=fake_site_id, region=region
        ).get_footprint()

        assert footprint == expected_exclusion_footprint
        get_manually_created_surroundings_from_db.assert_called_once_with(
            site_id=fake_site_id
        )


class TestFeatureProviderMixin:
    @pytest.mark.parametrize(
        "surrounding_type, expected_feature_index",
        [
            (ManualSurroundingTypes.BUILDINGS, 0),
            (ManualSurroundingTypes.EXCLUSION_AREA, 1),
        ],
    )
    def test_get_features(
        self,
        get_manually_created_surroundings_from_db,
        manually_created_surroundings,
        surrounding_type,
        expected_feature_index,
    ):
        class FeatureProviderInheritor(FeatureProviderMixin):
            manual_surrounding_type = surrounding_type

        features = FeatureProviderInheritor(
            site_id=-999, region=REGION.LAT_LON
        ).get_features()

        assert features == [
            manually_created_surroundings["features"][expected_feature_index]
        ]
        get_manually_created_surroundings_from_db.assert_called_once_with(site_id=-999)

import fiona
import pytest
from shapely.geometry import Point, box, mapping
from shapely.strtree import STRtree

import surroundings.eu_noise.noise_surrounding_handler
from common_utils.constants import REGION
from surroundings.eu_noise import EUNoiseLevelHandler


class TestEUNoiseSurroundingHandler:
    @pytest.mark.parametrize(
        "db_low, db_high, expected_noise_level",
        [
            (100, 0, 100),
            (0, 100, 50),
        ],
    )
    def test_get_noise_level(self, db_low, db_high, expected_noise_level):
        assert expected_noise_level == EUNoiseLevelHandler._get_noise_level(
            {"properties": {"DB_Low": db_low, "DB_High": db_high}}
        )

    def test_get_noise_areas_and_levels(self, mocker):
        noise_area = box(0, 0, 1, 1)
        mocker.patch.object(
            surroundings.eu_noise.noise_surrounding_handler,
            "download_files_if_not_exists",
            return_value=["fake-file"],
        )
        mocker.patch.object(fiona, "open").return_value.__enter__.return_value = [
            {
                "properties": {"DB_Low": 90, "DB_High": 100},
                "geometry": mapping(noise_area),
            }
        ]

        noise_area_tree, noise_area_levels = EUNoiseLevelHandler(
            region=REGION.EUROPE,  # to avoid projections
            location=Point(0, 0),
            bounding_box_extension=500,
            noise_source_type=mocker.ANY,
            noise_time_type=mocker.ANY,
        )._get_noise_areas_and_levels()

        assert isinstance(noise_area_tree, STRtree)
        assert noise_area_levels == {noise_area.wkb: 95}

    @pytest.mark.parametrize(
        "location, expected_noise_level",
        [
            (Point(0.5, 0.5), 100),
            (Point(1.0, 0.5), 100),
            (Point(1.1, 0.5), 50),
            (Point(2, 2), 0),
            (Point(2000, 2000), 0),
        ],
    )
    def test_get_at(self, location, expected_noise_level, mocker):
        noise_areas = [box(0, 0, 1, 1), box(0.75, 0, 2, 1)]
        noise_areas_tree = STRtree(noise_areas)
        noise_areas_level = {
            noise_areas[0].wkb: 100,
            noise_areas[1].wkb: 50,
        }
        mocker.patch.object(
            EUNoiseLevelHandler,
            "_get_noise_areas_and_levels",
            return_value=(noise_areas_tree, noise_areas_level),
        )

        noise_level = EUNoiseLevelHandler(
            location=Point(0, 0),
            region=REGION.EUROPE,  # to avoid projections
            bounding_box_extension=500,
            noise_source_type=mocker.ANY,
            noise_time_type=mocker.ANY,
        ).get_at(location=location)

        assert noise_level == expected_noise_level

    def test_get_at_projects_from_region_crs_to_dataset_crs(self, mocker):
        location_hamburg_crs = Point(
            -4953645.027432846, -3137628.479475237
        )  # resolves to 0.5, 0.5 in REGION.EUROPE crs

        noise_areas = [box(0, 0, 1, 1)]
        noise_areas_tree = STRtree(noise_areas)
        noise_areas_level = {
            noise_areas[0].wkb: 100,
        }
        mocker.patch.object(
            EUNoiseLevelHandler,
            "_get_noise_areas_and_levels",
            return_value=(noise_areas_tree, noise_areas_level),
        )

        noise_level = EUNoiseLevelHandler(
            location=location_hamburg_crs,
            region=REGION.DE_HAMBURG,
            bounding_box_extension=500,
            noise_source_type=mocker.ANY,
            noise_time_type=mocker.ANY,
        ).get_at(location=location_hamburg_crs)

        assert noise_level == 100

import pytest
from deepdiff import DeepDiff
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box

from brooks.models import SimOpening, SimSeparator
from brooks.types import SeparatorType
from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, REGION
from simulations.noise.noise_sources_levels_generator import (
    EuNoiseSourcesLevelsGenerator,
    GenericNoiseSourcesLevelsGenerator,
    SwisstopoNoiseSourcesLevelsGenerator,
    get_noise_sources,
)
from simulations.noise.utils import (
    aggregate_noises,
    fishnet_split,
    get_opening_sample_location_for_noise,
    get_surrounding_footprints,
)
from surroundings.base_building_handler import Building
from surroundings.eu_noise import EUNoiseLevelHandler, EUNoiseSourceGeometryProvider
from surroundings.manual_surroundings import (
    ManualBuildingSurroundingHandler,
    ManualExclusionSurroundingHandler,
)
from surroundings.osm import OSMBuildingsHandler
from surroundings.swisstopo import (
    SwissTopoBuildingSurroundingHandler,
    SwissTopoNoiseLevelHandler,
)
from surroundings.v2.swisstopo import SwissTopoNoiseSourceGeometryProvider
from tests.utils import random_simulation_version

DUMMY_NOISE_VALUE = {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100}


@pytest.mark.parametrize(
    "linestring_to_split, expected_result",
    [
        (
            LineString([(0, 0), (15, 0), (15, 5), (0, 5)]),
            [
                LineString([(0, 0), (10, 0)]),
                LineString([(10, 0), (15, 0)]),
                LineString([(15, 0), (15, 5), (10, 5)]),
                LineString([(10, 5), (0, 5)]),
            ],
        ),
    ],
)
def test_fishnet_split(linestring_to_split, expected_result):
    res = fishnet_split(geometry=linestring_to_split, col_width=10, row_width=10)
    assert len(res) == 4
    for ls in res:
        assert (
            len([ls for expected_geom in expected_result if ls.equals(expected_geom)])
            == 1
        )


@pytest.mark.parametrize(
    "region, noise_location_provider, noise_surrounding_handler",
    [
        (REGION.CH, SwissTopoNoiseSourceGeometryProvider, SwissTopoNoiseLevelHandler),
        (REGION.DE_HAMBURG, EUNoiseSourceGeometryProvider, EUNoiseLevelHandler),
    ],
)
@pytest.mark.parametrize(
    "noise_source_type",
    [
        NOISE_SOURCE_TYPE.TRAFFIC,
        NOISE_SOURCE_TYPE.TRAIN,
    ],
)
@pytest.mark.parametrize(
    "noise_time",
    [
        NOISE_TIME_TYPE.DAY,
        NOISE_TIME_TYPE.NIGHT,
    ],
)
@pytest.mark.parametrize(
    "source_geometry, exclusion_area, expected_result",
    [
        (
            LineString([(0, 0), (100, 0)]),
            Polygon(),
            [(float(i), 0.0, DUMMY_NOISE_VALUE) for i in range(5, 105, 10)],
        ),
        (
            LineString([(0, 0), (0, 100)]),
            Polygon(),
            [(0.0, float(i), DUMMY_NOISE_VALUE) for i in range(5, 105, 10)],
        ),
        (
            LineString([(0, 0), (100, 100)]),
            Polygon(),
            [(float(i), float(i), DUMMY_NOISE_VALUE) for i in range(5, 105, 10)],
        ),
        (
            LineString([(-500, -500), (500, 500)]),
            Polygon(),
            [(float(i), float(i), DUMMY_NOISE_VALUE) for i in range(-495, 505, 10)],
        ),
        (
            LineString([(-500, -500), (500, 500)]),
            box(-100, -100, 100, 100),
            [
                (float(i), float(i), DUMMY_NOISE_VALUE)
                for i in range(-495, 505, 10)
                if i > 100 or i < -100
            ],
        ),
    ],
)
def test_get_noise_sources(
    region,
    noise_location_provider,
    noise_surrounding_handler,
    noise_source_type,
    noise_time,
    source_geometry,
    exclusion_area,
    expected_result,
    mocker,
):
    mocked_noise_surrounding_handler = mocker.patch.object(
        noise_surrounding_handler,
        "get_at",
        return_value=DUMMY_NOISE_VALUE[NOISE_TIME_TYPE.DAY],
    )
    mocked_noise_location_provider = mocker.patch.object(
        noise_location_provider,
        "get_source_geometries",
        return_value=[source_geometry],
    )
    mocker.patch.object(
        ManualExclusionSurroundingHandler, "get_footprint", return_value=exclusion_area
    )

    noise_sources = [
        (p.x, p.y, z)
        for p, z in get_noise_sources(
            site_id=mocker.ANY,
            location=Point(0, 0),
            bounding_box_extension=500,
            region=region,
            noise_source_type=noise_source_type,
            simulation_version=random_simulation_version(),
        )
    ]

    assert not DeepDiff(
        noise_sources,
        expected_result,
        significant_digits=2,
    )
    mocked_noise_location_provider.assert_called_once_with(
        noise_source_type=noise_source_type
    )
    assert (
        mocked_noise_surrounding_handler.call_count == len(expected_result) * 2
    )  # 1 call per noise time type


def test_get_noise_sources_picks_correct_handler(
    mocker,
):
    mocker.patch.object(
        ManualExclusionSurroundingHandler,
        ManualExclusionSurroundingHandler.get_footprint.__name__,
        return_value=Polygon(),
    )
    mocked_generic = mocker.patch.object(
        GenericNoiseSourcesLevelsGenerator,
        GenericNoiseSourcesLevelsGenerator.generate.__name__,
    )
    mocked_swiss = mocker.patch.object(
        SwisstopoNoiseSourcesLevelsGenerator,
        SwisstopoNoiseSourcesLevelsGenerator.generate.__name__,
    )
    mocked_eu = mocker.patch.object(
        EuNoiseSourcesLevelsGenerator,
        EuNoiseSourcesLevelsGenerator.generate.__name__,
    )
    for region, mock in [
        (REGION.CH, mocked_swiss),
        (REGION.DE_HAMBURG, mocked_eu),
        (REGION.DE_BERLIN, mocked_generic),
    ]:
        get_noise_sources(
            site_id=mocker.ANY,
            location=Point(0, 0),
            bounding_box_extension=500,
            region=region,
            noise_source_type=NOISE_SOURCE_TYPE.TRAFFIC,
            simulation_version=random_simulation_version(),
        )
        mock.assert_called_once()


@pytest.mark.parametrize(
    "region, surrounding_handler",
    [
        (REGION.CH, SwissTopoBuildingSurroundingHandler),
        (REGION.DE_HAMBURG, OSMBuildingsHandler),
    ],
)
def test_get_surrounding_footprints_calls_the_right_building_handler(
    mocker, region, surrounding_handler, overpass_api_mocked
):
    dummy_building_footprints = [box(0, 0, 1, 1)]
    mocked_building_handler = mocker.patch.object(
        surrounding_handler,
        "get_buildings",
        return_value=[
            Building(footprint=building_footprint, geometry=building_footprint)
            for building_footprint in dummy_building_footprints
        ],
    )
    mocker.patch.object(
        ManualBuildingSurroundingHandler, "get_footprint", return_value=Polygon()
    )
    mocker.patch.object(
        ManualExclusionSurroundingHandler, "get_footprint", return_value=Polygon()
    )
    overpass_api_mocked()

    surrounding_footprints = list(
        get_surrounding_footprints(
            site_id=mocker.ANY,
            location=Point(0, 0),
            region=region,
            bounding_box_extension=500,
            simulation_version=random_simulation_version(),
        )
    )

    assert mocked_building_handler.call_count == 1
    assert surrounding_footprints == dummy_building_footprints


@pytest.mark.parametrize(
    "exclusion_polygon, manual_building_footprints, expected_surrounding_footprints",
    [
        (box(0.5, 0, 1.0, 1.0), Polygon(), box(0.0, 0, 0.5, 1.0)),
        (Polygon(), Polygon(), box(0, 0, 1, 1)),
        (box(-1, -1, 2, 2), box(0.5, 0, 1.0, 1.0), box(0.5, 0, 1.0, 1.0)),
        (
            MultiPolygon([box(-1, -1, 2, 2)]),
            box(0.5, 0, 1.0, 1.0),
            box(0.5, 0, 1.0, 1.0),
        ),
        (
            box(-1, -1, 2, 2),
            MultiPolygon([box(0.5, 0, 1.0, 1.0)]),
            box(0.5, 0, 1.0, 1.0),
        ),
    ],
)
def test_get_surrounding_footprints_applies_manual_surroundings(
    mocker,
    exclusion_polygon,
    manual_building_footprints,
    expected_surrounding_footprints,
):
    building_footprints = [box(0, 0, 1, 1)]

    mocked_building_footprints = mocker.patch.object(
        SwissTopoBuildingSurroundingHandler,
        "get_buildings",
        return_value=[
            Building(footprint=building_footprint, geometry=building_footprint)
            for building_footprint in building_footprints
        ],
    )
    mocked_manual_buildings_footprint = mocker.patch.object(
        ManualBuildingSurroundingHandler,
        "get_footprint",
        return_value=manual_building_footprints,
    )
    mocked_exclusion_footprint = mocker.patch.object(
        ManualExclusionSurroundingHandler,
        "get_footprint",
        return_value=exclusion_polygon,
    )

    surrounding_footprints = list(
        get_surrounding_footprints(
            site_id=mocker.ANY,
            location=Point(0, 0),
            region=REGION.CH,
            bounding_box_extension=500,
            simulation_version=random_simulation_version(),
        )
    )

    assert len(surrounding_footprints) == 1
    assert surrounding_footprints[0].equals(expected_surrounding_footprints)
    mocked_building_footprints.assert_called_once_with()
    mocked_manual_buildings_footprint.assert_called_once_with()
    mocked_exclusion_footprint.assert_called_once_with()


@pytest.mark.parametrize(
    "noises_attenuated, expected_total_noise",
    [
        ([], 0),
        ([100], 100),
        ([100] * 2, 103.01),
        ([100] * 100, 119.99),
        ([100, 95], 101.19),
        ([100, 90], 100.41),
    ],
)
def test_aggregate_noises(noises_attenuated, expected_total_noise):
    assert aggregate_noises(noises=noises_attenuated) == pytest.approx(
        expected_total_noise, abs=1e-2
    )


@pytest.mark.parametrize(
    "opening_footprint, footprint_facade, expected",
    [
        (box(0, 0, 1, 1), box(0, 0, 1, 1), (0.5, 0.5, 0.5)),
        (box(0.5, 0.0, 1, 1), box(0, 0, 2, 2), (0.75, -0.227, 0.5)),
        # Window inside the footprint, empty polygon:
        (box(0.5, 0.5, 1, 1), box(0, 0, 2, 2), None),
    ],
)
def test_get_opening_sample_location_for_noise(
    opening_footprint: Polygon, footprint_facade: Polygon, expected
):
    opening = SimOpening(
        footprint=opening_footprint,
        height=(0, 1),
        separator=SimSeparator(
            footprint=opening_footprint, separator_type=SeparatorType.WALL
        ),
        separator_reference_line=LineString(),
    )
    result = get_opening_sample_location_for_noise(
        opening, footprint_facade=footprint_facade
    )
    assert result == pytest.approx(expected, abs=1e-2)

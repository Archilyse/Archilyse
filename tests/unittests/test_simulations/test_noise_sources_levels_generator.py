import random

import pytest
from shapely.geometry import LineString, Point

from brooks.util.projections import project_geometry
from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, REGION
from simulations.noise.noise_sources_levels_generator import (
    GenericNoiseSourcesLevelsGenerator,
)
from surroundings.v2.osm.railways import OSMNoisyRailwayGeometryProvider
from surroundings.v2.osm.streets import OSMNoisyStreetsGeometryProvider
from surroundings.v2.osm.streets.constants import STREET_TYPE_MAPPING
from tests.surroundings_utils import create_fiona_collection

schema = {
    "geometry": "LineString",
    "properties": {"fclass": "str"},
}


@pytest.fixture
def mocked_osm_streets_shapefile(patch_geometry_provider_source_files):
    entities = [
        (
            project_geometry(
                LineString([(2700000.0, 1200000.0), (2700000.0 + i, 1200001.0 + +i)]),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {"fclass": street_type},
        )
        for i, street_type in enumerate(sorted(STREET_TYPE_MAPPING.keys()))
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMNoisyStreetsGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


@pytest.fixture
def mocked_osm_rail_shapefile(patch_geometry_provider_source_files):
    entities = [
        (
            project_geometry(
                LineString([(2700000.0, 1200000.0), (2700000.0 + i, 1200001.0 + +i)]),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {"fclass": "jan_payaso"},
        )
        for i in range(21)
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMNoisyRailwayGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


@pytest.mark.parametrize(
    "noise_source_type, num_points",
    [(NOISE_SOURCE_TYPE.TRAIN, 47), (NOISE_SOURCE_TYPE.TRAFFIC, 46)],
)
def test_generic_noise_sources_level_generator(
    mocked_osm_streets_shapefile,
    mocked_osm_rail_shapefile,
    noise_source_type,
    num_points,
):
    location = Point(2700000.0, 1200000.0)
    generator = GenericNoiseSourcesLevelsGenerator(
        location=location,
        bounding_box_extension=100,
        region=REGION.CH,
        noise_source_type=noise_source_type,
    )
    result = list(generator.generate())
    assert len(result) == num_points
    # check format
    elem_random = random.choice(result)
    assert isinstance(elem_random, tuple)
    assert isinstance(elem_random[0], Point)
    assert set(elem_random[1].keys()) == set(NOISE_TIME_TYPE)
    assert all(isinstance(v, int) for v in elem_random[1].values())

from itertools import combinations

import pygeos
import pytest
import shapely.geos
from requests.exceptions import ConnectionError
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.wkt import loads

from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.constants import (
    SIMULATION_VALUE_TYPE,
    SUN_DIMENSION,
    UNIT_BASICS_DIMENSION,
    VIEW_DIMENSION,
)
from common_utils.exceptions import InvalidShapeException
from common_utils.grouper import Grouper
from handlers.utils import aggregate_stats_dimension, get_simulation_name
from surroundings.utils import get_grid_points


def test_chunks():
    from common_utils.chunker import chunker

    first = list(range(5))
    assert list(chunker(first, size_of_chunk=2)) == [[0, 1], [2, 3], [4]]

    second = []
    assert list(chunker(second, size_of_chunk=1)) == []


@pytest.mark.parametrize(
    "num_exceptions,expected", [(10, ConnectionError), (0, None), (4, None)]
)
def test_apply_decorator_to_all_methods(mocker, monkeypatch, num_exceptions, expected):
    from handlers import gcloud_storage as gcloud_module

    def testing(*args, **kwargs):
        return 0

    mocker.patch.object(gcloud_module.wait_exponential, "__call__", testing)

    mocked_client = mocker.patch.object(
        gcloud_module.GCloudStorageHandler, "client", autospec=True
    )
    if expected is not None:
        gcloud_module.GCloudStorageHandler.client.lookup_bucket.side_effect = [
            expected("")
        ] * num_exceptions
        with pytest.raises(expected):
            gcloud_module.GCloudStorageHandler()._lookup_bucket("test")
    else:
        gcloud_module.GCloudStorageHandler()._lookup_bucket("test")
        assert mocked_client.lookup_bucket.call_count == 1


@pytest.mark.parametrize(
    "data, expected_count",
    [
        ([1, 2, 3], 1),
        ([1, 3, 2], 1),
        ([1, 3, 5], 0),
        ([1, 5, 4, 2, 6], 2),
        ([6, 5, 2, 7, 4, 3], 1),
    ],
)
def test_grouper(data, expected_count):
    grouper = Grouper()
    for a, b in combinations(data, 2):
        if abs(a - b) == 1:
            grouper.link(a, b)
    assert len(grouper.groups) == expected_count


def test_ensure_polygon_validity(invalid_multipolygon):
    assert not invalid_multipolygon.is_valid
    new_geom = ensure_geometry_validity(invalid_multipolygon)
    assert new_geom.is_valid
    assert isinstance(new_geom, Polygon)


@pytest.mark.parametrize(
    "geoms",
    [
        [box(0, 0, 10, 10), box(10.5, 10.5, 10.51, 10.51)],
        [box(0, 0, 10, 10), box(11, 0, 12, 1)],
        [box(0, 0, 10, 10), box(11, 0, 12, 1.5)],
    ],
)
def test_ensure_polygon_validity_multipol_to_pol(geoms):
    multipolygon = MultiPolygon(geoms)
    new_geom = ensure_geometry_validity(multipolygon, force_single_polygon=True)
    assert new_geom.is_valid
    assert isinstance(new_geom, Polygon)


def test_ensure_polygon_validity_multipol_to_pol_raises():
    multipolygon = MultiPolygon([box(0, 0, 10, 10), box(11, 0, 15, 10)])
    with pytest.raises(InvalidShapeException) as e:
        ensure_geometry_validity(multipolygon, force_single_polygon=True)
        assert (
            "Geometry is not valid as it cant be converted to a polygon. Num geoms: 2"
            in str(e.value)
        )


def test_ensure_polygon_validity_multipol_stays_multpol():
    multipolygon = MultiPolygon([box(0, 0, 10, 10), box(10.5, 10.5, 10.51, 10.51)])
    new_geom = ensure_geometry_validity(multipolygon, force_single_polygon=False)
    assert new_geom.is_valid
    assert isinstance(new_geom, MultiPolygon)


def test_ensure_polygon_validity_predicate_error():
    polygon = loads(
        "POLYGON ((8.51316125186 12.02172637225, 8.51316125186 12.02172637225, 8.63880270955 12.02172637225, 8.63880270955 12.32172911544, 8.63880270988 14.84380475257, 8.43780270988 14.8438047526, 5.98284057085 14.84380475254, 5.98284057085 16.80755421315, 8.48689330676 16.80504360328, 8.48689330676 15.59666845926, 8.60689785148 15.59666845926, 10.99177529525 15.59666845923, 10.99177529521 13.50735539055, 11.04177529521 13.50735539055, 11.04177529525 15.58566853553, 11.04177529525 15.59667173697, 11.04177529525 15.59766845923, 11.04177529525 15.64666845923, 8.60689330676 15.64666845926, 8.60689330676 16.80492328905, 12.08299871723 16.80143808109, 12.48225477717 16.28547631848, 12.5613418521 16.34667464018, 12.55950143049 16.34905303157, 14.82604848621 18.21450271355, 16.15256074302 16.57855800153, 14.29571772955 15.07292962896, 13.64391926701 15.85483207984, 13.99520405137 16.12143947028, 13.94683983679 16.18516468309, 13.25389886907 15.65925752356, 13.25302061652 15.66035996368, 13.12787701358 15.56066503582, 13.87595797316 14.62162482012, 13.87595797316 8.82806009325, 13.81595797316 8.82806009325, 13.81595797316 8.78441878597, 6.13284057081 8.78441878606, 6.13284057085 12.02172637225, 8.51316125186 12.02172637225), (8.51316125186 12.02172637225, 8.48694708589 11.97914917762, 9.20621491248 11.53630632832, 10.04243156772 11.33561433106, 10.05297221462 11.37952447221, 10.05487666129 11.37945411994, 10.06214882605 11.3348859547, 10.84090614357 11.46191729018, 10.83432579637 11.50232696897, 10.83742854091 11.50344678868, 10.85817205628 11.46814877629, 11.56099101035 11.8809154636, 12.02638280614 12.40941722592, 12.31395955427 13.14826825572, 12.27553182949 13.163236591, 12.27612348674 13.16638788304, 12.3173635277 13.16639854064, 12.3173635277 13.50735539055, 11.57876123665 13.50735539055, 11.57876123669 14.44512078259, 11.52876123669 14.44512078259, 11.52876123665 13.51835542551, 11.52876123665 13.50735896665, 11.52876123665 13.50635539055, 11.52876123665 13.45735539054, 12.2673635277 13.45735539054, 12.2673635277 13.16640138332, 11.98300190403 12.4358107502, 11.52876123665 11.91997227732, 10.83285354785 11.51126458708, 10.05409970563 11.38423381849, 9.22563817135 11.58306458672, 8.51316125186 12.02172637225))"
    )
    new_geom = ensure_geometry_validity(polygon, force_single_polygon=False)
    assert new_geom.is_valid


def test_get_grid_points():
    bounding_box = box(0, 0, 1000, 1000)
    points = list(get_grid_points(bounding_box=bounding_box, interval=500))
    assert len(points) == 9


@pytest.mark.parametrize(
    "unit_stats, expected_result",
    [
        (
            [{"min": 1, "max": 100, "count": 2, "mean": 50.5, "stddev": 49.5}],
            {"min": 1, "max": 100, "count": 2, "mean": 50.5, "stddev": 49.5},
        ),
        (
            [],
            {"min": 0, "max": 0, "count": 0, "mean": 0, "stddev": 0},
        ),
        (
            [
                {"min": 0, "max": 100, "count": 2, "mean": 50, "stddev": 50},
                {"min": 1000, "max": 2000, "count": 2, "mean": 1500, "stddev": 500},
            ],
            {"min": 0, "max": 2000, "mean": 775, "stddev": 807.3877631, "count": 4},
        ),
    ],
)
def test_aggregate_unit_stats_dimension(unit_stats, expected_result):
    assert aggregate_stats_dimension(stats=unit_stats) == pytest.approx(
        expected_result, rel=1e-2
    )


def test_get_simulation_name(unit_vector_with_balcony):
    for sim_name in (
        get_simulation_name(sim_dimension, value_type)
        for sim_type in [SUN_DIMENSION, VIEW_DIMENSION, UNIT_BASICS_DIMENSION]
        for sim_dimension in sim_type
        for value_type in SIMULATION_VALUE_TYPE
    ):
        assert sim_name in unit_vector_with_balcony[0]


def test_pygeos_shapely_compatible():
    assert shapely.geos.geos_version_string == pygeos.io.geos_capi_version_string

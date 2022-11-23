import pytest
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SIMULATION_VERSION
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.constants import BOUNDING_BOX_EXTENSION_GROUNDS
from surroundings.osm import (
    OSMBuildingsHandler,
    OSMForestHandler,
    OSMLakesHandler,
    OSMParksHandler,
    OSMRailwayHandler,
    OSMRiversHandler,
    OSMRiversPolygonsHandler,
    OSMSeaHandler,
    OSMStreetHandler,
    OSMTreesHandler,
)
from surroundings.raster_window_triangulator import RasterWindowTriangulator
from surroundings.srtm import SRTMElevationHandler
from surroundings.surrounding_handler import (
    ManualSurroundingsHandler,
    OSMSurroundingHandler,
)
from surroundings.swisstopo import SwisstopoElevationHandler


@pytest.mark.parametrize("site_id", [999, None])
@pytest.mark.parametrize(
    "lat,lon,region,expected_elevation_handler",
    [
        (47.349433, 8.492015, REGION.CH, SwisstopoElevationHandler),
        (50.05332, 14.34838, REGION.CZ, SRTMElevationHandler),
        (1.3639176, 103.842882, REGION.SG, SRTMElevationHandler),
        (56.1738767, 9.5566292, REGION.DK, ZeroElevationHandler),
    ],
)
def test_generate_view_surroundings(
    mocker,
    lat,
    lon,
    region,
    expected_elevation_handler,
    overpass_api_mocked,
    mocked_gcp_download,
    site_id,
):
    import surroundings.surrounding_handler as surrounding_handler_module

    region_crs_location = project_geometry(
        geometry=Point(lon, lat),
        crs_from=REGION.LAT_LON,
        crs_to=region,
    )

    raster_spy = mocker.spy(OSMSurroundingHandler, "_get_raster_grid")
    elevation_handler_spy = mocker.spy(OSMSurroundingHandler, "_get_elevation_handler")

    mocker.patch.object(
        RasterWindowTriangulator,
        "create_triangles",
        return_value=[Polygon([[0, 0, 0], [2, 1, 1], [0.5, 2, 2]])],
    )
    apply_manual_adjustments_mock = mocker.patch.object(
        ManualSurroundingsHandler, "apply_manual_adjustments", return_value=[]
    )
    surrounding_handler_mocks = [
        mocker.patch.object(surrounding_handler_module, surrounding_handler.__name__)
        for surrounding_handler in (
            OSMBuildingsHandler,
            OSMForestHandler,
            OSMParksHandler,
            OSMRailwayHandler,
            OSMSeaHandler,
            OSMStreetHandler,
            OSMTreesHandler,
            OSMLakesHandler,
            OSMRiversPolygonsHandler,
            OSMRiversHandler,
        )
    ]

    standard_args = dict(
        region=region,
        location=region_crs_location,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        bounding_box_extension=100,
    )

    list(
        OSMSurroundingHandler.generate_view_surroundings(
            **standard_args,
            site_id=site_id,
            building_footprints=[],
        )
    )

    elevation_handler_spy.assert_called_once_with(**standard_args)
    assert isinstance(elevation_handler_spy.spy_return, expected_elevation_handler)

    raster_spy.assert_called_once_with(**standard_args)

    for handler_mock in surrounding_handler_mocks:
        handler_mock.assert_called_once_with(
            **standard_args,
            raster_grid=raster_spy.spy_return,
            elevation_handler=elevation_handler_spy.spy_return,
        )
        handler_mock().get_triangles.assert_called_once()

    if site_id:
        apply_manual_adjustments_mock.assert_called_once()


@pytest.mark.parametrize(
    "region,should_yield_raster_grid",
    [
        (REGION.CH, True),
        (REGION.DE_HAMBURG, True),
        (REGION.MC, False),
    ],
)
def test_get_raster_grid(region, should_yield_raster_grid, mocker):
    mocker.patch.object(
        RasterWindowTriangulator,
        RasterWindowTriangulator.create_triangles.__name__,
        return_value=[Polygon([(0, 0, 0), (1, 0, 0), (1, 1, 0)])],
    )
    raster_grid = OSMSurroundingHandler._get_raster_grid(
        region=region,
        location=Point(0, 0),
        simulation_version=SIMULATION_VERSION.PH_2022_H1,
    )
    if should_yield_raster_grid:
        assert isinstance(raster_grid, STRtree)
    else:
        assert raster_grid is None


@pytest.mark.parametrize(
    "bounding_box_extension, expected_bounding_box_extension",
    [(None, BOUNDING_BOX_EXTENSION_GROUNDS), (1000, 1000)],
)
def test_get_elevation_handler_defaults_to_grounds_bounding_box_extension(
    mocker, bounding_box_extension, expected_bounding_box_extension
):
    import surroundings.surrounding_handler

    fake_location = Point(0, 0)

    get_elevation_handler_spy = mocker.spy(
        surroundings.surrounding_handler,
        surroundings.surrounding_handler.get_elevation_handler.__name__,
    )

    common_args = dict(
        region=REGION.CH,
        location=fake_location,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
    )

    OSMSurroundingHandler._get_elevation_handler(
        **common_args,
        bounding_box_extension=bounding_box_extension,
    )

    get_elevation_handler_spy.assert_called_once_with(
        **common_args, bounding_box_extension=expected_bounding_box_extension
    )

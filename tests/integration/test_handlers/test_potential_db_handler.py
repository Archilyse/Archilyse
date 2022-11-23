import pytest
from shapely.affinity import translate

from brooks.util.projections import project_geometry
from common_utils.constants import (
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
)
from common_utils.exceptions import DBMultipleResultsException, DBNotFoundException
from handlers.db import PotentialSimulationDBHandler

FLOOR_NUMBER = 1


@pytest.fixture
def simulations(building_footprints_as_wkts):
    sims = []
    for building_footprint in building_footprints_as_wkts[:2]:
        projected_building_lat_lon = project_geometry(
            geometry=building_footprint.geoms[0],
            crs_from=REGION.CH,
            crs_to=REGION.LAT_LON,
        )
        db_sim = PotentialSimulationDBHandler.add(
            floor_number=FLOOR_NUMBER,
            type=SIMULATION_TYPE.VIEW,
            status=POTENTIAL_SIMULATION_STATUS.SUCCESS,
            result={},
            region=REGION.CH.name,
            layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
            simulation_version=SIMULATION_VERSION.PH_01_2021,
            building_footprint=projected_building_lat_lon,
        )
        lon = projected_building_lat_lon.centroid.x
        lat = projected_building_lat_lon.centroid.y
        sims.append({"id": db_sim["id"], "lat": lat, "lon": lon})

    return sims


@pytest.fixture
def overlapping_simulations(building_footprints_as_wkts):
    TRANSLATION = 0.01
    common_params = dict(
        floor_number=FLOOR_NUMBER,
        type=SIMULATION_TYPE.VIEW,
        status=POTENTIAL_SIMULATION_STATUS.SUCCESS,
        result={},
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
    )

    building_footprint = building_footprints_as_wkts[0].geoms[0]

    lat_lon_footprint = project_geometry(
        geometry=building_footprint,
        crs_from=REGION.CH,
        crs_to=REGION.LAT_LON,
    )
    lat_lon = lat_lon_footprint.representative_point()

    db_sim1 = PotentialSimulationDBHandler.add(
        building_footprint=lat_lon_footprint,
        **common_params,
    )

    # We move the second simulation slightly away from the first one, but footprints overlaps
    lat_lon_footprint = project_geometry(
        geometry=translate(building_footprint, xoff=TRANSLATION, yoff=TRANSLATION),
        crs_from=REGION.CH,
        crs_to=REGION.LAT_LON,
    )
    lat_lon2 = lat_lon_footprint.representative_point()

    db_sim2 = PotentialSimulationDBHandler.add(
        building_footprint=lat_lon_footprint,
        **common_params,
    )
    return (
        {"lat": lat_lon.y, "lon": lat_lon.x, "id": db_sim1["id"]},
        {"lat": lat_lon2.y, "lon": lat_lon2.x, "id": db_sim2["id"]},
    )


def test_get_by_location_picks_correct_simulation_by_building_footprint(simulations):
    for sim in simulations:
        lat = sim["lat"]
        lon = sim["lon"]
        result = PotentialSimulationDBHandler.get_by_location(
            lat=lat, lon=lon, floor_number=FLOOR_NUMBER, sim_type=SIMULATION_TYPE.VIEW
        )
        assert result["id"] == sim["id"]


def test_get_by_location_does_not_match_raises_exception(simulations):
    lat = simulations[0]["lat"]
    lon = simulations[0]["lon"]
    with pytest.raises(DBNotFoundException):
        PotentialSimulationDBHandler.get_by_location(
            lat=lat,
            lon=lon,
            floor_number=FLOOR_NUMBER + 2,  # Floor number does not match
            sim_type=SIMULATION_TYPE.VIEW,
        )


def test_get_by_location_match_many(overlapping_simulations):
    for sim in overlapping_simulations:
        lat = sim["lat"]
        lon = sim["lon"]
        with pytest.raises(DBMultipleResultsException):
            PotentialSimulationDBHandler.get_by_location(
                lat=lat,
                lon=lon,
                floor_number=FLOOR_NUMBER,
                sim_type=SIMULATION_TYPE.VIEW,
            )

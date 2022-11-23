import uuid

from shapely.geometry import Point
from tqdm import tqdm

from brooks.util.projections import project_geometry
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    POTENTIAL_LAYOUT_MODE,
    REGION,
    SIMULATION_TYPE,
)
from handlers import PlanHandler
from handlers.db import (
    FloorDBHandler,
    PlanDBHandler,
    PotentialSimulationDBHandler,
    SiteDBHandler,
)
from tasks.potential_view_tasks import potential_simulation_task

ARCHILYSE_API_USER_ID = 2


def run_all_sites():
    sites = [
        s["id"]
        for s in SiteDBHandler.find(
            client_id=1, pipeline_and_qa_complete=True, output_columns=["id"]
        )
    ]
    plans = [
        p["id"] for p in PlanDBHandler.find_in(site_id=sites, output_columns=["id"])
    ]

    for plan_id in tqdm(plans):
        georeferenced_layout_footprint = PlanHandler(
            plan_id=plan_id
        ).get_georeferenced_footprint()

        for floor in FloorDBHandler.find(
            plan_id=plan_id, output_columns=["floor_number"]
        ):
            if floor["floor_number"] >= 0:
                run_location(
                    georeferenced_layout_footprint.centroid,
                    floor["floor_number"],
                    plan_id,
                )


def run_location(lv95_location: Point, floor_number: int, plan_id):
    lat_lon = project_geometry(
        geometry=lv95_location,
        crs_to=REGION.LAT_LON,
        crs_from=REGION.CH,
    )
    location = dict(lat=lat_lon.x, lon=lat_lon.y, floor_number=floor_number)
    for simulation_type in [SIMULATION_TYPE.SUN, SIMULATION_TYPE.VIEW]:
        add_simulation(
            location=location,
            plan_id=plan_id,
            floor_number=floor_number,
            simulation_type=simulation_type,
        )


def add_simulation(
    location: dict, plan_id: int, floor_number: int, simulation_type: SIMULATION_TYPE
):
    simulation_identifier = (
        f"SL_POTENTIAL_{plan_id}_{floor_number}_{simulation_type.name}"
    )

    # check simulation is not already existing unless failed
    simulation = PotentialSimulationDBHandler.find(identifier=simulation_identifier)
    if simulation and simulation[0]["status"] != ADMIN_SIM_STATUS.FAILURE.value:
        return

    potential_simulation_task.delay(
        location=location,
        task_id=str(uuid.uuid4()),
        simulation_type=simulation_type,
        user_id=ARCHILYSE_API_USER_ID,
        identifier=simulation_identifier,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS.name,
    )


if __name__ == "__main__":
    run_all_sites()

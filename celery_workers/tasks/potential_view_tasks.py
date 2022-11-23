import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Tuple

from celery import Task, group
from shapely import wkt
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from brooks.models.layout import PRECISION_UNARY_UNION
from brooks.util.geometry_ops import (
    buffer_n_rounded,
    get_polygons,
    remove_small_holes_from_polygon,
    safe_simplify,
)
from brooks.util.projections import project_geometry
from common_utils.constants import (
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_POTENTIAL_DATASET,
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
)
from handlers import PotentialSimulationHandler
from handlers.db import PotentialSimulationDBHandler
from handlers.quavis import PotentialViewQuavisHandler
from surroundings.base_building_handler import Building
from surroundings.base_entity_surrounding_handler import BaseEntitySurroundingHandler
from surroundings.swisstopo import SwissTopoBuildingSurroundingHandler
from tasks.quavis_tasks import run_quavis_task
from tasks.surroundings_tasks import generate_surroundings_for_potential_task
from tasks.utils.constants import CELERY_MAX_RETRIES, CELERY_RETRYBACKOFF
from tasks.utils.utils import celery_retry_task
from workers_config.celery_app import celery_app

SIMULATION_TYPES_TO_RUN = {SIMULATION_TYPE.SUN, SIMULATION_TYPE.VIEW}
MIN_BUILDING_AREA = 10  # m²


@celery_retry_task()
def potential_simulate_area(
    self,
    lat: float,
    lon: float,
    bounding_box_extension: float,
):
    """Simulates a given area, with SWISSTOPO and PH_2022_H1 sim version"""
    # Todo extend to any surr handler

    from handlers.geo_location import GeoLocator

    region = GeoLocator.get_region_from_lat_lon(lat=lat, lon=lon)

    projected_simulation_location = project_geometry(
        geometry=Point(lon, lat),
        crs_from=REGION.LAT_LON,
        crs_to=region,
    )
    building_handler = SwissTopoBuildingSurroundingHandler(
        location=projected_simulation_location,
        simulation_version=SIMULATION_VERSION.PH_2022_H1,
        bounding_box_extension=bounding_box_extension + 200,
    )

    buildings = list(building_handler.get_buildings())

    for building_footprint in get_building_footprints_to_simulate(
        location=projected_simulation_location,
        bounding_box_extension=bounding_box_extension,
        buildings=buildings,
    ):
        number_of_floors = (
            PotentialSimulationHandler.get_building_floor_count_estimation(
                target_building_footprint=building_footprint, buildings=buildings
            )
        )
        get_full_potential_chain_for_building_footprint(
            building_footprint=building_footprint, number_of_floors=number_of_floors
        ).delay()


def get_building_footprints_to_simulate(
    location: Point, bounding_box_extension: float, buildings: list[Building]
) -> Iterable[Polygon]:
    buildings_footprints = unary_union(
        [
            buffer_n_rounded(
                building.footprint,
                buffer=0.001,
                precision=PRECISION_UNARY_UNION,
            )
            for building in buildings
        ]
    )
    area_of_interest = BaseEntitySurroundingHandler.get_surroundings_bounding_box(
        location=location,
        bounding_box_extension=bounding_box_extension,
    )
    for building_footprint in get_polygons(buildings_footprints):
        if building_footprint.area < MIN_BUILDING_AREA:
            continue
        intersection_area = building_footprint.intersection(area_of_interest).area
        if intersection_area / building_footprint.area > 0.5:
            if bool(building_footprint.interiors):
                building_footprint = remove_small_holes_from_polygon(
                    polygon=building_footprint
                )

            yield safe_simplify(building_footprint)


def get_full_potential_chain_for_building_footprint(
    building_footprint: Polygon,
    number_of_floors: int,
    region: REGION = REGION.CH,
    surrounding_source: SURROUNDING_SOURCES = SURROUNDING_SOURCES.SWISSTOPO,
):
    """building and buildings_footprint projected to regional coords"""
    building_footprint_lat_lon = project_geometry(
        geometry=building_footprint, crs_from=region, crs_to=REGION.LAT_LON
    )

    simulation_ids = [
        PotentialSimulationDBHandler.add(
            type=sim_type,
            building_footprint=building_footprint_lat_lon,
            floor_number=floor_number,
            layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
            status=POTENTIAL_SIMULATION_STATUS.PENDING,
            simulation_version=SIMULATION_VERSION.PH_2022_H1,
            source_surr=surrounding_source,
            region=region.name,
        )["id"]
        for sim_type in SIMULATION_TYPES_TO_RUN
        for floor_number in range(number_of_floors)
    ]

    return generate_surroundings_for_potential_task.si(
        region=region.name,
        source_surr=surrounding_source.value,
        simulation_version=SIMULATION_VERSION.PH_2022_H1.value,
        building_footprint_lat_lon=building_footprint_lat_lon.wkt,
    ) | group(
        *[
            get_potential_quavis_simulation_chain(simulation_id=simulation_id)
            for simulation_id in simulation_ids
        ]
    )


def get_potential_quavis_simulation_chain(simulation_id: int):
    """Needs surroundings already uploaded"""
    potential_simulation_chain = (
        configure_quavis_potential_task.si(simulation_id=simulation_id)
        | run_quavis_task.si(run_id=simulation_id)
        | store_quavis_results_potential_task.si(simulation_id=simulation_id)
        | delete_potential_simulation_artifacts.si(simulation_id=simulation_id)
    ).on_error(potential_results_failure.s(simulation_id=simulation_id))
    return potential_simulation_chain


@celery_app.task()
def potential_results_failure(request, exc, traceback, simulation_id, **kwargs):
    """Changes the status of the simulation at the end of the chain"""
    from handlers.db import PotentialSimulationDBHandler

    result = {"msg": str(exc), "code": exc.__class__.__name__}
    PotentialSimulationDBHandler.update(
        item_pks=dict(id=simulation_id),
        new_values=dict(status=POTENTIAL_SIMULATION_STATUS.FAILURE, result=result),
    )


@celery_retry_task()
def configure_quavis_potential_task(self, simulation_id: int):
    from handlers.db import PotentialSimulationDBHandler
    from handlers.quavis import QuavisGCPHandler

    simulation = PotentialSimulationDBHandler.update(
        item_pks=dict(id=simulation_id),
        new_values=dict(status=POTENTIAL_SIMULATION_STATUS.PROCESSING),
    )

    (
        _,
        obs_height,
        obs_times,
    ) = PotentialSimulationHandler.get_obs_times_height_dimensions_for_sim(
        simulation=simulation
    )

    quavis_input = PotentialViewQuavisHandler.get_quavis_input(
        entity_info=simulation,
        grid_resolution=DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=obs_height,
        datetimes=obs_times,
        simulation_version=SIMULATION_VERSION(simulation["simulation_version"]),
    )
    QuavisGCPHandler.upload_quavis_input(
        run_id=simulation_id, quavis_input=quavis_input
    )

    return simulation_id


class PotentialStoreTask(Task):
    def apply_async(self, *args, **kwargs):
        kwargs.pop("priority", None)
        return super().apply_async(
            *args, **kwargs, priority=celery_app.conf["task_queue_max_priority"]
        )


@celery_app.task(
    base=PotentialStoreTask,
    bind=True,
    retry_backoff=CELERY_RETRYBACKOFF,
    retry_kwargs={"max_retries": CELERY_MAX_RETRIES},
)
def store_quavis_results_potential_task(self, simulation_id: int):
    from handlers.db import PotentialSimulationDBHandler
    from handlers.quavis import QuavisGCPHandler

    simulation = PotentialSimulationDBHandler.get_by(id=simulation_id)

    (
        dimensions,
        obs_height,
        obs_times,
    ) = PotentialSimulationHandler.get_obs_times_height_dimensions_for_sim(
        simulation=simulation
    )

    simulation_results = PotentialViewQuavisHandler.get_quavis_results(
        entity_info=simulation,
        quavis_input=QuavisGCPHandler.get_quavis_input(run_id=simulation_id),
        quavis_output=QuavisGCPHandler.get_quavis_output(run_id=simulation_id),
        grid_resolution=DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=obs_height,
        datetimes=obs_times,
        simulation_version=SIMULATION_VERSION(simulation["simulation_version"]),
    )

    formatted_results = PotentialSimulationHandler.format_view_sun_raw_results(
        view_sun_raw_results=simulation_results,
        dimensions=dimensions,
        simulation_region=REGION[simulation["region"]],
    )
    PotentialSimulationDBHandler.update(
        item_pks=dict(id=simulation_id),
        new_values=dict(
            result=formatted_results, status=POTENTIAL_SIMULATION_STATUS.SUCCESS
        ),
    )


@celery_retry_task()
def delete_potential_simulation_artifacts(self, simulation_id: int):
    from handlers.quavis import QuavisGCPHandler

    QuavisGCPHandler.delete_simulation_artifacts(run_id=simulation_id)


@celery_retry_task()
def generate_potential_tile(
    self, tile_bounds: Tuple[float, float, float, float], dump_shape: str
):
    from handlers.gcloud_storage import GCloudStorageHandler
    from handlers.simulations.potential_tile_exporter import PotentialTileExporter

    storage_handler = GCloudStorageHandler()

    with TemporaryDirectory() as temp_dir:
        directory = Path(temp_dir)
        PotentialTileExporter.dump_to_vector_tile(
            directory=directory,
            dump_shape=wkt.loads(dump_shape),
            tile_bounds=tile_bounds,
        )
        for file in directory.iterdir():
            zipped_file = file.with_suffix(".zip")
            with zipfile.ZipFile(zipped_file, "w", zipfile.ZIP_DEFLATED) as zipy:
                zipy.write(filename=file)

            storage_handler.upload_file_to_bucket(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                destination_folder=GOOGLE_CLOUD_POTENTIAL_DATASET,
                local_file_path=zipped_file,
            )

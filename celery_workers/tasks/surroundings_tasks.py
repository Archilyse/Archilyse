from pathlib import Path

from shapely import wkt

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    REGION,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
    TASK_READY_STATES,
    PipelineCompletedCriteria,
)
from common_utils.exceptions import (
    DependenciesUnMetSimulationException,
    TaskAlreadyRunningException,
)
from tasks.utils.utils import celery_retry_task
from workers_config.celery_app import celery_app


@celery_retry_task
def generate_surroundings_for_view_analysis_task(self, site_id: int):
    """Task that generates the surroundings required for the view simulation for a specific site id
    and upload the results serialized into GCP.

    Args:
        site_id: Id of site
    """
    from handlers import SiteHandler

    SiteHandler.upload_view_surroundings(site_id=site_id)


@celery_retry_task
def generate_surroundings_for_potential_task(
    self,
    region: str,
    source_surr: str,
    simulation_version: str,
    building_footprint_lat_lon: str,
):
    """Task that generates the surroundings required for the potential simulation
    and upload the results serialized into GCP.
    """
    from handlers import PotentialSimulationHandler

    triangles = PotentialSimulationHandler.generate_view_surroundings(
        region=REGION[region],
        source_surr=SURROUNDING_SOURCES[source_surr],
        simulation_version=SIMULATION_VERSION[simulation_version],
        building_footprint_lat_lon=wkt.loads(building_footprint_lat_lon),
    )
    path = PotentialSimulationHandler.get_surroundings_path(
        region=REGION[region],
        source_surr=SURROUNDING_SOURCES[source_surr],
        simulation_version=SIMULATION_VERSION[simulation_version],
        building_footprint_wkt=building_footprint_lat_lon,
    )
    PotentialSimulationHandler.upload_view_surroundings(triangles=triangles, path=path)


@celery_retry_task
def generate_geo_referencing_surroundings_for_site_task(self, site_id: int):
    """Task that generates the surroundings required for the georeferencing gui for a specific site id
    and upload the results serialized into GCP.

    Args:
        site_id: Id of site
    """

    from handlers import SiteHandler

    SiteHandler.generate_georeferencing_surroundings_slam(site_id=site_id)


def enqueue_sample_surroundings_task(site_id: int):
    from handlers.db import SiteDBHandler
    from tasks.workflow_tasks import WorkflowGenerator

    if not sample_surr_check_can_run(site_id=site_id):
        raise DependenciesUnMetSimulationException(
            f"Pipeline not completed for all plans for site {site_id}"
        )

    SiteDBHandler.update(
        item_pks={"id": site_id},
        new_values={
            "sample_surr_task_state": ADMIN_SIM_STATUS.PENDING.value,
        },
    )

    chain = WorkflowGenerator(site_id=site_id).get_sample_surr_generation_chain()
    chain = chain.on_error(sample_surr_error.s(site_id=site_id))
    chain.delay()


@celery_retry_task
def generate_sample_surroundings_for_view_analysis_task(self, site_id: int):
    """Task that generates the surroundings in a smaller bounding box and uploads html results to gcp

    Args:
        site_id: Id of site
    """
    from tempfile import NamedTemporaryFile

    from common_utils.constants import (
        GOOGLE_CLOUD_BUCKET,
        GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS,
        SIMULATION_VERSION,
    )
    from handlers import GCloudStorageHandler, SiteHandler
    from handlers.db import SiteDBHandler
    from handlers.quavis import SLAMQuavisHandler
    from surroundings.visualization.sourroundings_3d_figure import (
        create_3d_surroundings_from_triangles_per_type,
    )

    site_info = SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(sample_surr_task_state=ADMIN_SIM_STATUS.PROCESSING.value),
    )

    triangles_per_surroundings_type = SiteHandler.generate_view_surroundings(
        site_info=site_info, sample=True
    )
    triangles_per_layout = SLAMQuavisHandler().get_site_triangles(
        entity_info=site_info,
        simulation_version=SIMULATION_VERSION(site_info["simulation_version"]),
    )
    with NamedTemporaryFile("wb", suffix=".html") as temp_file:
        create_3d_surroundings_from_triangles_per_type(
            triangles_per_layout=triangles_per_layout,
            triangles_per_surroundings_type=triangles_per_surroundings_type,
            filename=temp_file.name,
            auto_open=False,
        )

        GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_folder=GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS,
            local_file_path=Path(temp_file.name),
            destination_file_name=SiteHandler.get_surroundings_sample_path(
                site_id=site_id
            ),
        )

    site_info = SiteDBHandler.get_by(
        id=site_id, output_columns=["sample_surr_task_state"]
    )
    if site_info["sample_surr_task_state"] == ADMIN_SIM_STATUS.PROCESSING.value:
        # Otherwise Pipeline/Site was modified during process and we discard this result
        # TODO make this properly as this allow more than one task running
        SiteDBHandler.update(
            item_pks=dict(id=site_id),
            new_values=dict(sample_surr_task_state=ADMIN_SIM_STATUS.SUCCESS.value),
        )


def sample_surr_check_can_run(site_id: int):
    from handlers import SiteHandler
    from handlers.db import SiteDBHandler

    site_info = SiteDBHandler.get_by(id=site_id)

    if site_info["sample_surr_task_state"] not in TASK_READY_STATES:
        raise TaskAlreadyRunningException

    site_criteria: PipelineCompletedCriteria = SiteHandler.pipeline_completed_criteria(
        site_id=site_id
    )
    if not site_criteria.ok:
        return False

    return True


@celery_app.task
def sample_surr_error(*args, site_id, **kwargs):
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(sample_surr_task_state=ADMIN_SIM_STATUS.FAILURE.value),
    )

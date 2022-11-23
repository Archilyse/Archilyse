import json
from functools import cached_property
from os import environ
from time import sleep, time
from typing import Set, Tuple, Type

from celery import Task, chain, group
from celery.canvas import Signature, _chain, chord

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    TASK_READY_STATES,
    TASK_TYPE,
    UNIT_USAGE,
    PipelineCompletedCriteria,
)
from common_utils.exceptions import (
    DependenciesUnMetSimulationException,
    TaskAlreadyRunningException,
)
from common_utils.logger import logger
from handlers.db.unit_handler import UnitDBHandler
from tasks.basic_features import run_basic_features_task, run_unit_types_task
from tasks.clustering_units_tasks import clustering_units_task
from tasks.competition_features_tasks import competition_features_calculation_task
from tasks.connectivity_tasks import connectivity_simulation_task
from tasks.deliverables_tasks import (
    generate_building_triangulation_task,
    generate_dwg_floor_task,
    generate_dxf_floor_task,
    generate_energy_reference_area_task,
    generate_ifc_file_task,
    generate_pngs_and_pdfs_for_floor_task,
    generate_unit_plots_task,
    generate_unit_pngs_and_pdfs,
    generate_vector_files_task,
    task_site_zip_deliverable,
)
from tasks.noise_tasks import noise_simulation_task, noise_windows_simulation_task
from tasks.post_simulations_validations import validate_simulations_task
from tasks.qa_validation_tasks import (
    qa_validation_task_failure,
    qa_validation_task_processing,
    run_qa_validation_task,
)
from tasks.quavis_tasks import run_quavis_task
from tasks.rectangulator_tasks import biggest_rectangle_task
from tasks.simulations_tasks import (
    configure_quavis_task,
    configure_sun_v2_quavis_task,
    delete_simulation_artifacts,
    register_simulation,
    run_buildings_elevation_task,
    simulation_error,
    simulation_success,
    store_quavis_results_task,
    store_sun_v2_quavis_results_task,
    update_site_location_task,
)
from tasks.surroundings_tasks import (
    generate_sample_surroundings_for_view_analysis_task,
    generate_surroundings_for_view_analysis_task,
)
from tasks.utils.constants import CELERY_MAX_RETRIES, CELERY_RETRYBACKOFF
from tasks.utils.utils import celery_retry_task, create_run_id
from workers_config.celery_app import celery_app
from workers_config.celery_config import INCREASED_TASK_PRIORITY, redis_conn_config

Canvas = Type[Signature | chord | chain]


def contains_parallelism(canvas: Canvas) -> bool:
    if isinstance(canvas, _chain):
        for task in canvas.tasks:
            return contains_parallelism(task)
    return isinstance(canvas, (chord, group))


def preprocessor_is_chord(parent_canvas: Canvas) -> bool:
    if isinstance(parent_canvas, _chain):
        return preprocessor_is_chord(parent_canvas.tasks[-1])
    return isinstance(parent_canvas, chord)


def workflow(
    *signatures: Canvas,
    run_in_parallel: bool = False,
    on_error: Signature = None,
) -> Canvas:
    """
    This factory method is supposed to hide all complexities of combining celery tasks and/or canvas.
    Use this method to create workflows instead of celery.canvas.chain group chord etc. and/or pipe operators.
    """
    if run_in_parallel:
        if any(map(contains_parallelism, signatures)):
            raise Exception("No nested parallelism please!")
        job = group(signatures) | empty_task.s()

    else:
        job = signatures[0]
        for si in signatures[1:]:
            if preprocessor_is_chord(job):
                # This is a trick:
                # Using chain() prevents to append to the chord's body - this is required as chords with body's
                # containing chains or chords have exceptions outside the chord's body when using an on error callback
                job |= chain(
                    empty_task.s(),
                )
            job |= si

    if on_error:
        job.on_error(on_error)

    return job


class DigitizeAnalyzeTask(Task):
    def delay(self, **kwargs):
        from handlers import QAHandler, SiteHandler
        from handlers.db import SiteDBHandler

        site_id = kwargs["site_id"]
        site_info = SiteDBHandler.get_by(id=site_id)
        if site_info["full_slam_results"] not in TASK_READY_STATES:
            raise TaskAlreadyRunningException
        site_criteria: PipelineCompletedCriteria = (
            SiteHandler.pipeline_completed_criteria(site_id=site_id)
        )
        qa_handler = QAHandler(site_id=site_id)
        plans_wo_floors: Set[int] = qa_handler.plans_wo_floors()
        buildings_wo_plans: Set[int] = qa_handler.buildings_wo_plans()
        site_wo_buildings: list[int] = qa_handler.site_wo_buildings()
        if (
            not site_criteria.ok
            or site_info["pipeline_and_qa_complete"] is False
            or plans_wo_floors
            or buildings_wo_plans
            or site_wo_buildings
        ):
            errors = {
                "pipeline_issues": str(site_criteria),
                "qa_done": site_info["pipeline_and_qa_complete"],
                "plans_wo_floors": plans_wo_floors,
                "buildings_wo_plans": buildings_wo_plans,
                "site_wo_buildings": site_wo_buildings,
            }
            raise DependenciesUnMetSimulationException(str(errors))

        SiteDBHandler.update(
            item_pks={"id": kwargs["site_id"]},
            new_values={
                "full_slam_results": ADMIN_SIM_STATUS.PENDING.value,
                "heatmaps_qa_complete": False,
            },
        )
        return super().delay(**kwargs)

    def __call__(self, *args, **kwargs):
        from handlers.db import SiteDBHandler

        SiteDBHandler.update(
            item_pks=dict(id=kwargs["site_id"]),
            new_values=dict(full_slam_results=ADMIN_SIM_STATUS.PROCESSING.value),
        )
        super().__call__(*args, **kwargs)


@celery_app.task(
    base=DigitizeAnalyzeTask,
    bind=True,
    retry_backoff=CELERY_RETRYBACKOFF,
    retry_kwargs={"max_retries": CELERY_MAX_RETRIES},
)
def run_digitize_analyze_client_tasks(self, site_id: int):
    """Task that generates all the results for the digitize or analysis package based on
    client pricing options:

    a) Basic features, this will run always as first step because is a dependency

    b) Run Analysis chain
        b-1) Calculates building elevation based on coordinates of the building
        b-2) Generate surroundings for the view
        b-3) executes quavis
        b-4) Calculate unit types for the dashboard column

    c - optional) Generates the PNG for units and floors
    d - optional) Generates the DXF for the floors

    e) Generate zipfile with all the deliverables available
    f) Update site to SUCCESS
    """
    from handlers.db import SiteDBHandler

    simulations_chain = WorkflowGenerator(
        site_id=site_id
    ).get_full_chain_based_on_client_options()
    site_info = SiteDBHandler.get_by(id=site_id)
    simulations_chain.apply_async(
        priority=INCREASED_TASK_PRIORITY + site_info["priority"]
    )


class WorkflowGenerator:
    def __init__(self, site_id: int):
        from handlers.db import ClientDBHandler, SiteDBHandler

        self.site_id = site_id
        self.site_info = SiteDBHandler.get_by(id=site_id)
        client = ClientDBHandler.get_by_site_id(site_id=self.site_id)
        self.options = {k[7:]: v for k, v in client.items() if k.startswith("option_")}

    @cached_property
    def residential_unit_ids(self):
        return list(
            UnitDBHandler.find_ids(
                site_id=self.site_id, unit_usage=UNIT_USAGE.RESIDENTIAL
            )
        )

    def get_unit_png_and_pdf_tasks(
        self,
    ) -> list[Signature]:
        from handlers.db import UnitDBHandler

        return [
            generate_unit_pngs_and_pdfs.si(unit_id=unit_id)
            for unit_id in UnitDBHandler.find_ids(site_id=self.site_id)
        ]

    def get_floor_deliverables_tasks(self) -> list[Canvas]:
        from handlers.db import FloorDBHandler

        def get_tasks(floor):
            t = []
            if self.options["pdf"]:
                t.append(generate_pngs_and_pdfs_for_floor_task.si(floor_id=floor["id"]))
            if self.options["dxf"]:
                t.extend(
                    [
                        generate_dxf_floor_task.si(floor_id=floor["id"]),
                        generate_dwg_floor_task.si(floor_id=floor["id"]),
                    ]
                )
            return t

        return [
            workflow(*tasks)
            for floor in FloorDBHandler.find_by_site_id(site_id=self.site_id)
            if (tasks := get_tasks(floor))
        ]

    def get_full_chain_based_on_client_options(self) -> Signature:
        post_pipeline_workflow = workflow(
            workflow(
                self.get_qa_validation_chain(),
                run_unit_types_task.si(site_id=self.site_id),
            ),
            workflow(
                update_site_location_task.si(site_id=self.site_id),
                run_buildings_elevation_task.si(site_id=self.site_id),
            ),
            run_in_parallel=True,
        )

        if self.options["analysis"]:
            (
                pre_simulation_tasks,
                simulation_tasks,
                post_simulation_tasks,
            ) = self.get_simulation_tasks()
            return workflow(
                post_pipeline_workflow,
                *pre_simulation_tasks,
                workflow(
                    *simulation_tasks,
                    *self.get_building_3d_tasks(),
                    *self.get_deliverables_tasks(),
                    run_in_parallel=True,
                ),
                workflow(*post_simulation_tasks, run_in_parallel=True),
                task_site_zip_deliverable.si(site_id=self.site_id),
                self.slam_results_success(),
                on_error=self.slam_results_failure(),
            )

        return workflow(
            post_pipeline_workflow,
            workflow(
                *self.get_deliverables_tasks(),
                run_in_parallel=True,
            ),
            task_site_zip_deliverable.si(site_id=self.site_id),
            self.slam_results_success(),
            on_error=self.slam_results_failure(),
        )

    def get_building_3d_tasks(self) -> list[Signature]:
        from handlers.db import BuildingDBHandler

        return [
            generate_building_triangulation_task.si(building_id=building_id)
            for building_id in BuildingDBHandler.find_ids(site_id=self.site_id)
        ]

    def get_simulation_tasks(
        self,
    ) -> Tuple[list[Signature], list[Signature], list[Signature]]:
        pre_simulation_tasks = [
            generate_surroundings_for_view_analysis_task.si(site_id=self.site_id),
        ]

        simulation_tasks = [
            self.get_view_task_chain(),
            self.get_sun_v2_task_chain(),
            self.get_connectivity_simulation_task_chain(),
            self.get_biggest_rectangle_task_chain(),
            self.get_noise_chain(),
        ]

        post_simulation_tasks = [
            self._get_vector_generation_tasks_chain(),
            validate_simulations_task.si(site_id=self.site_id),
        ]

        if self.residential_unit_ids:
            post_simulation_tasks.append(
                generate_unit_plots_task.si(site_id=self.site_id)
            )
            if self.options["competition"]:
                post_simulation_tasks.append(
                    self.get_competition_features_task_chain(),
                )

        return pre_simulation_tasks, simulation_tasks, post_simulation_tasks

    def _get_vector_generation_tasks_chain(self):
        gen_vector_si = generate_vector_files_task.si(site_id=self.site_id)
        if self.site_info.get("sub_sampling_number_of_clusters"):
            return workflow(
                clustering_units_task.si(site_id=self.site_id), gen_vector_si
            )
        else:
            return gen_vector_si

    def get_noise_chain(self):
        return workflow(
            self.get_noise_windows_simulation_task_chain(),
            self.get_noise_simulation_task_chain(),
        )

    def get_deliverables_tasks(self):
        deliverable_tasks = [
            generate_energy_reference_area_task.si(site_id=self.site_id),
        ]
        if self.options["pdf"]:
            deliverable_tasks.extend(self.get_unit_png_and_pdf_tasks())

        if self.options["dxf"] or self.options["pdf"]:
            # To avoid serialization errors due to concurrent tasks updating the floor entry
            # we chain all the tasks for the same floor inside the next function
            deliverable_tasks.extend(self.get_floor_deliverables_tasks())

        if self.options["ifc"]:
            deliverable_tasks.append(generate_ifc_file_task.si(site_id=self.site_id))

        return deliverable_tasks

    def get_basic_features_task_chain(self):
        run_id = create_run_id()
        return workflow(
            register_simulation.si(
                site_id=self.site_id,
                run_id=run_id,
                task_type=TASK_TYPE.BASIC_FEATURES.name,
            ),
            run_basic_features_task.si(run_id=run_id),
        )

    def get_biggest_rectangle_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            biggest_rectangle_task.si(site_id=self.site_id, run_id=run_id),
            run_id=run_id,
            task_type=TASK_TYPE.BIGGEST_RECTANGLE,
        )

    def get_simulation_task_chain_wrapper(
        self,
        *signatures: Signature,
        run_id: str,
        task_type: TASK_TYPE,
    ):
        return workflow(
            register_simulation.si(
                site_id=self.site_id, run_id=run_id, task_type=task_type.name
            ),
            workflow(*signatures, on_error=simulation_error.s(run_id=run_id)),
            simulation_success.si(run_id=run_id),
        )

    def get_sun_v2_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            workflow(
                configure_sun_v2_quavis_task.si(run_id=run_id),
                run_quavis_task.si(run_id=run_id),
                store_sun_v2_quavis_results_task.si(run_id=run_id),
                delete_simulation_artifacts.si(run_id=run_id),
            ),
            run_id=run_id,
            task_type=TASK_TYPE.SUN_V2,
        )

    def get_view_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            workflow(
                configure_quavis_task.si(run_id=run_id),
                run_quavis_task.si(run_id=run_id),
                store_quavis_results_task.si(run_id=run_id),
                delete_simulation_artifacts.si(run_id=run_id),
            ),
            run_id=run_id,
            task_type=TASK_TYPE.VIEW_SUN,
        )

    def get_competition_features_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            competition_features_calculation_task.si(
                site_id=self.site_id, run_id=run_id
            ),
            run_id=run_id,
            task_type=TASK_TYPE.COMPETITION,
        )

    def get_connectivity_simulation_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            connectivity_simulation_task.si(site_id=self.site_id, run_id=run_id),
            run_id=run_id,
            task_type=TASK_TYPE.CONNECTIVITY,
        )

    def get_noise_simulation_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            noise_simulation_task.si(site_id=self.site_id, run_id=run_id),
            run_id=run_id,
            task_type=TASK_TYPE.NOISE,
        )

    def get_noise_windows_simulation_task_chain(self):
        run_id = create_run_id()
        return self.get_simulation_task_chain_wrapper(
            noise_windows_simulation_task.si(site_id=self.site_id, run_id=run_id),
            run_id=run_id,
            task_type=TASK_TYPE.NOISE_WINDOWS,
        )

    def get_sample_surr_generation_chain(self):
        return workflow(
            update_site_location_task.si(site_id=self.site_id),
            run_buildings_elevation_task.si(site_id=self.site_id),
            generate_sample_surroundings_for_view_analysis_task.si(
                site_id=self.site_id
            ),
        )

    def get_qa_validation_chain(self):
        return workflow(
            qa_validation_task_processing.si(site_id=self.site_id),
            workflow(
                self.get_basic_features_task_chain(),
                run_qa_validation_task.si(site_id=self.site_id),
                on_error=qa_validation_task_failure.s(site_id=self.site_id),
            ),
        )

    def slam_results_success(self):
        return slam_results_success.si(site_id=self.site_id)

    def slam_results_failure(self):
        return slam_results_failure.s(site_id=self.site_id)


@celery_retry_task
def slam_results_success(self, site_id: int):
    """Changes the status of the sites at the end of the chain"""
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(full_slam_results=ADMIN_SIM_STATUS.SUCCESS.value),
    )


@celery_app.task
def slam_results_failure(*args, site_id, **kwargs):
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(full_slam_results=ADMIN_SIM_STATUS.FAILURE.value),
    )


@celery_app.task
def empty_task(arg):
    """This task solely exist for technical reasons"""
    return arg


if environ.get("TEST_ENVIRONMENT"):

    @celery_app.task
    def fake_error_handler(request, exc, traceback, redis_key=None):
        from redis.client import Redis

        logger.error(f"Oh no! {exc}")
        if redis_key:
            Redis(**redis_conn_config).rpush(
                redis_key,
                json.dumps(
                    {
                        "time": time(),
                        "message": str(exc),
                    }
                ),
            )

    @celery_retry_task
    def fake_task(
        self,
        message=None,
        raise_exception=False,
        wait_for=0,
    ):
        sleep(wait_for)
        if message:
            if raise_exception:
                raise Exception(message)
            else:
                logger.info(message)

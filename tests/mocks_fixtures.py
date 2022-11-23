import uuid
import webbrowser
from typing import List

import pytest
from shapely.geometry import Point

from surroundings.base_building_handler import Building
from surroundings.swisstopo import SwissTopoBuildingSurroundingHandler
from tasks import (
    basic_features,
    clustering_units_tasks,
    competition_features_tasks,
    connectivity_tasks,
    deliverables_tasks,
    noise_tasks,
    qa_validation_tasks,
    quavis_tasks,
    rectangulator_tasks,
    simulations_tasks,
    surroundings_tasks,
    workflow_tasks,
)
from tests.utils import random_simulation_version


@pytest.fixture
def app():
    """Required for the test flask client"""
    from slam_api.app import app

    return app


@pytest.fixture
def mock_working_dir(monkeypatch):
    monkeypatch.setenv("WORKING_DIR", "/it can not exists")


@pytest.fixture
def mocked_surrounding_storage_handler(mocker):
    class FakeSurroundingStorageHandler:
        triangles = None

        @classmethod
        def upload(cls, triangles, *args, **kwargs):
            cls.triangles = triangles

        @classmethod
        def read_from_cloud(cls, *args, **kwargs):
            return cls.triangles

    from surroundings import surrounding_handler

    return mocker.patch.object(
        surrounding_handler,
        surrounding_handler.SurroundingStorageHandler.__name__,
        FakeSurroundingStorageHandler,
    )


@pytest.fixture
def mocked_gcp_download(mocker):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file.__name__,
        return_value=None,
    )


@pytest.fixture
def mocked_gcp_download_file_as_bytes(mocker):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file_as_bytes.__name__,
        return_value=b"a beautiful image",
    )


@pytest.fixture
def mocked_gcp_delete(mocker):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.delete_resource.__name__,
        return_value=None,
    )


@pytest.fixture
def mocked_gcp_create_bucket(mocker):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.create_bucket_if_not_exists.__name__,
        return_value=None,
    )


@pytest.fixture
def mocked_gcp_upload_file_to_bucket(mocker, random_media_link):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.upload_file_to_bucket.__name__,
        return_value=random_media_link,
    )


@pytest.fixture
def mocked_gcp_download_file_from_media_link(mocker, random_media_link):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file_from_media_link.__name__,
        return_value=b"a noice image",
    )


@pytest.fixture
def mocked_gcp_upload_bytes_to_bucket(mocker, random_media_link):
    from handlers.gcloud_storage import GCloudStorageHandler

    return mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.upload_bytes_to_bucket.__name__,
        return_value=random_media_link,
    )


@pytest.fixture
def mock_gcp_client(mocker):
    from handlers import GCloudStorageHandler

    return mocker.patch.object(GCloudStorageHandler, "client", autospec=True)


@pytest.fixture
def mocked_plan_image_upload_to_gc(mocker, random_plain_floorplan_link):
    from handlers import PlanHandler

    return mocker.patch.object(
        PlanHandler,
        PlanHandler.upload_plan_image_to_google_cloud.__name__,
        return_value=random_plain_floorplan_link,
    )


@pytest.fixture
def mocked_get_units_plot(mocker):
    return mocker.patch("slam_api.apis.unit_view.get_units_plot", return_value="")


@pytest.fixture
def mocked_webbrowser(mocker):
    return mocker.patch.object(webbrowser, "open", return_value=None)


@pytest.fixture
def celery_eager(monkeypatch):
    from workers_config import celery_config

    monkeypatch.setattr(celery_config, "task_always_eager", True)


@pytest.fixture
def mocked_site_pipeline_completed(mocker):
    from common_utils.constants import PipelineCompletedCriteria
    from handlers.site_handler import SiteHandler

    return mocker.patch.object(
        SiteHandler,
        "pipeline_completed_criteria",
        return_value=PipelineCompletedCriteria(
            labelled=True,
            classified=True,
            splitted=True,
            units_linked=True,
            georeferenced=True,
        ),
    )


@pytest.fixture()
def dummy_elevation(mocker):
    from common_utils.constants import REGION
    from surroundings.base_elevation_handler import BaseElevationHandler

    class DummyElevationHandler(BaseElevationHandler):
        EPSG = REGION.CH

        def get_elevation(self, point) -> float:
            return 100.0

    import surroundings.base_elevation_handler as base

    mocker.patch.object(
        base,
        "get_elevation_handler",
        return_value=DummyElevationHandler(
            region=REGION.CH,
            location=Point(2691566.8, 1233463.5),
            simulation_version=random_simulation_version(),
        ),
    )


@pytest.fixture
def mocked_quavis_gcp_handler(mocker):
    class MockQuavisGCPHandler:
        quavis_input = None
        quavis_output = None
        delete_counter = 0

        @classmethod
        def delete_simulation_artifacts(cls, run_id):
            cls.delete_counter += 1

        @classmethod
        def get_quavis_output(cls, *args, **kwargs):
            return cls.quavis_output

        @classmethod
        def get_quavis_input(cls, *args, **kwargs):
            return cls.quavis_input

        @classmethod
        def upload_quavis_input(cls, quavis_input, *args, **kwargs):
            cls.quavis_input = quavis_input

        @classmethod
        def upload_quavis_output(cls, quavis_output, *args, **kwargs):
            cls.quavis_output = quavis_output

    import handlers.quavis
    from handlers.quavis import quavis_gcp_handler

    mocker.patch.object(handlers.quavis, "QuavisGCPHandler", MockQuavisGCPHandler)

    return mocker.patch.object(
        quavis_gcp_handler, "QuavisGCPHandler", MockQuavisGCPHandler
    )


@pytest.fixture
def run_ids(site, mocker) -> List[str]:
    """7 run_ids"""

    from tasks import workflow_tasks

    run_ids = [
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
    ]
    mocker.patch.object(
        workflow_tasks,
        workflow_tasks.create_run_id.__name__,
        side_effect=run_ids,
    )
    return run_ids


@pytest.fixture()
def basic_features_run_id(site, mocker) -> str:
    from tasks import workflow_tasks

    run_id = str(uuid.uuid4())
    mocker.patch.object(
        workflow_tasks,
        workflow_tasks.create_run_id.__name__,
        return_value=run_id,
    )
    return run_id


@pytest.fixture
def overpass_api_mocked(mocker):
    def _f(return_value=None):
        from surroundings.osm.overpass_api_handler import OverpassAPIHandler

        return mocker.patch.object(
            OverpassAPIHandler, "get_building_metadata", return_value=return_value or {}
        )

    return _f


@pytest.fixture
def mocked_delay_slam_result(mocker):
    from tasks import workflow_tasks

    return mocker.patch.object(workflow_tasks.Task, "apply_async", return_value=None)


@pytest.fixture
def mocked_generate_geo_referencing_surroundings_for_site_task(mocker):
    from tasks.surroundings_tasks import (
        generate_geo_referencing_surroundings_for_site_task,
    )

    return mocker.patch.object(
        generate_geo_referencing_surroundings_for_site_task,
        "delay",
        return_value=None,
    )


@pytest.fixture
def mocked_run_generate_geo_referencing_surroundings_for_site_task(mocker):
    from tasks.surroundings_tasks import (
        generate_geo_referencing_surroundings_for_site_task,
    )

    return mocker.patch.object(
        generate_geo_referencing_surroundings_for_site_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def mock_elevation(mocker):
    from surroundings.swisstopo import SwisstopoElevationHandler

    def _mock_elevation(elevation=100, elevation_handler=SwisstopoElevationHandler):

        return mocker.patch.object(
            elevation_handler,
            "get_elevation",
            return_value=elevation,
        )

    return _mock_elevation


@pytest.fixture
def fake_noise_simulator():
    class FakeNoiseRayTracer:
        def get_noise_at(self, **kwargs) -> float:
            return 30

    return FakeNoiseRayTracer()


@pytest.fixture
def mocked_geolocator(monkeypatch, requests_mock):
    from handlers.geo_location import GeoLocator

    monkeypatch.setenv("TEST_ENVIRONMENT", "False")

    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 293958087,
            "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
            "osm_type": "way",
            "osm_id": 28468412,
            "lat": "47.39223866146593",
            "lon": "8.460005963469223",
            "display_name": "Alter Zürichweg, Gut Sonnenberg, Schlieren, Bezirk Dietikon, Zürich, 8952, Switzerland",
            "address": {
                "road": "Alter Zürichweg",
                "isolated_dwelling": "Gut Sonnenberg",
                "town": "Schlieren",
                "county": "Bezirk Dietikon",
                "state": "Zürich",
                "postcode": "8952",
                "country": "Switzerland",
                "country_code": "ch",
            },
            "boundingbox": ["47.3917749", "47.3931473", "8.4575939", "8.4639758"],
        },
    )


@pytest.fixture
def mocked_geolocator_outside_ch(monkeypatch, requests_mock):
    from handlers.geo_location import GeoLocator

    monkeypatch.setenv("TEST_ENVIRONMENT", "False")

    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 293958087,
            "osm_id": 28468412,
            "lat": "50.0",
            "lon": "14.0",
            "display_name": "Somewhere in Prague",
            "address": {
                "state": "Prague",
                "postcode": "8952",
                "country": "Czech Republic",
                "country_code": "cz",
            },
            "boundingbox": ["50.0", "50.2", "14.1", "14.3"],
        },
    )


@pytest.fixture
def get_buildings_convex_building(convex_building_1, mocker):
    mocker.patch.object(
        SwissTopoBuildingSurroundingHandler,
        SwissTopoBuildingSurroundingHandler.get_buildings.__name__,
        return_value=[
            Building(
                geometry=convex_building_1,
                footprint=SwissTopoBuildingSurroundingHandler._create_building_footprint(
                    convex_building_1
                ),
            )
        ],
    )


@pytest.fixture
def ifc_file_dummy(mocker):
    ifc_file_dummy = mocker.MagicMock()
    ifc_file_dummy.create_entity = mocker.MagicMock(
        side_effect=lambda t, *args, **kwargs: f"dummy_{t}"
    )
    return ifc_file_dummy


@pytest.fixture
def ifc_file_dummy_with_parameters(mocker):
    ifc_file_dummy_with_parameters = mocker.MagicMock()
    ifc_file_dummy_with_parameters.create_entity = mocker.MagicMock(
        side_effect=lambda t, *args, **kwargs: f"dummy_{t}({str(kwargs)})"
    )
    return ifc_file_dummy_with_parameters


@pytest.fixture
def initial_tasks_mocked(mocker):
    return [
        mocker.patch.object(*to_mock, return_value=None)
        for to_mock in [
            (basic_features.run_unit_types_task, "run"),
            (simulations_tasks.run_buildings_elevation_task, "run"),
            (simulations_tasks.update_site_location_task, "run"),
        ]
    ]


@pytest.fixture
def quavis_task_mocked(mocker):
    return mocker.patch.object(quavis_tasks.run_quavis_task, "run", return_value=None)


@pytest.fixture
def generate_surroundings_task_mocked(mocker, run_ids):
    return mocker.patch.object(
        surroundings_tasks.generate_surroundings_for_view_analysis_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def configure_quavis_mocked(mocker):
    return mocker.patch.object(
        simulations_tasks.configure_quavis_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def store_quavis_results_mocked(mocker):
    return mocker.patch.object(
        simulations_tasks.store_quavis_results_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def store_quavis_sun_v2_results_mocked(mocker):
    return mocker.patch.object(
        simulations_tasks.store_sun_v2_quavis_results_task, "run", return_value=None
    )


@pytest.fixture
def configure_sun_v2_quavis_task_mocked(mocker):
    return mocker.patch.object(
        simulations_tasks.configure_sun_v2_quavis_task, "run", return_value=None
    )


@pytest.fixture
def qa_validation_task_mocked(mocker):
    return mocker.patch.object(
        qa_validation_tasks.run_qa_validation_task, "run", return_value=None
    )


@pytest.fixture
def basic_feature_mocked(mocker):
    return mocker.patch.object(
        basic_features.run_basic_features_task, "run", return_value=None
    )


@pytest.fixture
def clustering_units_mocked(mocker):
    return mocker.patch.object(
        clustering_units_tasks.clustering_units_task, "run", return_value=None
    )


@pytest.fixture
def dxf_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_dxf_floor_task, "run", return_value=None
    )


@pytest.fixture
def dwg_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_dwg_floor_task, "run", return_value=None
    )


@pytest.fixture
def png_pdf_floor_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_pngs_and_pdfs_for_floor_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def connectivity_mocked(mocker):
    return mocker.patch.object(
        connectivity_tasks.connectivity_simulation_task, "run", return_value=None
    )


@pytest.fixture
def noise_simulation_mocked(mocker):
    return mocker.patch.object(
        noise_tasks.noise_simulation_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def noise_window_simulation_mocked(mocker):
    return mocker.patch.object(
        noise_tasks.noise_windows_simulation_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def biggest_rectangle_simulation_mocked(mocker):
    return mocker.patch.object(
        rectangulator_tasks.biggest_rectangle_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def competition_features_mocked(mocker):
    return mocker.patch.object(
        competition_features_tasks.competition_features_calculation_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def success_task_mocked(mocker):
    return mocker.patch.object(
        workflow_tasks.slam_results_success, "run", return_value=None
    )


@pytest.fixture
def zip_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.task_site_zip_deliverable, "run", return_value=None
    )


@pytest.fixture
def generate_building_triangulation_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_building_triangulation_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def generate_ifc_file_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_ifc_file_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def generate_vector_files_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_vector_files_task, "run", return_value=None
    )


@pytest.fixture
def generate_energy_reference_area_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_energy_reference_area_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def generate_unit_plots_task_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_unit_plots_task,
        "run",
        return_value=None,
    )


@pytest.fixture
def generate_unit_pngs_and_pdfs_mocked(mocker):
    return mocker.patch.object(
        deliverables_tasks.generate_unit_pngs_and_pdfs,
        "run",
        return_value=None,
    )


@pytest.fixture
def slam_results_success_mocked(mocker):
    return mocker.patch.object(
        workflow_tasks.slam_results_success, "run", return_value=None
    )

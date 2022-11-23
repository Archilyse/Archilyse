import mimetypes
from collections import defaultdict
from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

from flask import jsonify, request, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest.fields import Upload
from google.cloud import exceptions as gcloud_exceptions
from marshmallow import Schema, ValidationError, fields
from shapely.geometry import mapping as shapely_mapping
from werkzeug.datastructures import FileStorage

from brooks.util.projections import project_geometry
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS,
    REGION,
    USER_ROLE,
)
from common_utils.exceptions import (
    DependenciesUnMetSimulationException,
    QAMissingException,
    TaskAlreadyRunningException,
)
from common_utils.utils import post_message_to_slack
from db_models import SiteDBModel
from handlers import GCloudStorageHandler, PlanLayoutHandler, QAHandler, SiteHandler
from handlers.db import (
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    SlamSimulationValidationDBHandler,
    UnitDBHandler,
)
from handlers.db.building_handler import BuildingDBSchema
from handlers.db.serialization.geojson import GeoJsonPolygonSchema
from handlers.db.site_handler import SiteDBSchema, SiteDBSchemaMethods
from handlers.db.unit_handler import UnitDBSchema
from handlers.ph_results_upload_handler import CVResultUploadHandler
from handlers.plan_handler import PipelineSchema, PlanHandler
from handlers.utils import get_client_bucket_name
from slam_api.dms_views.collection_view import dms_limited_collection_view
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.serialization import CustomValuatorResultFileDeserializer, MsgSchema
from slam_api.utils import group_id_loader, role_access_control
from tasks.deliverables_tasks import (
    generate_energy_reference_area_task,
    generate_ifc_file_task,
    generate_unit_plots_task,
    generate_vector_files_task,
)
from tasks.workflow_tasks import WorkflowGenerator, slam_results_success, workflow

site_app = Blueprint("site", __name__)


@site_app.errorhandler(ValidationError)
def handle_marshmallow_validation_error(e):
    return jsonify(msg=str(e)), HTTPStatus.UNPROCESSABLE_ENTITY


class BuildingWithFloorInfo(Schema.from_dict(BuildingDBSchema().fields)):  # type: ignore
    floors = fields.Dict()


class SiteWithBuildings(Schema.from_dict(SiteDBSchema().fields), SiteDBSchemaMethods):  # type: ignore
    buildings = fields.Nested(BuildingWithFloorInfo, many=True, required=True)


class SiteArgsSchema(Schema.from_dict(SiteDBSchema().fields), SiteDBSchemaMethods):  # type: ignore
    classification_scheme = fields.Str()
    sub_sampling_number_of_clusters = fields.Int(allow_none=True)
    qa_id = fields.Int(required=True)


class SiteAnalysisQuery(Schema):
    client_id = fields.Integer(required=False)
    site_id = fields.Integer(required=False)
    building_id = fields.Integer(required=False)
    floor_id = fields.Integer(required=False)
    unit_id = fields.Integer(required=False)


class NetAreaDistributionSchema(Schema):
    fields.Dict(keys=fields.Int(), values=fields.Float())


class SimulationValidationSchema(Schema):
    fields.Dict(keys=fields.Int(), values=fields.Dict())


class SiteSurfaceSchema(Schema):
    total_square_meters = fields.List(fields.Str())


@site_app.route("/<int:site_id>/ph-results", methods=["POST"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@site_app.arguments(
    Schema.from_dict({"custom_valuator_results": Upload(required=True)}),
    location="files",
    as_kwargs=True,
)
@site_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
def upload_custom_valuator_results(
    site_id: int, custom_valuator_results: FileStorage
) -> Dict:
    custom_valuator_results = CustomValuatorResultFileDeserializer.deserialize(
        file=custom_valuator_results
    )
    CVResultUploadHandler.update_custom_valuator_results(
        site_id=site_id, custom_valuator_results=custom_valuator_results
    )
    return {"msg": "File uploaded successfully."}


@site_app.route("/<int:site_id>")
class SiteView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @site_app.response(schema=SiteDBSchema, status_code=HTTPStatus.OK)
    def get(self, site_id: int) -> Tuple[Dict, HTTPStatus]:
        return jsonify(SiteDBHandler.get_by(id=site_id))

    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @site_app.arguments(
        SiteArgsSchema(partial=True),
        location="json",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=SiteDBModel)
    @site_app.response(schema=SiteDBSchema, status_code=HTTPStatus.OK)
    def put(self, site_id: int, **kwargs):
        updated_site = SiteHandler.update(site_id=site_id, **kwargs)
        return jsonify(updated_site)

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @site_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
    def delete(self, site_id: int):
        SiteDBHandler.delete({"id": site_id})
        return dict(msg="Deleted successfully")


@site_app.route("/<int:site_id>/structure", methods=["GET"])
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
        USER_ROLE.COMPETITION_ADMIN,
        USER_ROLE.COMPETITION_VIEWER,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
@site_app.response(schema=SiteWithBuildings, status_code=HTTPStatus.OK)
def site_get_structure(site_id: int) -> Tuple[Dict, HTTPStatus]:
    site = SiteDBHandler.get_by(id=site_id)
    buildings = BuildingDBHandler.find(site_id=site_id)
    floor_by_building_id = defaultdict(list)
    plans_ready = SiteHandler.get_plan_ids_with_annotation_ready(site_id=site_id)
    for floor in FloorDBHandler.find_in(
        building_id=[b["id"] for b in buildings],
        output_columns=["id", "plan_id", "floor_number", "building_id"],
    ):
        floor["plan_ready"] = floor["plan_id"] in plans_ready
        floor_by_building_id[floor["building_id"]].append(floor)

    site["buildings"] = buildings
    for building in buildings:
        building["floors"] = {
            floor["id"]: {
                "plan_id": floor["plan_id"],
                "floor_number": floor["floor_number"],
                "building_id": floor["building_id"],
                "plan_ready": floor["plan_ready"],
            }
            for floor in floor_by_building_id[building["id"]]
        }
    return jsonify(site)


@site_app.route("/<int:site_id>/surrounding_buildings_footprints", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@site_app.response(
    schema=Schema.from_dict({"data": fields.Nested(GeoJsonPolygonSchema, many=True)}),
    status_code=HTTPStatus.OK,
)
def site_get_surrounding_buildings(site_id: int) -> Dict:
    swisstopo_buildings_footprints = SiteHandler.get_surr_buildings_footprints_for_site(
        site_id=site_id, as_lat_lon=True
    )
    return jsonify(
        dict(data=[shapely_mapping(b) for b in swisstopo_buildings_footprints])
    )


@site_app.route("/<int:site_id>/run-feature-generation", methods=["POST"])
@role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER})
@site_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
def generate_features(site_id):
    from tasks.workflow_tasks import run_digitize_analyze_client_tasks

    try:
        run_digitize_analyze_client_tasks.delay(site_id=site_id)
        return jsonify(
            msg=f"Successfully started running analysis for site with id [{site_id}]"
        )
    except DependenciesUnMetSimulationException as e:
        return (
            jsonify(
                msg=f"Some requirements are not met for the site requested: [{str(e)}]"
            ),
            HTTPStatus.BAD_REQUEST,
        )
    except TaskAlreadyRunningException:
        return (
            jsonify(msg=f"Analysis for site {site_id} is already running"),
            HTTPStatus.BAD_REQUEST,
        )


@site_app.route("/<int:site_id>/surroundings_sample")
class SampleSurroundings(MethodView):
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self, site_id: int):
        with NamedTemporaryFile() as f:
            try:
                GCloudStorageHandler().download_file(
                    bucket_name=GOOGLE_CLOUD_BUCKET,
                    remote_file_path=GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS.joinpath(
                        SiteHandler.get_surroundings_sample_path(site_id=site_id)
                    ),
                    local_file_name=Path(f.name),
                )
            except gcloud_exceptions.NotFound:
                return (
                    jsonify({"msg": "Surroundings sample file not ready"}),
                    HTTPStatus.NOT_FOUND,
                )
            else:
                return send_file(
                    f.name,
                    mimetype=mimetypes.types_map[".html"],
                    as_attachment=True,
                    attachment_filename=f"{site_id}_sample_surroundings.html",
                )

    @role_access_control(roles={USER_ROLE.ADMIN})
    @site_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
    def post(self, site_id: int):
        from tasks.surroundings_tasks import enqueue_sample_surroundings_task

        try:
            enqueue_sample_surroundings_task(site_id=site_id)

        except DependenciesUnMetSimulationException as e:
            return (
                jsonify(msg=str(e)),
                HTTPStatus.BAD_REQUEST,
            )
        except TaskAlreadyRunningException:
            return (
                jsonify(
                    msg=f"Sample Surroundings generation for site {site_id} is already running"
                ),
                HTTPStatus.BAD_REQUEST,
            )


@site_app.route("/<int:site_id>/qa-task")
class QAValidationTask(MethodView):
    @staticmethod
    def _qa_data_is_missing(site_id: int) -> bool:
        try:
            QAHandler.get_qa_data_check_exists(site_id=site_id)
            return False
        except QAMissingException:
            return True

    @staticmethod
    def _qa_task_is_running(site_id: int) -> bool:
        site = SiteDBHandler.get_by(
            id=site_id, output_columns=["basic_features_status"]
        )
        return site["basic_features_status"] in (
            ADMIN_SIM_STATUS.PENDING.name,
            ADMIN_SIM_STATUS.PROCESSING.name,
        )

    @staticmethod
    def _reset_result_fields(site_id: int):
        SiteDBHandler.update(
            item_pks=dict(id=site_id),
            new_values=dict(
                basic_features_status=ADMIN_SIM_STATUS.PENDING.value,
                basic_features_error=None,
                qa_validation=None,
            ),
        )

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @site_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
    def post(self, site_id: int):
        if self._qa_task_is_running(site_id=site_id):
            return (
                jsonify(msg=f"QA task for site {site_id} is already running"),
                HTTPStatus.BAD_REQUEST,
            )
        if self._qa_data_is_missing(site_id=site_id):
            return (
                jsonify(msg=f"Site {site_id} doesn't have QA data"),
                HTTPStatus.BAD_REQUEST,
            )

        self._reset_result_fields(site_id=site_id)

        WorkflowGenerator(site_id=site_id).get_qa_validation_chain().delay()

        return jsonify(
            msg=f"Successfully started running analysis for site with id [{site_id}]"
        )


@site_app.route("/", methods=["GET"])
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
@group_id_loader
@site_app.arguments(
    Schema.from_dict(
        {
            "client_id": fields.Int(required=True, allow_none=False),
            "client_site_id": fields.Str(),
            "dms_sites": fields.Boolean(required=False, dump_default=False),
        }
    ),
    location="querystring",
    as_kwargs=True,
)
@dms_limited_collection_view(db_model=SiteDBModel)
@site_app.response(schema=SiteDBSchema(many=True), status_code=HTTPStatus.OK)
def get_sites(
    group_id,
    client_id: int,
    dms_sites: Optional[bool] = False,
    dms_limited_sql_filter: Optional[str] = None,
    client_site_id: Optional[str] = None,
):
    """
    dms_limited_sql_filter: tuple of sql alchemy filter conditions
    """
    if dms_sites:
        sites = SiteHandler.get_dms_sites(
            client_id=client_id, dms_limited_sql_filter=dms_limited_sql_filter
        )
    else:
        sites = SiteDBHandler.get_sites_with_ready_field(
            client_id=client_id,
            client_site_id=client_site_id,
            group_id=group_id,
            additional_filter=dms_limited_sql_filter,
        )
    return jsonify(sites), HTTPStatus.OK


@site_app.route("/", methods=["POST"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@group_id_loader
@site_app.arguments(SiteArgsSchema(partial=True), location="form", as_kwargs=True)
@site_app.response(schema=SiteDBSchema, status_code=HTTPStatus.CREATED)
def add_site(group_id, **kwargs):
    kwargs.pop("ifc", None)
    if request.files:
        kwargs["ifc"] = [f for _, files in request.files.lists() for f in files]
    if qa_id := kwargs.pop("qa_id"):
        new_site = SiteHandler.add(**kwargs, group_id=group_id, qa_id=qa_id)
        return jsonify(new_site), HTTPStatus.CREATED
    return jsonify({"No site QA data provided."}), HTTPStatus.BAD_REQUEST


@site_app.route("/<int:site_id>/units", methods=["GET"])
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.COMPETITION_ADMIN,
        USER_ROLE.COMPETITION_VIEWER,
        USER_ROLE.DMS_LIMITED,
    }
)
@site_app.arguments(
    Schema.from_dict({"field": fields.Str(required=False, dump_default=False)}),
    location="querystring",
    as_kwargs=True,
)
@dms_limited_entity_view(db_model=SiteDBModel)
@site_app.response(schema=UnitDBSchema(many=True), status_code=HTTPStatus.OK)
def get_units_by_site(site_id: int, field: Optional[str] = None) -> List[Dict]:
    if field:
        units = UnitDBHandler.find(site_id=site_id, output_columns=[f"{field}"])
    else:
        units = UnitDBHandler.find(site_id=site_id)
    return jsonify(units)


@site_app.route("/<int:site_id>/deliverable/download", methods=["GET"])
@role_access_control(roles={USER_ROLE.ADMIN})
def download_deliverable_zipfile(site_id: int):
    """
    Download deliverable Zipfile
    """
    site = SiteDBHandler.get_by(id=site_id)
    with NamedTemporaryFile() as fzip:
        try:
            GCloudStorageHandler().download_file(
                bucket_name=get_client_bucket_name(client_id=site["client_id"]),
                remote_file_path=SiteHandler.get_deliverable_zipfile_path(
                    client_id=site["client_id"], site_id=site_id
                ),
                local_file_name=Path(fzip.name),
            )
        except gcloud_exceptions.NotFound:
            return jsonify({"msg": "Zipfile not ready"}), HTTPStatus.NOT_FOUND
        else:
            return send_file(
                fzip.name,
                mimetype=mimetypes.types_map[".zip"],
                as_attachment=True,
                attachment_filename=f"deliverable-{site_id}.zip",
            )


@site_app.route("/<int:site_id>/pipeline", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@site_app.response(schema=PipelineSchema(many=True), status_code=HTTPStatus.OK)
def get_site_pipelines(site_id: int):
    site = SiteDBHandler.get_by(id=site_id)
    plans = PlanDBHandler.find(
        site_id=site_id,
        output_columns=[
            "id",
            "created",
            "updated",
            "building_id",
            "georef_x",
            "georef_y",
            "georef_rot_x",
            "georef_rot_y",
            "georef_rot_angle",
            "annotation_finished",
            "georef_scale",
            "site_id",
            "without_units",
            "is_masterplan",
        ],
    )
    result = PlanHandler.get_pipelines_output(plans=plans, site=site)

    return jsonify(result)


@site_app.route("/<int:site_id>/sim_validation", methods=["GET"])
@role_access_control(roles={USER_ROLE.ADMIN})
@site_app.response(schema=SimulationValidationSchema, status_code=HTTPStatus.OK)
def get_site_simulation_validation(site_id: int):
    validation = SlamSimulationValidationDBHandler.get_by(
        site_id=site_id, output_columns=["results"]
    )

    return jsonify(validation["results"])


@site_app.route("/<int:site_id>/ground_georef_plans", methods=["GET"])
@role_access_control(roles={USER_ROLE.ADMIN})
def get_ground_georeferenced_plans(site_id: int):
    site_info = SiteDBHandler.get_by(id=site_id, output_columns=["georef_region"])
    all_floors = FloorDBHandler.find_by_site_id(
        site_id=site_id, output_columns=["floor_number", "plan_id", "building_id"]
    )
    plans_by_building_id = defaultdict(list)
    for floor in all_floors:
        plans_by_building_id[floor["building_id"]].append(floor)

    final_plans = set()
    for building_plans in plans_by_building_id.values():
        relevant_plans = [
            f["plan_id"] for f in building_plans if f["floor_number"] <= 0
        ]
        if not relevant_plans:  # take the lowest floor in this case
            relevant_plans = [
                sorted(building_plans, key=lambda p: p["floor_number"])[0]["plan_id"]
            ]
        final_plans.update(relevant_plans)

    try:
        return jsonify(
            {
                "features": [
                    {
                        "geometry": shapely_mapping(
                            project_geometry(
                                geometry=PlanLayoutHandler(plan_id=plan_id)
                                .get_georeferenced_footprint()
                                .simplify(1, preserve_topology=False),
                                crs_from=REGION[site_info["georef_region"]],
                                crs_to=REGION.LAT_LON,
                            )
                        ),
                        "type": "Feature",
                    }
                    for plan_id in final_plans
                ],
                "type": "FeatureCollection",
            }
        )
    except IndexError:
        # Plans are not georeferenced yet, but we allow interface to load with no exception
        return jsonify({})


@site_app.route("/net-area-distribution")
class NetAreaDistributionView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @site_app.response(schema=NetAreaDistributionSchema, status_code=HTTPStatus.OK)
    @site_app.arguments(SiteAnalysisQuery(partial=True), location="query")
    def get(self, query):
        if client_id := query.get("client_id"):
            # In this case you get a total number of units....
            result = ClientDBHandler.get_total_unit_number_by_site_id_completed(
                client_id=client_id
            )
        else:
            if unit_id := query.get("unit_id"):
                units = [UnitDBHandler.get_by(id=unit_id)]
            else:
                units = UnitDBHandler.get_joined_by_site_building_floor_id(**query)
            needs_all_units = query.get("building_id")
            #  Needed to display correct ph prices in the UI
            if needs_all_units:
                result = {
                    "floors": SiteHandler.get_net_area_distribution(
                        units=units, **query
                    ),
                    "units": SiteHandler._get_net_area_distribution(
                        units=units, index="id"
                    ),
                }
            else:
                result = SiteHandler.get_net_area_distribution(units=units, **query)
        return jsonify(result)


@site_app.route("/names")
class SiteNamesViewCollection(MethodView):
    class SiteNamesSchema(Schema):
        id = fields.Int()
        name = fields.Str()

    class QueryArgsSchema(Schema):
        client_id = fields.Int(required=True, allow_none=True)

    @role_access_control(roles={USER_ROLE.ADMIN})
    @site_app.response(schema=SiteNamesSchema, status_code=HTTPStatus.OK)
    @site_app.arguments(
        QueryArgsSchema, required=True, location="query", as_kwargs=True
    )
    def get(self, client_id: int):
        return jsonify(
            SiteDBHandler.find(client_id=client_id, output_columns=["id", "name"])
        )


@site_app.route("/<int:site_id>/task/<task_name>")
class SiteTaskView(MethodView):
    @staticmethod
    def _update_slam_status_if_not_processing(site_id: int) -> bool:
        site = SiteDBHandler.get_by(id=site_id, output_columns=["full_slam_results"])

        if site["full_slam_results"] in (
            ADMIN_SIM_STATUS.PENDING.name,
            ADMIN_SIM_STATUS.PROCESSING.name,
        ):
            raise ValidationError(f"site {site_id} is still processing!")

        return slam_results_success.si(site_id=site_id)

    @role_access_control(roles={USER_ROLE.ADMIN})
    @site_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
    def post(self, site_id: int, task_name: str):
        {
            "generate_unit_plots_task": lambda site_id: generate_unit_plots_task.si(
                site_id=site_id
            ),
            "generate_energy_reference_area_task": lambda site_id: generate_energy_reference_area_task.si(
                site_id=site_id
            ),
            "generate_ifc_file_task": lambda site_id: generate_ifc_file_task.si(
                site_id=site_id
            ),
            "generate_vector_files_task": lambda site_id: generate_vector_files_task.si(
                site_id=site_id
            ),
            "all_deliverables": lambda site_id: workflow(
                *WorkflowGenerator(site_id=site_id).get_deliverables_tasks(),
                run_in_parallel=True,
            ),
            "slam_results_success": self._update_slam_status_if_not_processing,
        }[task_name](site_id=site_id).delay()

        post_message_to_slack(
            text=f"The job {task_name} was triggered manually for site {site_id}.",
            channel="#tech-support",
        )

        return jsonify(
            msg=f"Successfully started task {task_name} for site with id [{site_id}]"
        )

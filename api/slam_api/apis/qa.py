import csv
from http import HTTPStatus
from io import BytesIO, StringIO

from flask import jsonify, request, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, ValidationError, fields, validates_schema

from common_utils.constants import USER_ROLE
from handlers import QAHandler
from handlers.db import QADBHandler
from handlers.db.qa_handler import QADataValuesSchema, TrimmedString
from slam_api.utils import role_access_control

qa_app = Blueprint("qa", __name__)


class QaGetBySchema(Schema):
    client_id = fields.Integer()
    client_site_id = fields.String()
    site_id = fields.Integer()

    @validates_schema
    def exclusive_fields(self, data, **kwargs):
        """
        Check if there is site_id or (client_site_id, client_id)
        but not both options at the same time
        """
        if (
            data.get("site_id")
            and any((data.get("client_id"), data.get("client_site_id")))
        ) or (
            not data.get("site_id")
            and (not data.get("client_id") or not data.get("client_site_id"))
        ):
            raise ValidationError(
                "There should only be site_id or (client_site_id, client_id)"
            )


class QaPutPostSchema(Schema):
    client_id = fields.Integer()
    client_site_id = TrimmedString()
    site_id = fields.Integer()
    data = fields.Dict(
        keys=TrimmedString(allow_none=False),
        values=fields.Nested(
            QADataValuesSchema(partial=False), required=True, allow_none=False
        ),
        allow_none=True,
    )


class QaTemplateHeaderFields(QADataValuesSchema):
    apartment_client_id = fields.Str()


@qa_app.route("/<int:qa_id>")
class QAView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @qa_app.arguments(QaPutPostSchema, location="json", as_kwargs=True)
    def put(self, qa_id: int, **kwargs):
        updated = QAHandler.update(qa_id=qa_id, new_values=kwargs)
        return jsonify(updated), HTTPStatus.OK

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    def delete(self, qa_id: int):
        QADBHandler.delete({"id": qa_id})
        return jsonify(msg="Deleted successfully")


@qa_app.route("/")
class QAViewCollection(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @qa_app.arguments(QaPutPostSchema, location="json", as_kwargs=True)
    def post(self, **kwargs):
        new_client = QADBHandler.add(**kwargs)
        return jsonify(new_client), HTTPStatus.CREATED

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    def get(self):
        errors = QaGetBySchema().validate(data=request.args)
        if errors:
            return (
                jsonify(
                    f"Invalid request parameters: {errors['_schema'] if '_schema' in errors else errors}"
                ),
                HTTPStatus.BAD_REQUEST,
            )

        qa_data = QAHandler.get_qa_data(
            site_id=request.args.get("site_id"),
            client_id_and_client_site_id=(
                request.args.get("client_id"),
                request.args.get("client_site_id"),
            ),
        )

        return jsonify(qa_data)


@qa_app.route("/template")
class QATemplateView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    def get(self):
        output_stream = StringIO()
        qa_template_header_fields = [
            fieldname for fieldname in QaTemplateHeaderFields().fields.keys()
        ]
        csv_writer = csv.DictWriter(output_stream, fieldnames=qa_template_header_fields)
        csv_writer.writeheader()
        output_stream.seek(0)

        return (
            send_file(
                BytesIO(output_stream.read().encode("UTF-8")),
                as_attachment=True,
                mimetype="text/csv",
                attachment_filename="template.csv",
            ),
            HTTPStatus.OK,
        )


@qa_app.route("/template_headers")
class QATemplateHeadersView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    def get(self):
        return (
            jsonify([fieldname for fieldname in QADataValuesSchema().fields.keys()]),
            HTTPStatus.OK,
        )

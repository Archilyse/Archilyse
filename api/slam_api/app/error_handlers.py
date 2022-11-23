from http import HTTPStatus

from flask import Flask, Response, jsonify
from flask_jwt_extended import unset_access_cookies
from marshmallow import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from common_utils.exceptions import (
    AreaMismatchException,
    CorruptedAnnotationException,
    DBException,
    DBNotFoundException,
    DBValidationException,
    GCSLinkEmptyException,
    InvalidRegion,
    JWTSignatureExpiredException,
    NetAreaDistributionUnsetException,
    QAMissingException,
    QAValidationException,
    SimulationNotSuccessException,
    UserAuthorizationException,
    ValidationException,
)
from common_utils.logger import logger


def register_error_handlers(app: Flask):  # noqa: C901
    @app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
    def all_exception_handler(error):
        logger.debug(str(error))
        return (
            jsonify(msg=f"Unexpected Error: {error}"),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @app.errorhandler(UserAuthorizationException)
    def handle_access_forbidden(error):
        return jsonify(msg=str(error)), HTTPStatus.FORBIDDEN

    @app.errorhandler(JWTSignatureExpiredException)
    def handle_jwt_token_signature(error):
        response = Response(
            {"msg": str(error)},
            mimetype="application/json",
            status=HTTPStatus.FORBIDDEN,
        )
        unset_access_cookies(response)
        return response

    @app.errorhandler(DBNotFoundException)
    @app.errorhandler(NoResultFound)
    def handle_not_found(e):
        return jsonify(msg=f"Entity not found! {e}"), HTTPStatus.NOT_FOUND

    @app.errorhandler(DBValidationException)
    def handle_bad_validation_request(e):
        return jsonify(msg=f"Entity is not acceptable! {e}"), HTTPStatus.BAD_REQUEST

    @app.errorhandler(ValidationException)
    def handle_validation_request(e):
        return jsonify(msg=f"Internal error: {e}"), HTTPStatus.BAD_REQUEST

    @app.errorhandler(CorruptedAnnotationException)
    def handle_corrupted_annotation_error(e):
        return (
            jsonify(msg=f"Internal error with the annotations: {e}"),
            HTTPStatus.BAD_REQUEST,
        )

    @app.errorhandler(DBException)
    def handle_bad_db_error_request(e):
        return (
            jsonify(msg=f"Entity is not acceptable! {e}"),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    @app.errorhandler(GCSLinkEmptyException)
    def handle_emtpy_link(error):
        return jsonify(msg=str(error)), HTTPStatus.NOT_FOUND

    @app.errorhandler(InvalidRegion)
    def handle_invalid_region(e):
        return jsonify(msg=f"Invalid region! {e}"), HTTPStatus.BAD_REQUEST

    @app.errorhandler(QAValidationException)
    def handle_qa_validation_error(e):
        return jsonify(msg=str(e)), HTTPStatus.BAD_REQUEST

    @app.errorhandler(QAMissingException)
    def handle_qa_missing(e: QAMissingException):
        return (
            jsonify(
                msg=f"There is no QA data available for site with id {e.site_id}. "
                "Please provide the information from the Edit Site view."
            ),
            HTTPStatus.NOT_FOUND,
        )

    @app.errorhandler(SimulationNotSuccessException)
    def handle_simulation_not_success(e: SimulationNotSuccessException):
        return jsonify(msg=str(e)), HTTPStatus.BAD_REQUEST

    @app.errorhandler(AreaMismatchException)
    def handle_area_mismatch_exception(e: AreaMismatchException):
        return jsonify(msg=str(e)), HTTPStatus.BAD_REQUEST

    @app.errorhandler(NetAreaDistributionUnsetException)
    def handle_not_defined_net_area_params(e: AreaMismatchException):
        return jsonify(msg=str(e)), HTTPStatus.BAD_REQUEST

    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation_exception(e):
        return jsonify(msg=e.messages), HTTPStatus.UNPROCESSABLE_ENTITY

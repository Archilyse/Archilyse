import os
import warnings
from uuid import uuid4

import click
from flask import jsonify, request
from flask_jwt_extended import JWTManager

from alembic_utils.utils import alembic_downgrade_base as downgrade_base
from alembic_utils.utils import (
    alembic_upgrade_head,
    check_no_pending_migrations,
    check_scripts_do_not_have_conflicts,
    downgrade_version,
    generate_migration_script,
)
from common_utils.constants import (
    get_security_password_salt,
    get_slam_secret_key,
    get_slam_version,
)
from common_utils.logger import logger
from common_utils.logging_config import configure_logging
from connectors.db_connector import create_db_if_not_exists, db_url, get_alembic_version
from slam_api.app.apm import setup_apm

from .apis import setup_apis
from .cors import setup_cors
from .error_handlers import register_error_handlers
from .flask_app import reFlask as Flask
from .json_utils import SlamJSONEncoder
from .logging import ApiLogFormatter, global_current_request_id

configure_logging(formatter=ApiLogFormatter)


app = Flask("SLAM API")

app.config["SECRET_KEY"] = get_slam_secret_key()
app.config["SECURITY_PASSWORD_SALT"] = get_security_password_salt()


# SQLALCHEMY
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# API DOCUMENTATION ####################################################################
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "api/docs"

app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
app.config["OPENAPI_SWAGGER_UI_VERSION"] = "3.28.0"
app.config[
    "OPENAPI_SWAGGER_UI_URL"
] = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.28.0/"


# JWT ##################################################################################
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "slam-auth"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False


app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 60 * 60 * 24 * 15)
)

#
# HACK: due `marshmallow` UserWarning: Multiple schemas warning, as the fix of it will
#       involve the refactor of the many schemas and endpoint definitions, I've decided
#       to ignoring these warnings as the cause no harm as Smorest is already handling
#       the  multiple schema definition.
#
warnings.filterwarnings("ignore", module="apispec", category=UserWarning)

jwt = JWTManager(app)


########################################################################################
setup_cors(app)
setup_apis(app)
setup_apm(_app=app)
register_error_handlers(app)

# Override default JSON encoder
app.json_encoder = SlamJSONEncoder
########################################################################################


@app.route("/api/_internal_/ping")
def flask_api_ping():
    return jsonify("pong")


@app.route("/api/_internal_/check")
def flask_api_check():
    return jsonify({"slam_version": get_slam_version(), **get_alembic_version()})


@app.cli.command()
def alembic_autogenerate_revision():
    generate_migration_script()


@app.cli.command()
def alembic_downgrade_base():
    downgrade_base()


@app.cli.command()
def post_deployment_tasks():
    from tasks.annotations_migration_tasks import migrate_all_react_annotations

    migrate_all_react_annotations.delay()


@app.cli.command()
@click.argument("version")
def alembic_downgrade_version(version):
    downgrade_version(version)


@app.cli.command()
def alembic_checks():
    logger.info("Running alembic checks")
    check_scripts_do_not_have_conflicts()
    check_no_pending_migrations()
    logger.info("Executed alembic checks")


@app.cli.command()
def create_database_and_upgrade():
    logger.info("Creating db if not exists")
    create_db_if_not_exists()
    logger.info("Applying migrations")
    alembic_upgrade_head()
    logger.info("Applied migrations, if any")


@app.before_request
def _set_global_logging_request_id():
    request.request_id = uuid4().hex
    global_current_request_id.set_id(request.request_id)

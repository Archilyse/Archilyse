#
# This script is very useful to download data from the staging DB
# It needs a site_id and it should download to your local DB all related entities
# It does optionally copy data from prod buckets to your personal ones
import os
from typing import Optional, Type

import click
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.orm import Session, joinedload
from tqdm import tqdm

from common_utils.constants import GOOGLE_CLOUD_BUCKET, GOOGLE_CLOUD_LOCATION
from common_utils.logger import logger
from db_models import ReactPlannerProjectDBModel
from handlers import GCloudStorageHandler
from handlers.db import (
    BaseDBHandler,
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_client_bucket_name


@click.command()
@click.option("--site_id", prompt=True, type=click.INT)
@click.option("--include_units", prompt=True, default=False, type=click.BOOL)
@click.option("--include_gcs_copy", prompt=True, default=False, type=click.BOOL)
def main(
    site_id,
    include_units,
    include_gcs_copy,
):
    from db_models import (
        AnnotationDBModel,
        BuildingDBModel,
        ClientDBModel,
        ExpectedClientDataDBModel,
        FloorDBModel,
        PlanDBModel,
        SiteDBModel,
        SlamSimulationDBModel,
        UnitDBModel,
        UnitSimulationDBModel,
        UserDBModel,
    )

    """ This script is very useful to download data from the staging DB
        It needs a site_id and it should download to your local DB all related entities
        It does optionally copy data from prod buckets to your personal ones
    """
    logger.info("\nRetrieving info from DB...")  # noqa: T001

    session = orm.sessionmaker()

    local_engine = sqlalchemy.create_engine(
        "postgresql+psycopg2://postgres:changeme@pgbouncer:5439/slam"
    )
    local_session = session(bind=local_engine)
    remote_engine = sqlalchemy.create_engine(
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['PGBOUNCER_HOST']}:{os.environ['PGBOUNCER_PORT']}/slam"
    )
    remote_session = session(bind=remote_engine)
    to_add = []

    # retrieves clients
    to_add.extend(remote_session.query(ClientDBModel).all())
    # retrieves users
    to_add.extend(
        remote_session.query(UserDBModel)
        .options(joinedload("roles"))
        .options(joinedload("group"))
        .all()
    )

    # retrieve site
    site = (
        remote_session.query(SiteDBModel)
        .filter(SiteDBModel.id == site_id)
        .options(joinedload("group"))
        .one()
    )
    to_add.append(site)

    # retrieve buildings
    buildings = (
        remote_session.query(BuildingDBModel)
        .filter(BuildingDBModel.site_id == site_id)
        .all()
    )
    to_add.extend(buildings)

    # retrieve plans
    plans = (
        remote_session.query(PlanDBModel).filter(PlanDBModel.site_id == site_id).all()
    )
    to_add.extend(plans)

    # retrieve annotations
    to_add.extend(
        remote_session.query(AnnotationDBModel)
        .filter(AnnotationDBModel.plan_id.in_(p.id for p in plans))
        .all()
    )

    # retrieve floors
    to_add.extend(
        remote_session.query(FloorDBModel)
        .filter(FloorDBModel.building_id.in_(b.id for b in buildings))
        .all()
    )

    # retrieve qa data
    to_add.extend(
        remote_session.query(ExpectedClientDataDBModel)
        .filter(ExpectedClientDataDBModel.site_id == site_id)
        .all()
    )

    to_add.extend(
        remote_session.query(ReactPlannerProjectDBModel)
        .filter(ReactPlannerProjectDBModel.plan_id.in_(p.id for p in plans))
        .all()
    )

    if include_units:
        # retrieve units
        units = (
            remote_session.query(UnitDBModel)
            .filter(UnitDBModel.site_id == site_id)
            .all()
        )
        to_add.extend(units)

        simulations = (
            remote_session.query(SlamSimulationDBModel)
            .filter(SlamSimulationDBModel.site_id == site_id)
            .all()
        )

        to_add.extend(simulations)

        unit_results = (
            remote_session.query(UnitSimulationDBModel)
            .filter(UnitSimulationDBModel.run_id.in_(s.run_id for s in simulations))
            .all()
        )
        to_add.extend(unit_results)

        # retrieve areas
        retrieve_areas(plans=plans, session=remote_session, accumulator=to_add)

    # copy data around
    remote_session.expunge_all()
    for element in to_add:
        local_session.merge(element)

    logger.info(f"A total of {len(to_add)} rows downloaded")  # noqa: T001

    if include_gcs_copy:
        logger.info("Updating personal Google Cloud Bucket...")  # noqa: T001
        create_buckets_if_not_exists()
        retrieve_gcs_data(
            site_id=site_id, include_units=include_units, session=local_session
        )
        logger.info("Personal Google Cloud Bucket Updated")  # noqa: T001

    local_session.commit()
    local_session.close()


def retrieve_areas(session, plans, accumulator):
    from db_models import AreaDBModel, UnitsAreasDBModel

    for plan in plans:
        areas = session.query(AreaDBModel).filter(AreaDBModel.plan_id == plan.id).all()
        accumulator.extend(areas)
        accumulator.extend(
            session.query(UnitsAreasDBModel).filter(
                UnitsAreasDBModel.area_id.in_(a.id for a in areas)
            )
        )


# **************************
# GCS COPY LOGIC
# **************************
def create_buckets_if_not_exists():
    GCloudStorageHandler().create_bucket_if_not_exists(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        location=GOOGLE_CLOUD_LOCATION,
        predefined_acl="public-read",
        predefined_default_object_acl="public-read",
    )


def retrieve_gcs_data(site_id: int, include_units: bool, session: Session):
    logger.info("Updating site and client links...")  # noqa: T001
    site = SiteDBHandler.get_by(id=site_id)
    entity_update_gcs_links(SiteDBHandler, site, session)
    # Update client:
    entity_update_gcs_links(
        ClientDBHandler, ClientDBHandler.get_by(id=site["client_id"]), session
    )
    # Update buildings and floors:
    for building in tqdm(BuildingDBHandler.find(site_id=site_id), "Buildings"):
        entity_update_gcs_links(BuildingDBHandler, building, session)
        for floor in tqdm(FloorDBHandler.find(building_id=building["id"]), "Floors"):
            entity_update_gcs_links(FloorDBHandler, floor, session)
    # Update plans:
    for plan in tqdm(PlanDBHandler.find(site_id=site_id), "Plans"):
        plan_upade_raw_file_link(PlanDBHandler, plan, site["client_id"], session)

    # Update units:
    if include_units:
        for unit in tqdm(UnitDBHandler.find(site_id=site_id), "Units"):
            entity_update_gcs_links(UnitDBHandler, unit, session)


def plan_upade_raw_file_link(
    handler: Type[PlanDBHandler],
    entity: dict,
    client_id: int,
    session: Session,
):
    current_plan_image_link = entity["image_gcs_link"]
    new_plan_image_link = copy_gcs_data(current_plan_image_link, client_id=client_id)
    session.query(handler.model).filter_by(id=entity["id"]).update(
        {"image_gcs_link": new_plan_image_link}
    )


def entity_update_gcs_links(
    entity_handler: Type[BaseDBHandler], entity: dict, session: Session
):
    to_update = {}
    for field, value in entity.items():
        if "gcs" in field and "link" in field and value:
            new_value = copy_gcs_data(value)
            to_update[field] = new_value
    session.query(entity_handler.model).filter_by(id=entity["id"]).update(to_update)


def copy_gcs_data(link: str, client_id: Optional[int] = None):
    source_bucket_name = "archilyse-slam-pipeline"
    destination_bucket_name = GOOGLE_CLOUD_BUCKET
    if "archilyse_client_" in link:
        source_bucket_name = f"archilyse_client_{client_id}"
        destination_bucket_name = get_client_bucket_name(client_id=client_id)
        GCloudStorageHandler().create_bucket_if_not_exists(
            bucket_name=destination_bucket_name,
            location=GOOGLE_CLOUD_LOCATION,
            predefined_acl="public-read",
            predefined_default_object_acl="public-read",
        )

    return GCloudStorageHandler().copy_file_to_another_bucket(
        source_bucket_name=source_bucket_name,
        media_link=link,
        destination_bucket_name=destination_bucket_name,
    )


if __name__ == "__main__":
    main()

import functools
from typing import Any, Callable, Type

from sqlalchemy import and_

from common_utils.constants import USER_ROLE
from common_utils.exceptions import (
    UnsupportedDBModelException,
    UserAuthorizationException,
)
from connectors.db_connector import BaseDBModel, get_db_session_scope
from db_models import (
    AreaDBModel,
    BuildingDBModel,
    ClientDBModel,
    FloorDBModel,
    PlanDBModel,
    SiteDBModel,
    UnitDBModel,
    UnitsAreasDBModel,
)
from db_models.db_entities import CompetitionDBModel, FolderDBModel, UserDBModel
from slam_api.utils import get_user_authorized


def validate_client_ownership(user: dict, **keys) -> bool:
    if user["client_id"] is not None:
        return user["client_id"] == keys.get("id")
    return True


def validate_site_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = s.query(SiteDBModel).filter_by(**keys, client_id=user["client_id"])
        return s.query(query.exists()).scalar()


def validate_plan_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = (
            s.query(PlanDBModel)
            .filter_by(**keys)
            .join(SiteDBModel)
            .filter(SiteDBModel.client_id == user["client_id"])
        )
        return s.query(query.exists()).scalar()


def validate_unit_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = (
            s.query(UnitDBModel)
            .filter_by(**keys)
            .join(
                SiteDBModel,
                and_(
                    SiteDBModel.id == UnitDBModel.site_id,
                    SiteDBModel.client_id == user["client_id"],
                ),
            )
        )
        return s.query(query.exists()).scalar()


def validate_floor_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = (
            s.query(FloorDBModel)
            .filter_by(**keys)
            .join(BuildingDBModel, FloorDBModel.building_id == BuildingDBModel.id)
            .join(SiteDBModel, SiteDBModel.id == BuildingDBModel.site_id)
            .filter(SiteDBModel.client_id == user["client_id"])
        )

        return s.query(query.exists()).scalar()


def validate_folder_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = s.query(FolderDBModel).filter_by(**keys, client_id=user["client_id"])
        return s.query(query.exists()).scalar()


def validate_user_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = s.query(UserDBModel).filter_by(**keys, client_id=user["client_id"])
        return s.query(query.exists()).scalar()


def validate_area_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = (
            s.query(AreaDBModel)
            .filter_by(**keys)
            .join(UnitsAreasDBModel, AreaDBModel.id == UnitsAreasDBModel.area_id)
            .join(UnitDBModel, UnitDBModel.id == UnitsAreasDBModel.unit_id)
            .join(
                SiteDBModel,
                and_(
                    SiteDBModel.id == UnitDBModel.site_id,
                    SiteDBModel.client_id == user["client_id"],
                ),
            )
        )
        return s.query(query.exists()).scalar()


def validate_competition_ownership(user: dict, **keys) -> bool:
    with get_db_session_scope(readonly=True) as s:
        query = s.query(CompetitionDBModel).filter_by(
            **keys, client_id=user["client_id"]
        )
        return s.query(query.exists()).scalar()


VALIDATOR_MAP = {
    ClientDBModel: validate_client_ownership,
    SiteDBModel: validate_site_ownership,
    PlanDBModel: validate_plan_ownership,
    FloorDBModel: validate_floor_ownership,
    UnitDBModel: validate_unit_ownership,
    FolderDBModel: validate_folder_ownership,
    UserDBModel: validate_user_ownership,
    AreaDBModel: validate_area_ownership,
    CompetitionDBModel: validate_competition_ownership,
}


def _entity_is_owned_by_client(
    db_model: Type[SiteDBModel],
    user: dict,
    keys: dict[str, Any],
) -> bool:
    return VALIDATOR_MAP[db_model](user=user, **keys)


def validate_entity_ownership(
    db_model: Type[BaseDBModel],
    key_selector: Callable,
):
    if db_model not in VALIDATOR_MAP:
        raise UnsupportedDBModelException(
            f"Entity ownership validation is currently not supported for db model {db_model.__name__}. "
            f"To support it please create a validator method and add it to VALIDATOR_MAP."
        )

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            current_user = get_user_authorized()
            if USER_ROLE.ADMIN not in current_user["roles"]:
                if _entity_is_owned_by_client(
                    db_model=db_model,
                    user=current_user,
                    keys=key_selector(kwargs),
                ):
                    return function(*args, **kwargs)
                raise UserAuthorizationException(
                    "Access to this resource is forbidden."
                )
            return function(*args, **kwargs)

        return wrapper

    return decorator

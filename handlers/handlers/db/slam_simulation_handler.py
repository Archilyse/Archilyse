from collections import defaultdict
from typing import Dict, Iterable, Optional, Set

from marshmallow_enum import EnumField
from sqlalchemy import func

from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from common_utils.exceptions import DBNotFoundException
from db_models import SlamSimulationDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class SlamSimulationDBSchema(BaseDBSchema):
    state = EnumField(ADMIN_SIM_STATUS, by_value=False)
    type = EnumField(TASK_TYPE, by_value=False)

    class Meta(BaseDBSchema.Meta):
        model = SlamSimulationDBModel


class SlamSimulationDBHandler(BaseDBHandler):
    schema = SlamSimulationDBSchema()
    model = SlamSimulationDBModel

    @classmethod
    def _max_created(cls, session, site_id: int, task_type: TASK_TYPE):
        return (
            session.query(func.max(cls.model.created).label("created"))
            .filter_by(site_id=site_id, type=task_type.name)
            .subquery()
        )

    @classmethod
    def check_state(
        cls, site_id: int, task_type: TASK_TYPE, states: Iterable[ADMIN_SIM_STATUS]
    ) -> bool:
        with cls.begin_session(readonly=True) as s:
            max_created = cls._max_created(
                session=s, site_id=site_id, task_type=task_type
            )
            return s.query(
                s.query(cls.model)
                .join(max_created, max_created.c.created == cls.model.created)
                .filter(
                    cls.model.site_id == site_id,
                    cls.model.type == task_type.name,
                    cls.model.state.in_([state.name for state in states]),
                )
                .exists()
            ).scalar()

    @classmethod
    def get_latest_run_id(
        cls,
        site_id: int,
        task_type: TASK_TYPE,
        state: Optional[ADMIN_SIM_STATUS] = None,
    ) -> str:
        with cls.begin_session(readonly=True) as s:
            simulation = s.query(cls.model.run_id).filter_by(
                site_id=site_id, type=task_type.name
            )

            if state:
                simulation = simulation.filter_by(state=state)

            simulation = simulation.order_by(cls.model.created.desc()).first()

        if not simulation:
            raise DBNotFoundException(
                f"No simulation found for site {site_id} and task type {task_type.name}"
            )
        return simulation.run_id

    @classmethod
    def get_latest_run_ids(
        cls,
        site_id: int,
        task_types: Set[TASK_TYPE],
        state: Optional[ADMIN_SIM_STATUS] = None,
    ) -> Dict[str, TASK_TYPE]:
        state = state or ADMIN_SIM_STATUS.SUCCESS
        with cls.begin_session(readonly=True) as s:
            latest_simulations = (
                s.query(
                    cls.model.run_id,
                    cls.model.created,
                    cls.model.type,
                )
                .filter(
                    cls.model.site_id == site_id,
                    cls.model.state == state,
                    cls.model.type.in_(task_types),
                )
                .all()
            )

            groups = defaultdict(list)
            for s in latest_simulations:
                groups[s.type].append(s)

            return {
                max(simulations, key=lambda s: s.created).run_id: task_type
                for task_type, simulations in groups.items()
            }

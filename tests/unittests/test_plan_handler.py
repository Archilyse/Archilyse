from unittest.mock import PropertyMock

import psycopg2
import pytest
from deepdiff import DeepDiff

from handlers import PlanHandler, PlanLayoutHandler
from handlers.db import PlanDBHandler


@pytest.mark.parametrize(
    "plan_id, expected_unit_sizes",
    [
        (
            332,
            (5, 5, 5, 6, 6, 6, 6, 6),
        ),  # 1 apartment has a shaft
        (863, (3, 8)),
        (2494, (5, 5, 5, 5, 5, 5, 6, 6, 6)),
        (3332, (12, 14)),
        (3354, (9, 10, 13)),
        (3489, (8, 8, 10, 10, 11, 14, 15, 16, 16)),
        (4976, (5, 5, 6, 6, 7)),
        (5797, (1, 5, 7, 8)),
        (5825, (9, 10, 12)),
        (
            6380,
            (9, 12, 12, 13, 14),
        ),
        (
            6951,
            (8, 9, 10, 14),
        ),  # One of the shafts is incorrectly assigned, although is not obviously wrong
        (7641, [1, 1, 2, 2, 2, 2]),
    ],
)
def test_auto_splitting(
    mocker,
    layout_scaled_classified_wo_db_conn,
    plan_id,
    expected_unit_sizes,
):
    """
    To visualize the results:
    from brooks.visualization.debug.visualisation import draw

    areas_by_db_id = {x.db_area_id: x for x in layout.areas}
    for apartment in response:
        draw([areas_by_db_id[x].footprint for x in apartment])

    """
    layout = layout_scaled_classified_wo_db_conn(plan_id)
    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout)
    response = PlanHandler(plan_id=plan_id).autosplit()

    assert sorted([len(x) for x in response]) == sorted(expected_unit_sizes)


@pytest.mark.parametrize(
    "plan_id, expected_coord",
    [
        (332, (26.414869304013505, 16.282979045472246)),
        (863, (19.459947517164546, 13.225538394212922)),
    ],
)
def test_plan_handler_calculate_rotation_point(
    mocker,
    layout_scaled_classified_wo_db_conn,
    plan_id,
    expected_coord,
):
    _ = mocker.patch.object(
        PlanLayoutHandler,
        "get_layout",
        return_value=layout_scaled_classified_wo_db_conn(annotation_plan_id=plan_id),
    )
    db_update_mocked = mocker.patch.object(PlanDBHandler, "update")
    rotation_point = PlanHandler(
        plan_id=plan_id, plan_info={"id": plan_id}
    ).rotation_point
    assert not DeepDiff(
        expected_coord, (rotation_point.x, rotation_point.y), significant_digits=3
    )
    db_update_mocked.assert_called_once_with(
        item_pks={"id": plan_id},
        new_values={
            "georef_rot_x": rotation_point.x,
            "georef_rot_y": rotation_point.y,
        },
    )


def test_set_as_masterplan_retries(mocker):
    mocker.patch.object(PlanDBHandler, "find", return_value=[])
    mocker.patch.object(PlanDBHandler, "get_by", return_value={"building_id": 1})
    mocker.patch.object(
        PlanHandler, "_update_building_plans_with_georef_data", return_value=[]
    )
    mocker.patch.object(
        PlanHandler,
        "is_georeferenced",
        PropertyMock(return_value=True),
    )

    mocked_bulk_update = mocker.patch.object(
        PlanDBHandler,
        "bulk_update",
        side_effect=[psycopg2.errors.SerializationFailure("test"), None],
    )
    PlanHandler(plan_id=1).set_as_masterplan()
    assert mocked_bulk_update.call_count == 2


class TestSaveGeorefData:
    @pytest.fixture
    def mocked_plans(self, mocker):
        def _internal(plan_info, plans_of_same_building=None):
            from handlers.plan_handler import PlanDBHandler

            mocker.patch.object(
                PlanHandler, "plan_info", PropertyMock(return_value=plan_info)
            )
            mocker.patch.object(
                PlanDBHandler,
                "find",
                return_value=plans_of_same_building or [plan_info],
            )

        return _internal

    @pytest.fixture
    def mocked_set_site_to_unprocessed(self, mocker):
        from handlers.plan_handler import SiteDBHandler

        return mocker.patch.object(SiteDBHandler, "set_site_to_unprocessed")

    def test_save_georef_data_resets_site_state(
        self, mocker, mocked_plans, mocked_set_site_to_unprocessed
    ):
        from handlers.plan_handler import PlanDBHandler

        georef_data = {"georef_rot_angle": 0, "georef_x": 4, "georef_y": 5}
        plan_id = 1
        site_id = 2

        mocked_plans(
            plan_info={
                "id": plan_id,
                "site_id": site_id,
                "building_id": 3,
                "georef_rot_x": 1,
                "georef_rot_y": 2,
                "is_masterplan": False,
            }
        )
        mocker.patch.object(PlanDBHandler, "update")

        PlanHandler(plan_id=plan_id).save_georeference_data(georef_data=georef_data)

        mocked_set_site_to_unprocessed.assert_called_once_with(site_id=site_id)

    def test_save_georef_data_no_masterplan(
        self, mocker, mocked_plans, mocked_set_site_to_unprocessed
    ):
        from handlers.plan_handler import PlanDBHandler

        georef_data = {"georef_rot_angle": 0, "georef_x": 4, "georef_y": 5}
        plan_id = 1

        mocked_plans(
            plan_info={
                "id": plan_id,
                "site_id": 2,
                "building_id": 3,
                "georef_rot_x": 1,
                "georef_rot_y": 2,
                "is_masterplan": False,
            }
        )
        mocked_db_update = mocker.patch.object(PlanDBHandler, "update")

        PlanHandler(plan_id=plan_id).save_georeference_data(georef_data=georef_data)

        mocked_db_update.assert_called_once_with(
            item_pks=dict(id=plan_id), new_values=georef_data
        )

    def test_save_georef_data_with_masterplan(
        self, mocker, mocked_plans, mocked_set_site_to_unprocessed
    ):
        from handlers.plan_handler import PlanDBHandler

        georef_data = {"georef_rot_angle": 0, "georef_x": 4, "georef_y": 5}

        plan_info = {
            "id": 1,
            "site_id": 2,
            "building_id": 3,
            "georef_rot_x": 1,
            "georef_rot_y": 2,
        }
        plans_of_same_building = [
            {"id": 1, "is_masterplan": False},
            {"id": 2, "is_masterplan": True},
        ]
        mocked_plans(plan_info=plan_info, plans_of_same_building=plans_of_same_building)
        mocked_db_update = mocker.patch.object(PlanDBHandler, "bulk_update")

        PlanHandler(plan_id=plan_info["id"]).save_georeference_data(
            georef_data=georef_data
        )

        mocked_db_update.assert_called_once_with(
            **{
                key: {plan["id"]: value for plan in plans_of_same_building}
                for key, value in dict(
                    **georef_data,
                    georef_rot_x=plan_info["georef_rot_x"],
                    georef_rot_y=plan_info["georef_rot_y"],
                ).items()
            }
        )

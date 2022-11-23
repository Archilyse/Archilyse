from shapely.geometry import box

from brooks.models import SimArea, SimLayout, SimSpace
from brooks.types import AreaType
from common_utils.constants import UNIT_USAGE
from handlers import SiteHandler, SlamSimulationHandler
from handlers.db import UnitDBHandler
from tasks.rectangulator_tasks import AREA_TYPES_TO_EXCLUDE, biggest_rectangle_task


def test_biggest_rectangle_task(mocker):
    fake_residential_unit_id = 1
    fake_residential_unit_id_2 = 2
    fake_commercial_unit_id = 3

    fake_db_area_id = 1
    fake_footprint = box(0, 0, 1, 1)
    fake_unit_layout = SimLayout()
    fake_unit_layout.add_spaces(
        {
            SimSpace(
                height=mocker.ANY,
                footprint=fake_footprint,
                areas={
                    SimArea(
                        footprint=fake_footprint,
                        area_type=AreaType.ROOM,
                        db_area_id=fake_db_area_id,
                    ),
                    *[
                        SimArea(
                            footprint=fake_footprint,
                            area_type=area_type_to_exclude,
                            db_area_id=area_id,
                        )
                        for area_id, area_type_to_exclude in enumerate(
                            AREA_TYPES_TO_EXCLUDE, start=2
                        )
                    ],
                },
            )
        }
    )

    mocked_residential_unit_ids = mocker.patch.object(
        UnitDBHandler,
        "find_ids",
        return_value=[fake_residential_unit_id, fake_residential_unit_id_2],
    )
    mocked_get_unit_layouts = mocker.patch.object(
        SiteHandler,
        "get_unit_layouts",
        return_value=[
            ({"id": fake_residential_unit_id}, fake_unit_layout),
            ({"id": fake_residential_unit_id_2}, fake_unit_layout),
            ({"id": fake_commercial_unit_id}, fake_unit_layout),
        ],
    )
    mocked_store_results = mocker.patch.object(SlamSimulationHandler, "store_results")

    fake_site_id = 1
    fake_run_id = "just-a-fake-rectangle-simulation"
    biggest_rectangle_task(run_id=fake_run_id, site_id=fake_site_id)

    mocked_residential_unit_ids.assert_called_once_with(
        site_id=fake_site_id, unit_usage=UNIT_USAGE.RESIDENTIAL.name
    )
    mocked_get_unit_layouts.assert_called_once_with(site_id=fake_site_id, scaled=True)
    mocked_store_results.assert_called_once_with(
        run_id=fake_run_id,
        results={
            fake_residential_unit_id: {fake_db_area_id: fake_footprint.wkt},
            fake_residential_unit_id_2: {fake_db_area_id: fake_footprint.wkt},
        },
    )

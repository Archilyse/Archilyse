from csv import DictWriter
from tempfile import NamedTemporaryFile

from deepdiff import DeepDiff

from bin.reports.gross_m2_by_site import calculate_areas_by_plan, write_report_by_site
from handlers.db import ClientDBHandler, FloorDBHandler, SiteDBHandler


def test_calculate_site_areas(first_pipeline_complete_db_models, mocker):
    mocker.patch.object(
        FloorDBHandler,
        "find",
        return_value=["pretend_to_find", "2_floors_for_the_plan"],
    )
    site = first_pipeline_complete_db_models["site"]
    result = calculate_areas_by_plan(site_id=site["id"])
    total_unit_area = sum(
        values["unit_area"] * values["nbr_of_floors"] for values in result[1].values()
    )
    total_public_area = sum(
        values["public_area"] * values["nbr_of_floors"] for values in result[1].values()
    )
    total_wall_area = sum(
        values["wall_area"] * values["nbr_of_floors"] for values in result[1].values()
    )
    assert not DeepDiff(
        {
            "total_unit_area": 147.782,
            "total_public_area": 156.629,
            "total_wall_area": 62.1233,
        },
        {
            "total_unit_area": total_unit_area,
            "total_public_area": total_public_area,
            "total_wall_area": total_wall_area,
        },
        significant_digits=3,
    )


def test_write_report(client_db, site, mocker):
    with NamedTemporaryFile(mode="w") as f:
        area_by_site_and_type = {
            site["id"]: {
                1: {
                    "unit_area": 1,
                    "public_area": 2,
                    "wall_area": 3,
                    "nbr_of_floors": 2,
                }
            }
        }
        writerow_spy = mocker.spy(DictWriter, "writerow")
        write_report_by_site(
            areas_by_site_and_plans=area_by_site_and_type,
            sites_info={site["id"]: SiteDBHandler.get_by(id=site["id"])},
            client_by_id={client_db["id"]: ClientDBHandler.get_by(id=client_db["id"])},
            filename=f.name,
        )
        assert writerow_spy.call_count == 2
        assert writerow_spy.call_args_list[1][0][1]["unit_area"] == 1
        assert writerow_spy.call_args_list[1][0][1]["public_area"] == 2
        assert writerow_spy.call_args_list[1][0][1]["wall_area"] == 3
        assert writerow_spy.call_args_list[1][0][1]["nbr_of_floors"] == 2
        assert writerow_spy.call_args_list[1][0][1]["total_plan_area"] == 6
        assert writerow_spy.call_args_list[1][0][1]["total_floor_area"] == 12

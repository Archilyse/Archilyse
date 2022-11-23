import math

import pytest

from brooks.types import AreaType
from common_utils.constants import (
    DB_INDEX_ANF,
    DB_INDEX_HNF,
    DB_INDEX_NET_AREA,
    DB_INDEX_ROOM_NUMBER,
    QA_VALIDATION_CODES,
    UNIT_USAGE,
)
from common_utils.exceptions import DBValidationException
from handlers import PlanLayoutHandler, QAHandler, SlamSimulationHandler
from handlers.db import (
    AreaDBHandler,
    PlanDBHandler,
    QADBHandler,
    ReactPlannerProjectsDBHandler,
    UnitDBHandler,
)
from handlers.db.qa_handler import (
    INDEX_HNF_AREA,
    INDEX_ROOM_NUMBER,
    QA_COLUMN_HEADERS,
    QADataValuesSchema,
)
from handlers.editor_v2 import ReactPlannerHandler
from handlers.validators import (
    GeoreferencingValidator,
    PlanClassificationRoomWindowValidator,
)
from handlers.validators.linking.unit_linking_validator import UnitLinkingValidator


def qa_values(missing_column: str = None, extra_column: str = None):
    values = {
        "client_building_id": "11",
        "number_of_rooms": 11.0,
        "HNF": 11.0,
        "ANF": 11.0,
        "net_area": 11.0,
        "street": "11",
        "floor": 11,
    }
    if extra_column:
        values[extra_column] = None
    if missing_column:
        values.pop(missing_column)
    return values


def qa_data(missing_column: str = None, extra_column: str = None):
    return {"bla.bla.bla": qa_values(missing_column, extra_column)}


def test_add_qa_data_with_invalid_data_types(site):
    with pytest.raises(DBValidationException):
        QADBHandler.add(
            site_id=site["id"],
            client_site_id=site["client_site_id"],
            client_id=site["client_id"],
            data={
                "abc.def.g.hhh": {
                    "client_building_id": 1  # building number should be a string
                }
            },
        )


def test_load_expected_qa_data():
    loaded = QADataValuesSchema().load(qa_values())
    assert loaded["client_building_id"] == "11"
    assert loaded["number_of_rooms"] == 11.0
    assert loaded["HNF"] == 11.0
    assert loaded["ANF"] == 11.0
    assert loaded["net_area"] == 11.0
    assert loaded["street"] == "11"
    assert loaded["floor"] == 11


def test_load_and_dump_qa_data_with_missing_column():
    schema = QADataValuesSchema()
    # missing column will be not be loaded
    loaded = schema.load(qa_values(missing_column=INDEX_ROOM_NUMBER))
    assert INDEX_ROOM_NUMBER not in loaded
    # missing column is dumped with default value
    dumped = schema.dump(loaded)
    assert dumped[INDEX_ROOM_NUMBER] is None


def test_load_null_values():
    loaded = QADataValuesSchema().load({"ANF": " ", "HNF": ""})
    assert loaded["ANF"] is None
    assert loaded["HNF"] is None


def test_qa_handler_add_and_get_qa(make_clients, make_sites, make_qa_data):
    # Checks same client_site_id with different client_ids
    clients = make_clients(2)
    site1, site2 = make_sites(*clients, client_site_id="Arnold")
    qa1, qa2 = make_qa_data(*(site1, site2))
    assert qa1 == QADBHandler.get_by(site_id=site1["id"])
    assert qa2 == QADBHandler.get_by(site_id=site2["id"])


def test_add_qa_missing_column(client_db, site):
    # when we upload a qa sheet with a missing column
    data = qa_data(missing_column=INDEX_ROOM_NUMBER)
    added = QADBHandler.add(site_id=site["id"], client_id=client_db["id"], data=data)
    # then the column is dumped with none value
    for client_site_id, values in data.items():
        for k, v in values.items():
            assert added["data"][client_site_id][k] == v
        assert added["data"][client_site_id][INDEX_ROOM_NUMBER] is None


def test_update_qa_missing_column(client_db, site, make_qa_data):
    (qa_entry,) = make_qa_data(site)
    # when we upload a qa sheet with a missing column
    data = qa_data(missing_column=INDEX_ROOM_NUMBER)
    updated = QADBHandler.update(
        item_pks={"id": qa_entry["id"]},
        new_values={"data": data},
    )
    # then the column is dumped with none value
    for client_site_id, values in data.items():
        for k, v in values.items():
            assert updated["data"][client_site_id][k] == v
        assert updated["data"][client_site_id][INDEX_ROOM_NUMBER] is None


def test_invalid_update_qa_extra_column(client_db, site, make_qa_data):
    (qa_entry,) = make_qa_data(site)
    with pytest.raises(DBValidationException):
        QADBHandler.update(
            item_pks={"id": qa_entry["id"]},
            new_values={"data": qa_data(extra_column="Dummy Column")},
        )


def test_valid_update_qa(client_db, site, make_qa_data):
    (qa_entry,) = make_qa_data(site)
    data = qa_data()
    updated = QADBHandler.update(
        item_pks={"id": qa_entry["id"]},
        new_values={"data": data},
    )
    assert data == updated["data"]


@pytest.fixture
def plan_georef_values(plan):
    return PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        # Values are random copied from another plan
        new_values={
            "georef_x": 8.439012220887376,
            "georef_y": 47.37264388680668,
            "georef_scale": 6.95890929748154e-06,
            "georef_rot_angle": 0.0,
            "georef_rot_x": 6228.23,
            "georef_rot_y": -3538.25,
        },
    )


@pytest.fixture
def client_site_id():
    return "22540"


@pytest.fixture
def index_info(client_site_id):
    buildings = ("01", "02")
    house_number = ("01", "02")
    units = ("0001", "0002")
    return {
        f"{client_site_id}.{building}.{house}.{unit}": qa_values()
        for building in buildings
        for house in house_number
        for unit in units
    }


@pytest.fixture
def units_db_with_indexed_info(index_info, site, floor, basic_features_finished):
    units = []
    for i, unit_id in enumerate(set(index_info.keys())):
        unit_added = UnitDBHandler.add(
            client_id=unit_id,
            plan_id=floor["plan_id"],
            site_id=site["id"],
            floor_id=floor["id"],
            apartment_no=i,
        )
        units.append(unit_added)
    SlamSimulationHandler.store_results(
        run_id=basic_features_finished["run_id"],
        results={
            u["id"]: [
                {
                    "UnitBasics.number-of-kitchens": 11.0,
                    "UnitBasics.number-of-bathrooms": 11.0,
                    DB_INDEX_ROOM_NUMBER: 11.0,
                    DB_INDEX_NET_AREA: 11.0,
                    DB_INDEX_HNF: 11.0,
                    DB_INDEX_ANF: 11.0,
                }
            ]
            for u in units
        },
    )
    return units


def test_check_sites_units(
    mocker, plan_georef_values, annotations_box_unfinished, make_areas_from_layout
):
    from handlers import qa_handler

    unit_id = 12323
    additional_unit_id = 12323
    missing_unit_id = 12323

    unit_client_id = "2376030.02.03.0040"
    additional_client_unit_id = 312
    missing_client_unit_id = 999

    make_areas_from_layout(
        layout=PlanLayoutHandler(plan_id=plan_georef_values["id"]).get_layout(
            raise_on_inconsistency=False
        ),
        plan_id=plan_georef_values["id"],
    )

    mocker.patch.object(
        qa_handler.SlamSimulationHandler,
        qa_handler.SlamSimulationHandler.get_all_results.__name__,
        return_value=[
            {
                "results": [
                    {
                        "UnitBasics.number-of-kitchens": 1.0,
                        "UnitBasics.number-of-bathrooms": 1.0,
                        "UnitBasics.number-of-rooms": 1.0,
                        "UnitBasics.net-area": 14.1,
                    }
                ],
                "unit_id": unit_id,
            },
            {
                "results": [
                    {
                        "UnitBasics.number-of-kitchens": 1.0,
                        "UnitBasics.number-of-bathrooms": 1.0,
                        "UnitBasics.number-of-rooms": 1.0,
                        "UnitBasics.net-area": 14.1,
                    }
                ],
                "unit_id": additional_unit_id,
            },
            {
                "results": [
                    {
                        "UnitBasics.number-of-kitchens": 1.0,
                        "UnitBasics.number-of-bathrooms": 1.0,
                        "UnitBasics.number-of-rooms": 1.0,
                        "UnitBasics.net-area": 14.1,
                    }
                ],
                "unit_id": missing_unit_id,
            },
        ],
    )
    mocker.patch.object(
        qa_handler.UnitDBHandler,
        "find",
        return_value=[
            {"id": unit_id, "client_id": unit_client_id, "unit_usage": "RESIDENTIAL"},
            {
                "id": additional_unit_id,
                "client_id": additional_client_unit_id,
                "unit_usage": "RESIDENTIAL",
            },
            {"id": missing_unit_id, "client_id": None, "unit_usage": "RESIDENTIAL"},
        ],
    )
    mocker.patch.object(QAHandler, "units_with_linking_errors", return_value=[])
    index_info = {
        unit_client_id: {"number_of_rooms": 1.0, "net_area": 14.1},
        missing_client_unit_id: {"number_of_rooms": 1.0, "net_area": 14.1},
    }
    stats = QAHandler(site_id=plan_georef_values["site_id"]).qa_site_and_unit_errors(
        qa_index_info=index_info
    )
    assert set(stats.keys()) == {"errors", "site_warnings", unit_client_id}
    assert (
        stats["site_warnings"][0]
        == f"{QA_VALIDATION_CODES.CLIENT_IDS_MISSING.value}: ['{missing_client_unit_id}']"
    )
    assert (
        stats["site_warnings"][1]
        == f"{QA_VALIDATION_CODES.CLIENT_IDS_UNEXPECTED.value}: ['{additional_client_unit_id}', 'None']"
    )
    assert (
        stats["errors"][0]
        == f"{QA_VALIDATION_CODES.PLAN_WO_FLOORS.value}: {{{plan_georef_values['id']}}}"
    )


def test_annotations_errors_qa_feedback_all_ok(
    site,
    index_info,
    units_db_with_indexed_info,
    annotations_box_finished,
    plan_georef_values,
    basic_features_finished,
    make_areas_from_layout,
):
    make_areas_from_layout(
        layout=PlanLayoutHandler(plan_id=plan_georef_values["id"]).get_layout(
            raise_on_inconsistency=False
        ),
        plan_id=plan_georef_values["id"],
    )
    feedback = QAHandler(site_id=site["id"]).qa_site_and_unit_errors(
        qa_index_info=index_info
    )
    assert len(feedback) == len(units_db_with_indexed_info)
    for value in feedback.values():
        assert value == []


def test_annotations_errors_and_classification_in_qa_feedback(
    site,
    index_info,
    units_db_with_indexed_info,
    plan_georef_values,
    basic_features_finished,
    areas_accessible_areas,
):
    AreaDBHandler.bulk_update(
        area_type={
            db_area["id"]: AreaType.SHAFT.name
            for db_area in AreaDBHandler.find(
                plan_id=plan_georef_values["id"], output_columns=["id"]
            )
        }
    )
    feedback = QAHandler(site_id=site["id"]).qa_site_and_unit_errors(
        qa_index_info=index_info
    )

    assert (
        len(feedback) == len(units_db_with_indexed_info) + 2
    )  # + site warnings & errors
    for key, value in feedback.items():
        if key == "errors":
            assert QA_VALIDATION_CODES.ANNOTATIONS_ERROR.value in value[0]
            assert QA_VALIDATION_CODES.CLASSIFICATION_ERROR.value in value[-1]
        elif key == "site_warnings":
            assert len(value) == 13
        else:
            assert value == []


def test_room_errors_in_qa_feedback(
    site,
    index_info,
    units_db_with_indexed_info,
    plan_georef_values,
    basic_features_finished,
    areas_accessible_areas,
    mocker,
):
    mocker.patch.object(
        PlanClassificationRoomWindowValidator,
        "area_types_requiring_window",
        return_value=[AreaType.ROOM, AreaType.KITCHEN_DINING],
    )
    mocker.patch.object(
        PlanClassificationRoomWindowValidator, "space_has_window", return_value=False
    )
    mocker.patch.object(QAHandler, "annotation_errors", return_value={})

    feedback = QAHandler(site_id=site["id"]).qa_site_and_unit_errors(
        qa_index_info=index_info
    )

    assert (
        len(feedback["site_warnings"]) == 8
    )  # corresponds to the number of spaces in the layout
    for warning in feedback["site_warnings"]:
        assert (
            warning
            == "plan 1: Space with not enough windows that has been classified as ['ROOM', 'KITCHEN_DINING']"
        )


def test_georeference_no_errors_non_overlapping_plans(
    site, make_buildings, make_plans, annotations_box_data
):
    """We have 1 plan on each building, they are not touching each other so everything should be fine."""
    building_1, building_2 = make_buildings(site, site)
    plan_1, plan_2 = make_plans(building_1, building_2)
    for i, plan in enumerate([plan_1, plan_2]):
        ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations_box_data)

        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            # Values are random copied from another plan
            new_values={
                "georef_x": 8.439012220887376 + i,
                "georef_y": 47.37264388680668 - i,
                "georef_scale": 6.95890929748154e-06,
                "georef_rot_angle": 0.0,
                "georef_rot_x": 6228.23,
                "georef_rot_y": -3538.25,
            },
        )

    assert not GeoreferencingValidator(site_id=site["id"]).georeferencing_errors()


def test_georeference_errors_plans_same_building_overlapping(
    site, make_buildings, make_plans, annotations_box_data
):
    """This test represent the following problem, where each box is a plan, the first 2 of the same building
    and the 3 one belonging to another one.

                +-----+
                |     |
            +-----+   |
            |   +-----+
        +-----+   |
        |   +-----+
        |     |
        +-----+
    """
    building_1, building_2 = make_buildings(site, site)
    plan_1, plan_2, plan_3 = make_plans(building_1, building_1, building_2)
    for i, plan in enumerate([plan_1, plan_2, plan_3]):
        ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations_box_data)

        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            # Values are random copied from another plan
            new_values={
                "georef_x": 8.439012220887376 + i,
                "georef_y": 47.37264388680668 + i,
                "georef_scale": 6.95890929748154e-06,
                "georef_rot_angle": 0.0,
                "georef_rot_x": 6228.23,
                "georef_rot_y": -3538.25,
            },
        )
    assert GeoreferencingValidator(site_id=site["id"]).georeferencing_errors() == {
        f'plan {plan_1["id"]}': "Plan does not match in georeferencing with 1 plans of the same building",
        f'plan {plan_2["id"]}': "Plan does not match in georeferencing with 1 plans of the same building",
    }


def test_qa_validation_site(mocker, site, basic_features_finished):
    unit_id_1 = 4554
    unit_id_2 = 342544
    unit_id_3 = 5456
    client_id_1 = "2215391.01.01.0001"
    client_id_2 = "2215391.01.01.0002"
    client_id_3 = "2215391.01.01.0003"
    plan_id = -999
    client_data = {
        client_id_1: dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{INDEX_ROOM_NUMBER: 4.5, INDEX_HNF_AREA: 68.75},
        ),
        client_id_2: dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{INDEX_ROOM_NUMBER: 1.5, INDEX_HNF_AREA: 30.3},
        ),
        client_id_3: dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{INDEX_ROOM_NUMBER: 2.5, INDEX_HNF_AREA: 47.0},
        ),
    }

    breaking_rooms_number = 99.0
    breaking_net_area_number = 150.0
    QADBHandler.add(
        client_site_id=site["client_site_id"],
        client_id=site["client_id"],
        site_id=site["id"],
        data=client_data,
    )

    units_info = [
        {
            "id": unit_id_1,
            "client_id": client_id_1,
            "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
            "plan_id": plan_id,
        },
        {
            "id": unit_id_2,
            "client_id": client_id_2,
            "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
            "plan_id": plan_id,
        },
        {
            "id": unit_id_3,
            "client_id": client_id_3,
            "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
            "plan_id": plan_id,
        },
    ]
    mocker.patch.object(
        UnitDBHandler, UnitDBHandler.find.__name__, return_value=units_info
    )
    mocker.patch.object(ReactPlannerHandler, "violation_position_to_pixels")
    mocker.patch.object(
        UnitLinkingValidator,
        "areas_by_unit_id",
        return_value={
            unit_id_1: [{"area_type": AreaType.LOBBY.name, "coord_x": 0, "coord_y": 0}],
            unit_id_2: [{"area_type": AreaType.LOBBY.name, "coord_x": 0, "coord_y": 0}],
            unit_id_3: [{"area_type": AreaType.LOBBY.name, "coord_x": 0, "coord_y": 0}],
        },
    )

    simulation_results = [
        {
            "unit_id": unit_id_1,
            "results": [
                {
                    "UnitBasics.number-of-kitchens": 1.0,
                    "UnitBasics.number-of-bathrooms": 1.0,
                    "UnitBasics.number-of-rooms": client_data[client_id_1][
                        INDEX_ROOM_NUMBER
                    ],
                    "UnitBasics.net-area": client_data[client_id_1][INDEX_HNF_AREA],
                    "UnitBasics.area-sia416-HNF": client_data[client_id_1][
                        INDEX_HNF_AREA
                    ],
                }
            ],
        },
        {
            "unit_id": unit_id_2,
            "results": [
                {
                    "UnitBasics.number-of-kitchens": 1.0,
                    "UnitBasics.number-of-bathrooms": 1.0,
                    "UnitBasics.number-of-rooms": client_data[client_id_2][
                        INDEX_ROOM_NUMBER
                    ],
                    "UnitBasics.net-area": client_data[client_id_2][INDEX_HNF_AREA],
                    "UnitBasics.area-sia416-HNF": client_data[client_id_2][
                        INDEX_HNF_AREA
                    ],
                }
            ],
        },
        {
            "unit_id": unit_id_3,
            "results": [
                {
                    "UnitBasics.number-of-kitchens": 0.0,
                    "UnitBasics.number-of-bathrooms": 0.0,
                    "UnitBasics.number-of-rooms": breaking_rooms_number,
                    "UnitBasics.net-area": breaking_net_area_number,
                    "UnitBasics.area-sia416-HNF": breaking_net_area_number,
                }
            ],
        },
    ]

    mocker.patch.object(
        SlamSimulationHandler,
        SlamSimulationHandler.get_all_results.__name__,
        return_value=simulation_results,
    )
    validation_data = QAHandler(site_id=site["id"]).qa_validation()
    assert validation_data == {
        "2215391.01.01.0001": [],
        "2215391.01.01.0002": [],
        "2215391.01.01.0003": [
            "Kitchen missing",
            "Bathrooms missing",
            f"Rooms mismatch. Should have {client_data[client_id_3]['number_of_rooms']} "
            f"rooms and it has {breaking_rooms_number} rooms",
            f"HNF mismatch. Should have {client_data[client_id_3]['HNF']} "
            f"m2 and it has {breaking_net_area_number} m2. Scale deviation factor: 0.31. ",
        ],
        "errors": [
            f"Site contains no buildings: [{site['id']}]",
            "Units containing area types not allowed for unit usage type: "
            "['2215391.01.01.0001', '2215391.01.01.0002', '2215391.01.01.0003']",
        ],
    }


@pytest.mark.parametrize("client_qa_data_exists", [False, True])
def test_qa_report_generation(site, qa_report_mock, client_qa_data_exists):
    if client_qa_data_exists:
        QADBHandler.add(
            client_site_id=site["client_site_id"],
            client_id=site["client_id"],
            site_id=site["id"],
            data=qa_report_mock["qa_data"],
        )

    qa_report = QAHandler(site_id=site["id"]).generate_qa_report()

    assert len(qa_report) == 3 if client_qa_data_exists else 2
    assert qa_report_mock["client_unit_ids"]["client_id_1"] in qa_report.index
    assert qa_report_mock["client_unit_ids"]["client_id_2"] in qa_report.index
    if (
        client_qa_data_exists
    ):  # This unit only exists in the client data but not in the db
        assert qa_report_mock["client_unit_ids"]["client_id_3"] in qa_report.index
    assert len(qa_report.keys()) == 11
    # Missing data is shown as NaN
    assert math.isnan(qa_report["net_area_QA"][0])
    assert math.isnan(qa_report["net_area_QA"][1])

    assert (
        qa_report.loc[[qa_report_mock["client_unit_ids"]["client_id_1"]]]["VF"][0]
        == 0.0
    )
    assert (
        qa_report.loc[[qa_report_mock["client_unit_ids"]["client_id_1"]]]["FF"][0]
        == 0.0
    )
    assert (
        qa_report.loc[[qa_report_mock["client_unit_ids"]["client_id_1"]]]["NNF"][0]
        == 0.0
    )
    assert (
        qa_report.loc[[qa_report_mock["client_unit_ids"]["client_id_2"]]]["VF"][0]
        == 10.0
    )
    assert (
        qa_report.loc[[qa_report_mock["client_unit_ids"]["client_id_2"]]]["FF"][0]
        == 5.0
    )
    assert (
        qa_report.loc[[qa_report_mock["client_unit_ids"]["client_id_2"]]]["NNF"][0]
        == 20.0
    )


def test_empty_floor_only_creates_empty_floor_warning(
    site, plan, annotations_box_data, mocker, floor, make_areas_from_layout
):
    mocker.patch.object(QAHandler, "get_qa_data_check_exists", return_value={})
    mocker.patch.object(SlamSimulationHandler, "get_all_results", return_value=[])
    mocker.patch.object(QAHandler, "units_with_linking_errors", return_value=[])
    ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations_box_data)
    make_areas_from_layout(
        layout=PlanLayoutHandler(plan_id=plan["id"]).get_layout(
            raise_on_inconsistency=False
        ),
        plan_id=plan["id"],
    )

    PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        # Values are random copied from another plan
        new_values={
            "georef_x": 8.439012220887376,
            "georef_y": 47.37264388680668,
            "georef_scale": 6.95890929748154e-06,
            "georef_rot_angle": 0.0,
            "georef_rot_x": 6228.23,
            "georef_rot_y": -3538.25,
        },
    )

    validation_data = QAHandler(site_id=site["id"]).qa_validation()

    assert validation_data.keys() == {"site_warnings"}
    assert validation_data["site_warnings"] == [
        "Floor number 1 in building some street 20-22 doesn't contain any units"
    ]

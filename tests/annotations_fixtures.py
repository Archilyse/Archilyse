import json
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture(scope="session")
def annotations_path(fixtures_path) -> Path:
    return fixtures_path.joinpath("annotations/")


@pytest.fixture
def react_planner_floorplan_annotation_w_errors(annotations_path) -> Dict:
    with annotations_path.joinpath("floorplan.json").open() as f:
        return json.load(f)


@pytest.fixture
def react_planner_plan_12288(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_12288.json").open() as f:
        return json.load(f)


@pytest.fixture
def react_planner_background_image_one_unit(annotations_path) -> Dict:
    with annotations_path.joinpath("background_image_one_unit.json").open() as f:
        return json.load(f)


@pytest.fixture
def react_planner_background_image_full_plan(annotations_path) -> Dict:
    with annotations_path.joinpath("background_image_full_plan.json").open() as f:
        return json.load(f)


@pytest.fixture
def react_data_valid_square_space_with_entrance_door(annotations_path) -> Dict:
    with annotations_path.joinpath("react_square_with_entrance_door.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_2016(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_2016.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_box_data(annotations_path) -> Dict:
    with annotations_path.joinpath("annotations_box_data.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_3213_heavy(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_3213.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_3_rooms_2_w_stairs(annotations_path) -> Dict:
    with annotations_path.joinpath("3_rooms_2_w_stairs.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_accessible_areas(annotations_path) -> Dict:
    with annotations_path.joinpath("accessible_areas.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_247(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_247.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_868(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_868.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_5690(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_5690.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_4976(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_4976.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_5825(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_5825.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_1241(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_1241.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_3881(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_3881.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_4836(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_4836.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotations_plan_2494(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_2494.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotation_plan_5797(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_5797.json").open() as f:
        return json.load(f)


@pytest.fixture
def annotation_plan_1478(annotations_path) -> Dict:
    with annotations_path.joinpath("plan_1478.json").open() as f:
        return json.load(f)

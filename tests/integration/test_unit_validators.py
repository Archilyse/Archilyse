import pytest
from shapely.geometry import box

from brooks.classifications import CLASSIFICATIONS
from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.models.violation import ViolationType
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from handlers import AreaHandler, PlanLayoutHandler, UnitHandler
from handlers.db import AreaDBHandler, PlanDBHandler, SiteDBHandler
from handlers.validators import SpacesConnectedValidator
from handlers.validators.unit_areas.unit_area_validation import UnitAreaValidator


class TestSpacesConnectedValidator:
    @pytest.mark.parametrize(
        "shaft_area_type,should_create_violation",
        [
            (AreaType.ROOM, True),
            (AreaType.SHAFT, False),
            (
                AreaType.OPERATIONS_FACILITIES,
                False,
            ),
            (AreaType.COMMON_KITCHEN, True),
        ],
    )
    def test_violation_not_connected_space(
        self,
        site,
        plan,
        populate_plan_annotations,
        shaft_area_type,
        should_create_violation,
    ):
        """
        Test Scenario:
        Apartment includes a space not connected
        Expectations:
        validation creates an violation unless the not connected space
        is of certain types like 'shafts'
        """

        populate_plan_annotations(fixture_plan_id=863, db_plan_id=plan["id"])

        AreaHandler.recover_and_upsert_areas(
            plan_id=plan["id"],
            plan_layout=PlanLayoutHandler(plan_id=plan["id"]).get_layout(
                validate=False,
                classified=False,
                scaled=False,
                set_area_types_by_features=True,
            ),
        )
        areas = AreaDBHandler.find(plan_id=plan["id"])
        # we know it is the 8 units situated at the left :)
        splitting_areas = sorted(areas, key=lambda x: x["coord_x"])[:8]

        shaft_area = [
            area for area in splitting_areas if area["area_type"] == AreaType.SHAFT.name
        ][0]

        AreaDBHandler.update(
            item_pks={"id": shaft_area["id"]},
            new_values={"area_type": shaft_area_type.name},
        )
        result = SpacesConnectedValidator(
            plan_id=plan["id"],
            new_area_ids=[a["id"] for a in splitting_areas],
            apartment_no=1,
            unit_handler=UnitHandler(),
        ).validate()

        if should_create_violation:
            assert result[0].violation_type == ViolationType.UNIT_SPACES_NOT_CONNECTED

        else:
            assert not result

        # No exception raised

    @pytest.mark.parametrize(
        "classification_scheme, area_types, door_type, indices_of_missing_areas, creates_violation",
        [
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.ROOM,
                    AreaType.ROOM,
                ],
                OpeningType.DOOR,
                [0],
                True,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.OPERATIONS_FACILITIES,
                    AreaType.ROOM,
                ],
                OpeningType.DOOR,
                [0],
                False,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.OPERATIONS_FACILITIES,
                    AreaType.ROOM,
                ],
                OpeningType.DOOR,
                [],
                False,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.ROOM,
                    AreaType.ROOM,
                ],
                OpeningType.DOOR,
                [0],
                True,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.SHAFT,
                    AreaType.ROOM,
                ],
                OpeningType.DOOR,
                [0],
                False,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.SHAFT,
                    AreaType.ROOM,
                ],
                OpeningType.DOOR,
                [],
                False,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.ROOM,
                    AreaType.BALCONY,
                ],
                OpeningType.DOOR,
                [0],
                True,
            ),
            (
                CLASSIFICATIONS.UNIFIED,
                [
                    AreaType.ROOM,
                    AreaType.BALCONY,
                ],
                OpeningType.ENTRANCE_DOOR,
                [],
                False,
            ),
        ],
    )
    def test_violation_spaces_connected_missing(
        self,
        plan,
        mocker,
        classification_scheme,
        area_types,
        door_type: OpeningType,
        indices_of_missing_areas,
        creates_violation,
    ):
        SiteDBHandler.update(
            item_pks={"id": plan["site_id"]},
            new_values={"classification_scheme": classification_scheme.name},
        )
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={"georef_scale": 1.0, "georef_rot_x": 0.0, "georef_rot_y": 0.0},
        )
        area_1 = SimArea(footprint=box(0, 0, 1, 1), area_type=area_types[0])
        space_1 = SimSpace(footprint=area_1.footprint)
        space_1.areas = {area_1}
        wall = SimSeparator(
            footprint=box(1, 0, 1.2, 1), separator_type=SeparatorType.WALL
        )
        door = SimOpening(
            footprint=box(1, 0.2, 1.2, 0.8),
            height=(1, 2.6),
            separator=wall,
            opening_type=door_type,
            separator_reference_line=get_center_line_from_rectangle(wall.footprint)[0],
        )
        wall.openings = {door}
        area_2 = SimArea(footprint=box(1.2, 0, 2.2, 1), area_type=area_types[1])
        space_2 = SimSpace(footprint=area_2.footprint)
        space_2.areas = {area_2}
        plan_layout = SimLayout(separators={wall}, spaces={space_1, space_2})

        new_areas = [
            area
            for i, area in enumerate([area_1, area_2])
            if i not in indices_of_missing_areas
        ]
        mocker.patch.object(
            UnitAreaValidator,
            "new_areas",
            mocker.PropertyMock(
                return_value=[
                    {
                        "coord_x": area.footprint.centroid.x,
                        "coord_y": area.footprint.centroid.y,
                        "area_type": area.type.name,
                        "id": str(i),
                    }
                    for i, area in enumerate(new_areas)
                ]
            ),
        )

        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=plan_layout)
        unit_layout_mock = mocker.patch.object(
            UnitHandler, "build_unit_from_area_ids", return_value=plan_layout
        )

        connectivity_graph_spy = mocker.spy(
            SpacesConnectedValidator, "_traverse_connected_spaces_dfs"
        )
        result = SpacesConnectedValidator(
            plan_id=plan["id"],
            new_area_ids=[],
            apartment_no=1,
            unit_handler=UnitHandler(),
        ).validate()

        if creates_violation:
            assert len(result) == 1
            assert (
                result[0].text
                == "There are spaces connected to the unit that are not assigned to it"
            )
        else:
            assert not result
        assert connectivity_graph_spy.call_args[1]["next_space_id"] == space_1.id
        unit_layout_mock.assert_called_once_with(area_ids=set(), plan_id=plan["id"])

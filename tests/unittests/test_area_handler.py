import uuid
from collections import Counter
from copy import deepcopy
from itertools import chain

import pytest
from shapely.affinity import scale
from shapely.geometry import LineString, Polygon, box
from shapely.wkt import loads

from brooks.models import SimArea, SimFeature, SimLayout, SimSpace
from brooks.models.violation import SpatialEntityViolation, ViolationType
from brooks.types import AreaType
from common_utils.utils import pairwise
from dufresne.linestring_add_width import add_width_to_linestring_improved
from handlers import AreaHandler, PlanLayoutHandler, ReactPlannerHandler
from handlers.db import AreaDBHandler
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    ReactPlannerArea,
    ReactPlannerAreaProperties,
    ReactPlannerData,
    ReactPlannerName,
    ReactPlannerVertex,
)
from handlers.validators import (
    PlanClassificationBalconyHasRailingValidator,
    PlanClassificationDoorNumberValidator,
    PlanClassificationFeatureConsistencyValidator,
    PlanClassificationRoomWindowValidator,
    PlanClassificationShaftValidator,
)


class TestAreaHandler:
    @staticmethod
    @pytest.mark.parametrize(
        "pol, not_representative_point",
        [
            (
                "POLYGON ((7508.6596429800138139 -3668.0000000000000000, "
                "7509.5118920778586471 -3896.0000000000000000, 7276.9540964265506773 "
                "-3896.0000000000000000, 7274.5674857962867463 -3243.8906976744187887, "
                "7276.1196546822611708 -3668.0000000000000000, 7508.6596429800138139 "
                "-3668.0000000000000000))",
                True,
            ),
            (
                "POLYGON ((3045.2102274067219696 -1728.0000000000000000, 3044.0779110812059116 "
                "-938.0000000000000000, 3329.0000000000000000 -938.0000000000000000, "
                "3329.0000000000000000 -1728.0000000000000000, 3045.2102274067219696 "
                "-1728.0000000000000000))",
                False,
            ),
        ],
    )
    def test_get_representative_point(pol, not_representative_point):
        """Tests that not always the representative point might be used,
        but it is guaranteed to be inside the polygon.
        Pending to test a case where get_representative_point raises InvalidShapeException
        """
        poly = loads(pol)
        point = AreaHandler.get_representative_point(poly)
        if not_representative_point:
            assert point != poly.representative_point()
        else:
            assert point == poly.representative_point()

        assert point.within(poly)

    @staticmethod
    @pytest.fixture
    def react_data_with_preclassified_area(
        react_data_valid_square_space_with_entrance_door,
    ):
        react_data_valid_square_space_with_entrance_door = deepcopy(
            react_data_valid_square_space_with_entrance_door
        )
        areas = react_data_valid_square_space_with_entrance_door["layers"]["layer-1"][
            "areas"
        ].values()
        for area in areas:
            area["properties"]["areaType"] = AreaType.ROOM.name
        return react_data_valid_square_space_with_entrance_door

    @staticmethod
    @pytest.mark.parametrize("scaled", [False, True])
    def test_preclassify_layout_from_experimental_annotations(
        react_data_with_preclassified_area, scaled
    ):
        plan_layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**react_data_with_preclassified_area),
            scaled=scaled,
            set_area_types_by_features=False,
            set_area_types_from_react_areas=True,
        )
        assert all([a.type == AreaType.ROOM for a in plan_layout.areas])

    @staticmethod
    @pytest.fixture
    def react_data_with_non_matching_area_coords(react_data_with_preclassified_area):
        area = next(
            iter(
                react_data_with_preclassified_area["layers"]["layer-1"][
                    "areas"
                ].values()
            )
        )
        area["coords"] = [box(12, 34, 56, 78).exterior.coords[:]]
        return react_data_with_preclassified_area

    @staticmethod
    def test_preclassify_layout_from_experimental_annotations_undefined_on_area_mismatch(
        react_data_with_non_matching_area_coords,
    ):
        plan_layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(
                **react_data_with_non_matching_area_coords
            ),
            set_area_types_by_features=False,
            set_area_types_from_react_areas=True,
        )

        assert all([a.type == AreaType.NOT_DEFINED for a in plan_layout.areas])

    @staticmethod
    @pytest.fixture
    def react_data_with_preclassified_area_with_holes(
        react_data_with_preclassified_area,
    ):
        react_data_with_preclassified_area = ReactPlannerData(
            **react_data_with_preclassified_area
        )
        outer_area = next(
            iter(react_data_with_preclassified_area.layers["layer-1"].areas.values())
        )
        exterior = outer_area.coords[0]
        interior = scale(
            Polygon(shell=exterior), xfact=0.5, yfact=0.5, origin="centroid"
        ).exterior
        area_coords_with_holes = [exterior, interior.coords[:]]

        outer_area.coords = area_coords_with_holes
        outer_area.properties.areaType = AreaType.ROOM.name

        # create a wall around the inner area so that the plan layout has one, too
        for coords in pairwise(interior.coords):
            line = LineString(coords)
            line_polygon = add_width_to_linestring_improved(line=line, width=5)
            vertices = [ReactPlannerVertex(x=x, y=y) for (x, y) in line.coords[:]]
            aux_vertices = [
                ReactPlannerVertex(x=x, y=y)
                for (x, y) in line_polygon.exterior.coords[:-1]
            ]
            react_data_with_preclassified_area.layers["layer-1"].vertices.update(
                {v.id: v for v in chain(vertices, aux_vertices)}
            )
            wall = ReactPlannerElementFactory.get_line_from_vertices(
                vertices=vertices,
                auxiliary_vertices=aux_vertices,
                width=5,
                name=ReactPlannerName.WALL,
                line_polygon=line_polygon,
            )
            react_data_with_preclassified_area.layers["layer-1"].lines[wall.id] = wall
        inner_area_id = str(uuid.uuid4())
        inner_area = ReactPlannerArea(
            id=inner_area_id,
            coords=[interior.coords[:]],
            properties=ReactPlannerAreaProperties(areaType=AreaType.CORRIDOR.name),
        )
        react_data_with_preclassified_area.layers["layer-1"].areas.update(
            {inner_area_id: inner_area}
        )
        return react_data_with_preclassified_area

    @staticmethod
    def test_preclassify_layout_from_experimental_annotations_with_holes(
        react_data_with_preclassified_area_with_holes,
    ):
        plan_layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=react_data_with_preclassified_area_with_holes,
            scaled=False,
            set_area_types_by_features=False,
            set_area_types_from_react_areas=True,
        )
        assert Counter([a.type for a in plan_layout.areas]) == Counter(
            {AreaType.ROOM: 1, AreaType.CORRIDOR: 1}
        )

    @staticmethod
    def test_recover_and_upsert_areas_should_get_scaled_layout(mocker):
        from handlers import PlanHandler

        plan_id = 123
        mocker.patch.object(AreaHandler, "get_existing_db_areas", return_value=[])
        mocker.patch.object(
            AreaHandler, "_get_new_areas_with_recovered_info", return_value=[[], []]
        )
        mocker.patch("handlers.area_handler.AreaDBHandler")
        plan_handler_mock = mocker.patch.object(
            PlanHandler, "__init__", return_value=None
        )

        get_layout_mock = mocker.patch.object(PlanLayoutHandler, "get_layout")

        AreaHandler.recover_and_upsert_areas(plan_id=plan_id)
        plan_handler_mock.assert_called_once_with(
            plan_id=plan_id, plan_info={}, site_info={}
        )
        get_layout_mock.assert_called_once_with(
            set_area_types_by_features=False,
            scaled=True,
            set_area_types_from_react_areas=False,
        )

    @staticmethod
    def test_get_existing_db_areas(mocker):
        plan_id = 123
        mocker.patch.object(
            AreaDBHandler, "find", return_value=[{"coord_x": 1, "coord_y": 1}]
        )
        scaled_areas = AreaHandler.get_existing_db_areas(
            plan_id=plan_id,
            plan_layout=SimLayout(scale_factor=123),
        )
        assert scaled_areas == [{"coord_x": 123, "coord_y": 123}]


class TestPutNewClassifications:
    @staticmethod
    def test_put_new_classifications_only_updates_areas_with_non_blocking_errors(
        mocker,
    ):
        mocker.patch.object(
            AreaHandler,
            "validate_plan_classifications",
            return_value=[
                SpatialEntityViolation(
                    entity=SimArea(footprint=Polygon(), db_area_id=i),
                    violation_type=ViolationType.BALCONY_WITHOUT_RAILING,
                    is_blocking=is_blocking,
                )
                for i, is_blocking in enumerate([True, False, False])
            ],
        )
        mocked_db_update = mocker.patch.object(AreaDBHandler, "bulk_update")
        AreaHandler.put_new_classifications(
            plan_id=999,
            areas_type_from_user={
                0: AreaType.ROOM.value,
                1: AreaType.BALCONY.value,
                2: AreaType.CORRIDOR.value,
            },
        )

        mocked_db_update.assert_called_once_with(
            area_type={
                1: AreaType.BALCONY.value,
                2: AreaType.CORRIDOR.value,
            }
        )

    @staticmethod
    def test_put_new_classifications_areas_of_space_not_updated(
        mocker,
    ):
        mocked_validate = mocker.patch.object(
            AreaHandler,
            "validate_plan_classifications",
            return_value=[
                SpatialEntityViolation(
                    entity=SimSpace(
                        footprint=Polygon(),
                        areas={SimArea(db_area_id=i, footprint=Polygon())},
                    ),
                    violation_type=ViolationType.BALCONY_WITHOUT_RAILING,
                    is_blocking=is_blocking,
                )
                for i, is_blocking in enumerate([False, True, True])
            ],
        )
        mocked_db_update = mocker.patch.object(AreaDBHandler, "bulk_update")
        user_input = {
            0: AreaType.ROOM.value,
            1: AreaType.BALCONY.value,
            2: AreaType.CORRIDOR.value,
        }

        AreaHandler.put_new_classifications(
            plan_id=999,
            areas_type_from_user=user_input,
        )

        mocked_db_update.assert_called_once_with(
            area_type={
                0: AreaType.ROOM.value,
            }
        )
        mocked_validate.assert_called_once_with(
            plan_id=999,
            area_id_to_area_type=user_input,
            only_blocking=False,
        )


def test_validate_plan_classifications_react_planner_make_only_1_call(mocker):
    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=SimLayout())
    mocked_db_calls = mocker.patch.object(
        ReactPlannerHandler, "get_by_migrated", return_value={"data": {"scale": 1.0}}
    )
    mocked_scale_spy = mocker.spy(ReactPlannerHandler, "plan_scale")
    for validator in (
        PlanClassificationBalconyHasRailingValidator,
        PlanClassificationShaftValidator,
        PlanClassificationDoorNumberValidator,
        PlanClassificationFeatureConsistencyValidator,
        PlanClassificationRoomWindowValidator,
    ):
        mocker.patch.object(
            validator,
            "validate",
            return_value=[
                SpatialEntityViolation(
                    entity=SimFeature(
                        footprint=Polygon([(0, 0), (0, 1), (1, 1), (0, 0)])
                    ),
                    violation_type=ViolationType.SHAFT_HAS_OPENINGS,
                )
            ],
        )

    violations = list(AreaHandler.validate_plan_classifications(plan_id=123))

    assert len(violations) == 5
    assert mocked_db_calls.call_count == 1
    assert mocked_scale_spy.call_count == 5

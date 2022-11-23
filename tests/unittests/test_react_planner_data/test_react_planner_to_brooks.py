import json
from collections import Counter, defaultdict
from dataclasses import asdict
from itertools import chain
from typing import Set

import pytest
from deepdiff import DeepDiff
from shapely.affinity import scale
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import unary_union

from brooks.layout_validations import SimLayoutValidations
from brooks.models import SimFeature, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.models.violation import ViolationType
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from common_utils.constants import (
    LENGTH_SI_UNITS,
    SI_UNIT_BY_NAME,
    WALL_BUFFER_BY_SI_UNIT,
)
from common_utils.exceptions import CorruptedAnnotationException
from handlers import PlanLayoutHandler
from handlers.db import ReactPlannerProjectsDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    ReactPlannerArea,
    ReactPlannerData,
    ReactPlannerGeomProperty,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerName,
    ReactPlannerType,
    react_planner_name_to_type,
)
from handlers.editor_v2.utils import (
    pixels_to_meters_scale,
    update_planner_element_coordinates,
)
from handlers.editor_v2.wall_postprocessor import ReactPlannerPostprocessor


class TestMapReactPlannerLinesToBrooksSeparators:
    def test_editor_v2_line_mapper_smoke_test(
        self,
        react_data_valid_square_space_with_entrance_door,
    ):
        walls: Set[
            SimSeparator
        ] = ReactPlannerToBrooksMapper._get_separators_from_lines(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            ),
        )
        assert len(walls) == 4
        for wall in walls:
            assert wall.editor_properties is not None
        assert (
            pytest.approx(unary_union([w.footprint for w in walls]).area, abs=1e-3)
            == 19697.945909
        )


class TestMapReactPlannerHolesToBrooksOpenings:
    def test_editor_v2_holes_mapper(
        self,
        react_data_valid_square_space_with_entrance_door,
    ):
        walls: Set[
            SimSeparator
        ] = ReactPlannerToBrooksMapper._get_separators_from_lines(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            ),
        )
        walls_indexed_by_id = {w.id: w for w in walls}
        post_processed_openings: Set[
            SimOpening
        ] = ReactPlannerToBrooksMapper._create_n_assign_opening_to_separators(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            ),
            separators_by_id=walls_indexed_by_id,
            post_processed=True,
        )

        non_processed_openings: Set[
            SimOpening
        ] = ReactPlannerToBrooksMapper._create_n_assign_opening_to_separators(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            ),
            separators_by_id=walls_indexed_by_id,
            post_processed=False,
        )
        assert len(post_processed_openings) == 1 == len(non_processed_openings)
        for opening in chain(post_processed_openings, non_processed_openings):
            assert opening.separator_reference_line is not None
        # 20cmx100cm
        assert sum(o.footprint.area for o in non_processed_openings) == pytest.approx(
            expected=2000.4, abs=10**-3
        )
        # Postprocessed walls are slightly bigger due to precision issues of shapely and this generates bigger openings
        assert sum(o.footprint.area for o in post_processed_openings) == pytest.approx(
            expected=2000.399, abs=10**-3
        )

    @staticmethod
    def test_hole_mapper_opening_discarded(
        mocker, react_data_valid_square_space_with_entrance_door
    ):
        mocker.patch.object(
            ReactPlannerToBrooksMapper,
            "get_element_polygon",
            side_effect=[CorruptedAnnotationException],
        )
        openings = ReactPlannerToBrooksMapper._create_n_assign_opening_to_separators(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            ),
            separators_by_id={},
            post_processed=False,
        )
        assert openings == set()


class TestMapReactItemsToBrooksFeatures:
    def test_editor_v2_items_mapper_smoke_test(
        self,
        react_planner_floorplan_annotation_w_errors,
    ):
        features: Set[SimFeature] = ReactPlannerToBrooksMapper._get_features_from_items(
            planner_elements=ReactPlannerData(
                **react_planner_floorplan_annotation_w_errors
            ),
        )
        assert len(features) == 1
        sink, *_ = features
        assert sink.type == FeatureType.SINK
        assert sink.footprint.area == 125 * 60

    @staticmethod
    def test_all_features_mapped_except_not_defined():
        assert set(
            ReactPlannerToBrooksMapper.REACT_PLANNER_TYPE_TO_FEATURES_MAP.values()
        ) == (set(FeatureType) - {FeatureType.NOT_DEFINED})


class TestMapReactAreasToBrooksAreasAndSpaces:
    def test_editor_v2_space_area_mapper_smoke_test(
        self,
        react_data_valid_square_space_with_entrance_door,
    ):
        separators: Set[
            SimSeparator
        ] = ReactPlannerToBrooksMapper._get_separators_from_lines(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            )
        )
        spaces: Set[SimSpace] = ReactPlannerToBrooksMapper._get_spaces_from_areas(
            separators=separators,
            area_splitters=set(),
            wall_buffer=WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE],
        )
        assert len(spaces) == 1
        assert (
            pytest.approx(sum(s.footprint.area for s in spaces), abs=1e-3) == 51915.7449
        )
        assert all(len(s.areas) == 1 for s in spaces)
        assert all(
            a.footprint.area == s.footprint.area for s in spaces for a in s.areas
        )

    @pytest.mark.parametrize("scaled", [True, False])
    def test_buffer_closes_gaps_for_both_scaled_and_unscaled_walls(self, scaled):

        gap_size_in_meters = 0.001
        wall1 = box(0, 0, 2 - gap_size_in_meters, 0.5)
        wall2 = box(2, 0, 2.5, 2.5)
        wall3 = box(0, 2, 2, 2.5)
        wall4 = box(-0.5, 0, 0, 2.5)
        walls = [wall1, wall2, wall3, wall4]

        planner_elements_fake = ReactPlannerData()
        planner_elements_fake.scale = 0.71706  # real prod case

        if not scaled:
            walls = [
                scale(
                    geom=wall,
                    xfact=1 / pixels_to_meters_scale(scale=planner_elements_fake.scale),
                    yfact=1 / pixels_to_meters_scale(scale=planner_elements_fake.scale),
                    origin=Point(0, 0),
                )
                for wall in walls
            ]

        separators = {
            SimSeparator(footprint=wall, separator_type=SeparatorType.WALL)
            for wall in walls
        }

        spaces = ReactPlannerToBrooksMapper._get_spaces_from_areas(
            separators=separators,
            area_splitters=set(),
            wall_buffer=ReactPlannerToBrooksMapper.get_wall_buffer_size(
                scale=planner_elements_fake.scale, scaled=scaled
            ),
        )

        assert len(spaces) == 1


class TestReactPlannerToBrooks:
    @staticmethod
    def test_map_react_planner_to_brooks_layout(
        react_planner_floorplan_annotation_w_errors,
    ):
        plan_layout: SimLayout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(
                **react_planner_floorplan_annotation_w_errors
            ),
            scaled=False,
        )
        separators_by_type = defaultdict(list)
        for s in plan_layout.separators:
            separators_by_type[s.type].append(s)
        openings_by_type = defaultdict(list)
        for o in plan_layout.openings:
            openings_by_type[o.type].append(o)
        assert len(separators_by_type[SeparatorType.WALL]) == 21
        assert len(separators_by_type[SeparatorType.RAILING]) == 3
        assert len(separators_by_type[SeparatorType.AREA_SPLITTER]) == 0
        assert len(plan_layout.features_by_type[FeatureType.SINK]) == 1
        assert len(openings_by_type[OpeningType.DOOR]) == 2
        assert len(openings_by_type[OpeningType.WINDOW]) == 1
        features_separators_openings = (
            plan_layout.features | plan_layout.separators | plan_layout.openings
        )
        assert len(features_separators_openings) == 28

    @staticmethod
    @pytest.mark.parametrize("scaled, post_processed", [(False, False), (True, True)])
    def test_map_react_planner_to_brooks_layout_custom_heights(
        scaled,
        post_processed,
        react_planner_floorplan_annotation_w_errors,
        custom_element_heights,
    ):
        layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(
                **react_planner_floorplan_annotation_w_errors
            ),
            scaled=scaled,
            post_processed=post_processed,
            default_element_heights=custom_element_heights,
        )

        opening_heights = set(
            [(opening.type, opening.height) for opening in layout.openings]
        )
        separator_heights = set(
            [(separator.type, separator.height) for separator in layout.separators]
        )
        feature_heights = set(
            [(feature.type, feature.height) for feature in layout.features]
        )
        area_heights = set([(area.type, area.height) for area in layout.areas])

        assert opening_heights == {
            (OpeningType.WINDOW, (24, 576)),
            (OpeningType.DOOR, (22, 484)),
        }
        assert separator_heights == {
            (SeparatorType.WALL, (0, 0)),
            (SeparatorType.RAILING, (25, 625)),
        }
        assert feature_heights == {
            (FeatureType.SINK, (5, 25)),
        }
        assert area_heights == {
            (AreaType.NOT_DEFINED, (2, 4)),
            (AreaType.BATHROOM, (2, 4)),
        }
        assert layout.default_element_heights == custom_element_heights

    @staticmethod
    def test_map_react_planner_to_brooks_should_contain_violations(
        react_planner_floorplan_annotation_w_errors,
    ):
        plan_layout: SimLayout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(
                **react_planner_floorplan_annotation_w_errors
            ),
            scaled=False,
        )
        violations = SimLayoutValidations.validate(layout=plan_layout)

        assert {e.type for e in violations} == {
            ViolationType.DOOR_NOT_CONNECTING_AREAS.name,
            ViolationType.SPACE_NOT_ACCESSIBLE.name,
        }

    @staticmethod
    def test_get_polygon():
        line = ReactPlannerLine(
            vertices=["a", "b"],
            auxVertices=["c", "d", "e", "f"],
            properties=ReactPlannerLineProperties(
                height=ReactPlannerGeomProperty(value=10),
                width=ReactPlannerGeomProperty(value=10),
            ),
            coordinates=[[[5.0, 0.0], [5.0, 2.0], [0.0, 2.0], [0.0, 0.0], [5.0, 0.0]]],
        )
        polygon = ReactPlannerToBrooksMapper.get_element_polygon(
            element=line,
        )
        assert polygon.area == 10.0
        assert polygon.bounds == (0.0, 0.0, 5.0, 2.0)

    @staticmethod
    def test_get_polygon_raises_error_if_coordinates_are_not_present():
        line = ReactPlannerLine(
            vertices=["a", "b"],
            auxVertices=["c", "d", "e", "f"],
            properties=ReactPlannerLineProperties(
                height=ReactPlannerGeomProperty(value=10),
                width=ReactPlannerGeomProperty(value=10),
            ),
            coordinates=[],
        )
        with pytest.raises(
            CorruptedAnnotationException,
            match="Line has no coordinates or doesn't have valid coordinates",
        ):
            ReactPlannerToBrooksMapper.get_element_polygon(
                element=line,
            )

    @staticmethod
    def test_planner_get_polygon_from_coordinates():
        line = ReactPlannerLine(
            vertices=["a"],
            auxVertices=["b"],
            coordinates=[
                [
                    [0, 0],
                    [5, 0],
                    [5, 5],
                    [0, 5],
                    [0, 0],
                ]
            ],
            properties=ReactPlannerLineProperties(
                height=ReactPlannerGeomProperty(value=10),
                width=ReactPlannerGeomProperty(value=10),
            ),
        )
        polygon = ReactPlannerToBrooksMapper.get_element_polygon(
            element=line,
        )
        assert polygon.area == 25
        assert polygon.bounds == (0.0, 0.0, 5.0, 5.0)


@pytest.mark.parametrize(
    "set_area_types_by_features, expected_area_types",
    [
        (False, {AreaType.NOT_DEFINED: 12}),
        (
            True,
            {
                AreaType.ELEVATOR: 1,
                AreaType.BATHROOM: 1,
                AreaType.SHAFT: 1,
                AreaType.STAIRCASE: 1,
                AreaType.NOT_DEFINED: 8,
            },
        ),
        (
            True,
            {
                AreaType.ELEVATOR: 1,
                AreaType.BATHROOM: 1,
                AreaType.SHAFT: 1,
                AreaType.STAIRCASE: 1,
                AreaType.NOT_DEFINED: 8,
            },
        ),
    ],
)
def test_react_planner_background_image_full_plan_classified_with_the_features(
    react_planner_background_image_full_plan,
    set_area_types_by_features,
    expected_area_types,
):
    plan_layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**react_planner_background_image_full_plan),
        scaled=False,
        post_processed=False,
        set_area_types_by_features=set_area_types_by_features,
    )
    assert Counter([area.type for area in plan_layout.areas]) == expected_area_types


def test_shaft_postprocessing_new_editor(
    react_planner_background_image_full_plan,
):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**react_planner_background_image_full_plan),
        scaled=False,
        post_processed=False,
    )
    assert {feature for feature in layout.features if feature.type == FeatureType.SHAFT}
    for area in layout.areas:
        shafts = {
            feature for feature in area.features if feature.type == FeatureType.SHAFT
        }
        for shaft in shafts:
            assert shaft.footprint.area == area.footprint.area


@pytest.mark.parametrize("post_processed", [True, False])
@pytest.mark.parametrize(
    "expected_values",
    [
        [0.75, 1.86, 2.93, 3.16, 3.58, 4.16, 7.08, 7.44, 12.26, 15.1, 20.55, 37.96],
    ],
)
def test_react_planner_post_processed_area_sizes(
    react_planner_background_image_full_plan, post_processed, expected_values
):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**react_planner_background_image_full_plan),
        scaled=True,
        post_processed=post_processed,
    )
    assert not DeepDiff(
        sorted([area.footprint.area for area in layout.areas]),
        expected_values,
        significant_digits=2,
    )


def test_unary_union_not_removing_interior(fixtures_path):
    """
    In some cases shapely's unary union is not correctly creating the unary union of walls
    due to some precision problems (removing interior). This test shows that after rounding down
    all coordinates the unary union is correctly created with an interior
    """
    with fixtures_path.joinpath("geometries/walls_failing_unary_union.json").open(
        "r"
    ) as f:
        postprocessed_walls = shape(json.load(f))

    assert unary_union(postprocessed_walls).interiors

    rounded_walls = ReactPlannerPostprocessor._round_geometries_before_unary_union(
        geometries=postprocessed_walls
    )

    assert unary_union(rounded_walls).interiors


def test_generate_layout_planner_non_rectangles(
    mocker,
    react_planner_non_rectangular_walls,
    default_plan_info,
):
    mocker.patch.object(
        ReactPlannerData,
        "get_reference_linestring_of_separator",
        return_value=LineString([(0, 0), (0, 1)]),
    )
    mocker.patch.object(
        ReactPlannerProjectsDBHandler,
        "get_by",
        return_value={"data": asdict(react_planner_non_rectangular_walls)},
    )

    layout = PlanLayoutHandler(plan_info={"id": 1, **default_plan_info}).get_layout(
        scaled=True
    )
    separators_area = 11.25
    assert sum(
        [separator.footprint.area for separator in layout.separators]
    ) == pytest.approx(separators_area, abs=1e-6)
    assert len(layout.separators) == 3
    assert len(layout.openings) == 1
    opening = list(layout.openings)[0]
    assert opening.height == (0.4, 2.6)
    assert opening.footprint.area == pytest.approx(1.0, abs=1e-6)
    spaces_wo_opening = unary_union(
        [separator.footprint for separator in layout.separators]
    ).difference(opening.footprint)
    assert spaces_wo_opening.area == pytest.approx(
        separators_area - opening.footprint.area, abs=1e-6
    )


def test_mapping_complete():
    mappings = (
        ReactPlannerToBrooksMapper.REACT_PLANNER_TYPE_TO_SEPARATOR_MAP,
        ReactPlannerToBrooksMapper.REACT_PLANNER_TYPE_TO_FEATURES_MAP,
        ReactPlannerToBrooksMapper.REACT_PLANNER_TYPE_TO_OPENING_MAP,
    )
    for planner_type in ReactPlannerType:
        assert any([planner_type in mapping for mapping in mappings])


def test_react_planner_name_to_type():
    for name in ReactPlannerName:
        if name not in (ReactPlannerName.VERTEX, ReactPlannerName.AREA):
            assert name in react_planner_name_to_type


def test_scale_react_areas():
    area_geom_with_hole = box(0, 0, 500, 500).difference(box(100, 100, 200, 200))
    data = ReactPlannerData(scale=1.0)
    data.layers["layer-1"].areas = {
        "1": ReactPlannerArea(coords=mapping(area_geom_with_hole)["coordinates"])
    }
    update_planner_element_coordinates(data=data, scaled=True)
    scaled_area = data.layers["layer-1"].areas["1"]
    assert scaled_area.polygon.area == pytest.approx(
        expected=SI_UNIT_BY_NAME["cm"].value ** 2 * area_geom_with_hole.area, abs=0.01
    )

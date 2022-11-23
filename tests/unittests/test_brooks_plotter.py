from copy import deepcopy

import pytest
from PIL import Image
from shapely.geometry import LineString, MultiLineString, Polygon, box
from shapely.ops import unary_union

from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.types import (
    AreaType,
    FeatureType,
    OpeningSubType,
    OpeningType,
    SeparatorType,
)
from brooks.utils import get_default_element_lower_edge, get_default_element_upper_edge
from brooks.visualization.brooks_plotter import BrooksPlotter
from brooks.visualization.floorplans.layouts.assetmanager_layout_text import (
    BaseAssetManagerTextGenerator,
)
from brooks.visualization.floorplans.patches.generators import (
    _are_lines_parallel,
    _get_layout_separator_interior_lines,
    _get_snapping_lines_from_separators,
    _snap_items_to_walls,
)
from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES
from common_utils.utils import pairwise
from tests.utils import _generate_dummy_layout, assert_image_phash


@pytest.mark.parametrize(
    "feature_type",
    [
        FeatureType.BATHTUB,
        FeatureType.SHOWER,
        FeatureType.SINK,
    ],
)
def test_feature_styles(mocker, fixtures_path, feature_type):
    plotter = BrooksPlotter()
    mocker.patch.object(BaseAssetManagerTextGenerator, "generate_metadata_texts")

    dummy_layout = _generate_dummy_layout(feature_type=feature_type)
    io_image = plotter.generate_floor_plot(
        angle_north=0,
        floor_plan_layout=dummy_layout,
        unit_layouts=[dummy_layout],
        unit_ids=["unit_id"],
        metadata={},
        language=SUPPORTED_LANGUAGES.EN,
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )

    with Image.open(io_image) as image_stream:
        assert_image_phash(
            new_image_content=image_stream,
            expected_image_file=fixtures_path.joinpath(
                f"images/brooks_plotter/{feature_type}.png"
            ),
        )


@pytest.mark.parametrize(
    "opening_sub_type",
    [OpeningSubType.DEFAULT, OpeningSubType.SLIDING],
)
def test_opening_sub_types(mocker, fixtures_path, opening_sub_type):
    plotter = BrooksPlotter()
    mocker.patch.object(BaseAssetManagerTextGenerator, "generate_metadata_texts")

    dummy_layout = _generate_dummy_layout(
        opening_types=[OpeningType.DOOR], opening_sub_types=[opening_sub_type]
    )
    io_image = plotter.generate_floor_plot(
        angle_north=0,
        floor_plan_layout=dummy_layout,
        unit_layouts=[dummy_layout],
        unit_ids=["unit_id"],
        metadata={},
        language=SUPPORTED_LANGUAGES.EN,
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )

    assert_image_phash(
        Image.open(io_image),
        fixtures_path.joinpath(f"images/brooks_plotter/{opening_sub_type}.png"),
    )


class TestWindowPatchGenerator:
    @pytest.mark.parametrize(
        "wall_geometry, opening_geometry",
        [([box(0, 0, 0.8, 1), box(0.9, 0, 1, 1)], box(0.5, 0, 0.905, 1))],
    )
    def test_generate_window_patch_regression_di_926_repair_geometry(
        self, mocker, wall_geometry, opening_geometry
    ):
        import brooks.visualization.floorplans.patches.generators as generators_module
        from brooks.visualization.floorplans.patches.generators import (
            generate_window_patch,
        )

        window_patch_spy = mocker.spy(generators_module, "WindowPatch")
        window_centerline_patch_spy = mocker.spy(
            generators_module, "WindowCenterLinePatch"
        )
        buffer_spy = mocker.spy(generators_module, "buffer_unbuffer_geometry")

        wall = SimSeparator(
            footprint=unary_union(wall_geometry), separator_type=SeparatorType.WALL
        )
        opening = SimOpening(
            footprint=opening_geometry,
            separator=wall,
            height=(
                get_default_element_lower_edge(OpeningType.WINDOW),
                get_default_element_upper_edge(OpeningType.WINDOW),
            ),
            separator_reference_line=LineString(),
        )
        list(generate_window_patch(opening=opening, wall=wall))

        buffer_spy.assert_called_once()
        cropped_geometry_coords, *_ = window_patch_spy.mock_calls[0].args
        repaired_geometry = Polygon(cropped_geometry_coords)
        assert repaired_geometry.is_valid
        assert repaired_geometry.area == pytest.approx(0.3, abs=1e-6)

        # both patch classes were instantiated with the same polygon / polygon coordinates
        window_centerline_patch_spy.assert_called_once_with(
            repaired_geometry, facecolor="none", edgecolor="black"
        )

    @pytest.mark.parametrize(
        "wall_geometry, opening_geometry",
        [
            (
                box(0, 0, 1, 1),
                Polygon([(0, 0), (0, 1), (1, 1), (1, 0.5), (1, 0), (0, 0)]),
            )
        ],
    )
    def test_generate_window_patch_regression_di_926_enforce_rectangular_opening(
        self, mocker, wall_geometry, opening_geometry
    ):
        import brooks.visualization.floorplans.patches.generators as generators_module
        from brooks.visualization.floorplans.patches.generators import (
            generate_window_patch,
        )

        window_centerline_patch_spy = mocker.spy(
            generators_module, "WindowCenterLinePatch"
        )

        wall = SimSeparator(
            footprint=unary_union(wall_geometry), separator_type=SeparatorType.WALL
        )
        opening = SimOpening(
            footprint=opening_geometry,
            separator=wall,
            height=(
                get_default_element_lower_edge(OpeningType.WINDOW),
                get_default_element_upper_edge(OpeningType.WINDOW),
            ),
            separator_reference_line=LineString(),
        )
        list(generate_window_patch(opening=opening, wall=wall))

        cropped_geometry_coords, *_ = window_centerline_patch_spy.mock_calls[0].args
        repaired_geometry = Polygon(cropped_geometry_coords)
        assert repaired_geometry.is_valid
        assert repaired_geometry.area == pytest.approx(1.0, abs=1e-6)
        assert len(repaired_geometry.exterior.coords) == 5


class TestFeaturePatchGenerator:
    @classmethod
    def test_kitchen_feature_patch(cls, mocker, fixtures_path):
        plotter = BrooksPlotter()
        mocker.patch.object(BaseAssetManagerTextGenerator, "generate_metadata_texts")

        area = SimArea(footprint=box(0, 0.2, 10, 10), area_type=AreaType.NOT_DEFINED)
        area.area_db_id = 1
        space = SimSpace(footprint=area.footprint)
        space.add_area(area=area)

        area.features.add(
            SimFeature(
                footprint=box(0.5, 0.5, 1.1, 1.1),
                feature_type=FeatureType.KITCHEN,
            )
        )
        area.features.add(
            SimFeature(
                footprint=box(1.1, 0.5, 1.7, 1.1), feature_type=FeatureType.KITCHEN
            ),
        )
        dummy_layout = SimLayout(spaces={space})

        io_image = plotter.generate_floor_plot(
            angle_north=0,
            floor_plan_layout=dummy_layout,
            unit_layouts=[dummy_layout],
            unit_ids=["unit_id"],
            metadata={},
            language=SUPPORTED_LANGUAGES.EN,
            file_format=SUPPORTED_OUTPUT_FILES.PNG,
        )

        with Image.open(io_image) as image_stream:
            assert_image_phash(
                new_image_content=image_stream,
                expected_image_file=fixtures_path.joinpath(
                    "images/brooks_plotter/FeatureType.KITCHEN.png"
                ),
            )

    @pytest.fixture
    def wall_with_interior(self):
        return box(-0.1, -0.1, 1.1, 1.1).difference(box(0, 0, 1, 1))

    @pytest.mark.parametrize(
        "feature_type,feature_footprint,line_footprint,expected_diff",
        [
            (FeatureType.SHAFT, Polygon(), Polygon(), 0.0),  # shafts disallowed
            (
                FeatureType.BATHTUB,
                box(0, 0, 1, 1),
                box(1, 1, 1.1, 3),
                0.0,
            ),  # no interior in wall
            (
                FeatureType.SINK,
                box(0.5, 0.5, 0.996, 0.75),
                pytest.lazy_fixture("wall_with_interior"),
                0.002,
            ),  # feature exterior and wall lines within snapping radius
            (
                FeatureType.SINK,
                box(-0.1, 0, 0.5, 0.5),
                pytest.lazy_fixture("wall_with_interior"),
                0.000,
            ),  # feature intersecting wall
            (
                FeatureType.STAIRS,
                box(0.5, 0.5, 0.95, 0.75),
                pytest.lazy_fixture("wall_with_interior"),
                0.000,
            ),  # feature exterior and wall lines outside of snapping radius
            (
                FeatureType.TOILET,
                box(0.9, 0.9, 0.96, 0.96),
                pytest.lazy_fixture("wall_with_interior"),
                0.006,
            ),  # snaps to upper-right corner
            (
                FeatureType.KITCHEN,
                box(0.5, 0.01, 0.96, 0.96),
                pytest.lazy_fixture("wall_with_interior"),
                0.084,
            ),  # snaps to lower-right corner, although there are 3 wall line candidates
        ],
    )
    def test_snap_items_to_walls(
        self, feature_type, feature_footprint, line_footprint, expected_diff, mocker
    ):
        original_feature_footprint = deepcopy(feature_footprint)

        feature = SimFeature(feature_type=feature_type, footprint=feature_footprint)
        separators = {
            SimSeparator(footprint=line_footprint, separator_type=SeparatorType.WALL)
        }
        separator_lines = _get_layout_separator_interior_lines(separators=separators)
        from brooks.visualization.floorplans.patches import generators

        mocker.patch.object(
            generators,
            "_get_layout_separator_interior_lines",
            return_value=separator_lines,
        )
        assert _snap_items_to_walls(
            feature=feature, separators=separators
        ).symmetric_difference(original_feature_footprint).area == pytest.approx(
            expected_diff, abs=1e-3
        )

    def test_skip_snapping_if_wall_intersection_afterwards(self, mocker):

        feature = SimFeature(feature_type=FeatureType.STAIRS, footprint=box(0, 0, 1, 1))
        potential_wall_to_snap_too = SimSeparator(
            footprint=box(1.01, 0, 1.31, 1.0), separator_type=SeparatorType.WALL
        )
        intersecting_wall_after_snapping = SimSeparator(
            footprint=box(1, 0.8, 1.3, 1.0), separator_type=SeparatorType.WALL
        )

        separator_lines = MultiLineString(
            [
                LineString(pair)
                for wall in [
                    potential_wall_to_snap_too,
                    intersecting_wall_after_snapping,
                ]
                for pair in pairwise(wall.footprint.exterior.coords[:])
            ]
        )
        from brooks.visualization.floorplans.patches import generators

        mocker.patch.object(
            generators,
            "_get_layout_separator_interior_lines",
            return_value=separator_lines,
        )
        snapped_footprint = _snap_items_to_walls(
            feature=feature,
            separators={potential_wall_to_snap_too, intersecting_wall_after_snapping},
        )
        assert snapped_footprint.symmetric_difference(
            feature.footprint
        ).area == pytest.approx(
            expected=0
        )  # no change in footprint

    def test_get_snapping_lines_from_separators(self):
        """
        Ensures that the method returns a horizontal & a vertical snapping line and not
        both horizontal lines even though the vertical line is further away from the feature
        """
        y_shift = 0.01
        x_shift = 0.02
        feature_footprint = box(0, 0 + y_shift, 1 - x_shift, 1 - y_shift)
        horizontal_separator_line1 = LineString([(0, 0), (1, 0)])
        horizontal_separator_line2 = LineString([(0, 1), (1, 1)])
        vertical_separator_line = LineString([(1, 0), (1, 1)])

        snapping_candidates = _get_snapping_lines_from_separators(
            footprint=feature_footprint,
            separator_lines=MultiLineString(
                [
                    horizontal_separator_line1,
                    horizontal_separator_line2,
                    vertical_separator_line,
                ]
            ),
        )
        assert len(snapping_candidates) == 2
        assert vertical_separator_line in [
            snapping_candidate[0] for snapping_candidate in snapping_candidates
        ]

    @pytest.mark.parametrize(
        "line_a, line_b, are_parallel",
        [
            (LineString([(0, 0), (0.5, 0.5)]), LineString([(0.6, 0.6), (1, 1)]), True),
            (LineString([(0, 0), (1, 0)]), LineString([(0, 1), (1, 1.00001)]), True),
            (LineString([(5, 5), (10, 10)]), LineString([(10, 5), (5, 10)]), False),
        ],
    )
    def test_are_lines_parallel(self, line_a, line_b, are_parallel):
        assert _are_lines_parallel(line_a=line_a, line_b=line_b) == are_parallel

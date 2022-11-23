import json
from collections import Counter

import pytest
from deepdiff import DeepDiff
from shapely import wkt
from shapely.geometry import LineString, MultiPolygon, Polygon, box, shape

from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.models.layout import PotentialLayoutWithWindows
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import (
    ensure_geometry_validity,
    get_center_line_from_rectangle,
)
from dufresne.linestring_add_width import (
    LINESTRING_EXTENSION,
    add_width_to_linestring_improved,
)
from dufresne.polygon.utils import as_multipolygon
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData


class TestAreaOpenings:
    @staticmethod
    def test_areas_openings_using_real_model(annotations_plan_5825):
        layout_5825 = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**annotations_plan_5825),
            scaled=True,
        )
        assert Counter(
            [len(value) for value in layout_5825.areas_openings.values()]
        ) == Counter({2: 12, 0: 6, 1: 5, 3: 5, 6: 2, 4: 2, 8: 2, 9: 1, 5: 1})
        assert all(
            o.angle == 0
            for area_openings in layout_5825.areas_openings.values()
            for o in area_openings
        )

    @staticmethod
    def test_areas_openings_l_shape(mocker):
        """
        Reproduces the case where we use the center of the area to scale the area,
        not expanding the area in all directions
                                               ┌──────┐(44.7, 14.38)
                                               │      │
                                               │      │
                                               │      │
                                               │      │
                                               │      │
                                               │      │
                                               │      │
        (40.32, 9.34) ┌──────┐                 │      │
                      │      │                 │      │
                      │      │                 │      │
                      │      └─────────────────┘      │
                      │                               │
                      └───────────────────────────────┘(44.73, 9.33)
        """
        area = SimArea(
            footprint=Polygon(
                [
                    (40.32, 9.34),
                    (40.32, 11.56),
                    (41.44, 11.56),
                    (41.44, 11.23),
                    (41.44, 11.1),
                    (41.45, 11.1),
                    (41.57, 11.1),
                    (42.48, 11.1),
                    (42.61, 11.1),
                    (42.61, 11.1),
                    (42.61, 11.1),
                    (42.61, 11.22),
                    (42.61, 11.56),
                    (42.76, 11.56),
                    (42.82, 11.56),
                    (42.83, 14.39),
                    (44.7, 14.38),
                    (44.73, 9.33),
                    (40.32, 9.34),
                ]
            )
        )
        opening_footprint = box(minx=40.4, maxx=41.19, miny=11.562, maxy=11.68)
        opening = SimOpening(
            footprint=opening_footprint,
            separator=SimSeparator(
                footprint=Polygon(), separator_type=SeparatorType.WALL
            ),
            height=(0, 0),
            separator_reference_line=get_center_line_from_rectangle(opening_footprint)[
                0
            ],
        )
        mocker.patch.object(
            SimLayout,
            "areas",
            mocker.PropertyMock(return_value={area}),
        )
        mocker.patch.object(
            SimLayout, "openings", mocker.PropertyMock(return_value={opening})
        )
        res = SimLayout().areas_openings
        assert area.id in res
        assert len(res[area.id]) == 1


def test_areas_separators(annotations_plan_5825):
    layout_5825 = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_5825), scaled=True
    )
    assert Counter(
        [len(value) for value in layout_5825.areas_separators.values()]
    ) == Counter({4: 14, 5: 9, 9: 4, 6: 3, 8: 2, 11: 1, 10: 1, 3: 1, 7: 1})
    assert all(
        s.angle == 0
        for area_separators in layout_5825.areas_separators.values()
        for s in area_separators
    )


def test_areas_separators_regression_di_633():
    balcony_area = box(0, 0, 2, 1)
    railing_line = LineString([(0, 0), (0, 1), (1, 1), (2, 1), (2, 0)])
    railing_polygon = add_width_to_linestring_improved(
        line=railing_line, width=0.1, extension_type=LINESTRING_EXTENSION.LEFT
    )
    area = SimArea(footprint=balcony_area)
    space = SimSpace(footprint=area.footprint)
    space.add_area(area)
    separator = SimSeparator(
        separator_type=SeparatorType.RAILING, footprint=railing_polygon
    )
    layout = SimLayout(spaces={space}, separators={separator})
    assert layout.areas_separators[area.id] == {separator}


def test_spaces_openings(annotations_plan_5825):
    layout_5825 = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_5825), scaled=True
    )
    assert Counter(
        [len(value) for value in layout_5825.spaces_openings.values()]
    ) == Counter({2: 12, 0: 6, 3: 5, 1: 5, 6: 2, 8: 2, 4: 2, 5: 1, 9: 1})
    assert all(
        o.angle == 0
        for space_openings in layout_5825.spaces_openings.values()
        for o in space_openings
    )


def test_spaces_separators(annotations_plan_5825):
    layout_5825 = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_5825), scaled=True
    )
    assert Counter(
        [len(value) for value in layout_5825.spaces_separators.values()]
    ) == Counter({4: 14, 5: 9, 9: 4, 6: 3, 8: 2, 11: 1, 7: 1, 3: 1, 10: 1})
    assert all(
        s.angle == 0
        for space_separators in layout_5825.spaces_separators.values()
        for s in space_separators
    )


@pytest.mark.parametrize(
    "annotations, expected",
    [
        (pytest.lazy_fixture("annotations_box_data"), 3.294),
        (pytest.lazy_fixture("annotations_plan_247"), 396.12828),
    ],
)
def test_footprint(annotations, expected):
    layout = ReactPlannerToBrooksMapper().get_layout(
        planner_elements=ReactPlannerData(**annotations)
    )
    assert layout.footprint.area == pytest.approx(expected, abs=10**2)
    assert all([s.angle == 0 for s in layout.separators])
    assert all([o.angle == 0 for o in layout.openings])


def test_footprint_ex_balconies():
    interior_footprint = box(0, 0, 1, 1)
    interior_space = SimSpace(footprint=interior_footprint)
    interior_area = SimArea(footprint=interior_footprint, area_type=AreaType.ROOM)
    interior_space.areas.add(interior_area)

    exterior_footprint = box(1, 0, 2, 1)
    exterior_space = SimSpace(footprint=exterior_footprint)
    exterior_area = SimArea(footprint=exterior_footprint, area_type=AreaType.BALCONY)
    exterior_space.areas.add(exterior_area)
    railings = SimSeparator(
        footprint=box(2, 0, 2.1, 1),
        separator_type=SeparatorType.RAILING,
        height=(1, 0),
    )
    layout = SimLayout(spaces={interior_space, exterior_space}, separators={railings})

    assert layout.footprint_ex_balconies.area == pytest.approx(
        layout.footprint.area - exterior_area.footprint.area - railings.footprint.area,
        abs=10**-2,
    )


@pytest.mark.parametrize(
    "area_type",
    [AreaType.BALCONY, AreaType.LOGGIA, AreaType.ARCADE, AreaType.WINTERGARTEN],
)
def test_footprint_outside_and_facade(area_type):
    interior_footprint = box(0, 0, 1, 1)
    interior_space = SimSpace(footprint=interior_footprint)
    interior_area = SimArea(footprint=interior_footprint, area_type=AreaType.ROOM)
    interior_space.areas.add(interior_area)

    exterior_footprint = box(1, 0, 2, 1)
    exterior_space = SimSpace(footprint=exterior_footprint)
    exterior_area = SimArea(footprint=exterior_footprint, area_type=area_type)
    exterior_space.areas.add(exterior_area)
    railings = SimSeparator(
        footprint=box(2, 0, 2.1, 1),
        separator_type=SeparatorType.RAILING,
        height=(1, 0),
    )
    layout = SimLayout(spaces={interior_space, exterior_space}, separators={railings})

    assert layout.footprint_facade.area == pytest.approx(
        layout.footprint.area - exterior_area.footprint.area - railings.footprint.area,
        abs=10**-2,
    )

    assert layout.footprint_outside.area == pytest.approx(
        exterior_area.footprint.area,
        abs=10**-2,
    )


@pytest.mark.parametrize(
    "opening_type, result_expected",
    [
        (OpeningType.DOOR, True),
        (OpeningType.WINDOW, True),
        (OpeningType.ENTRANCE_DOOR, False),
    ],
)
def test_get_windows_and_outdoor_doors(opening_type, result_expected):
    spaces = set()
    for area_type, footprint in [
        (AreaType.ROOM, box(0, 0, 1, 1)),
        (AreaType.BALCONY, box(1, 0, 2, 1)),
    ]:
        space = SimSpace(footprint=footprint)
        area = SimArea(footprint=footprint, area_type=area_type)
        space.areas.add(area)
        spaces.add(space)

    wall = SimSeparator(
        footprint=box(0.9, 0, 1.1, 1), separator_type=SeparatorType.WALL
    )
    opening = SimOpening(
        footprint=box(0.9, 0.3, 1.1, 0.7),
        opening_type=opening_type,
        separator=wall,
        height=(2, 0),
        separator_reference_line=get_center_line_from_rectangle(wall.footprint)[0],
    )
    wall.add_opening(opening)
    layout = SimLayout(spaces=spaces, separators={wall})

    expected_result = []
    if result_expected:
        expected_result.append(opening)

    assert layout.areas
    assert all(
        list(layout.get_windows_and_outdoor_doors(area=area)) == expected_result
        for area in layout.areas
    )


class TestPotentialSimLayout:
    @pytest.mark.parametrize(
        "index,opening_area,separator_area,spaces_area",
        [
            (-1, 11.59, 33.822, 162.894),
            (0, 9.166, 10.769, 117.388),
            (2, 31.718, 274.814, 567.254),
        ],
    )
    def test_get_layout_from_polygon(
        self,
        building_footprints_as_wkts,
        opening_area,
        separator_area,
        index,
        spaces_area,
    ):
        building_footprint = building_footprints_as_wkts[index].geoms[0]
        layout = PotentialLayoutWithWindows(
            floor_number=0,
            footprint=building_footprint,
        )
        all_layout_spaces_area = sum([s.footprint.area for s in layout.spaces])

        assert all(s.footprint.area > 0.0 for s in layout.separators)
        assert pytest.approx(all_layout_spaces_area, abs=1e-2) == spaces_area

        assert all_layout_spaces_area < building_footprint.area

        assert len(layout.spaces) == 1
        assert len([area for space in layout.spaces for area in space.areas]) == 1
        assert (
            pytest.approx(
                sum([opening.footprint.area for opening in layout.openings]), abs=1e-2
            )
            == opening_area
        )
        assert (
            pytest.approx(
                sum([separator.footprint.area for separator in layout.separators]),
                abs=1e-2,
            )
            == separator_area
        )

    def test_get_layout_from_building_footprint_3by3m(self):
        building_footprint = box(0, 0, 3, 3)
        layout = PotentialLayoutWithWindows(
            footprint=building_footprint, floor_number=0
        )
        all_layout_spaces_area = sum([s.footprint.area for s in layout.spaces])
        assert (
            pytest.approx(all_layout_spaces_area, abs=1e-2) == building_footprint.area
        )

        # one of effects of down-buffering a polygon by its squared value greater than building footprint are is that
        # a polygon with area 0.0 is placed in the middle of the building footprint
        assert all(s.footprint.area > 0.0 for s in layout.separators)
        assert len(layout.separators) == 4
        assert len(layout.spaces) == 1
        assert len([area for space in layout.spaces for area in space.areas]) == 1


def test_get_buffered_polygon_of_connected_areas(annotations_plan_1241, caplog):
    layout = ReactPlannerToBrooksMapper().get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_1241)
    )
    polygon_merged_and_buffered = layout.get_polygon_of_spaces_and_doors(
        layout=layout, clipping_buffer=0.3
    )
    assert not [record for record in caplog.records if record.levelname == "ERROR"]
    assert isinstance(polygon_merged_and_buffered, Polygon)


def test_buffer_and_erode_polygon(fixtures_path):
    with fixtures_path.joinpath(
        "geometries/pols_test_space_connector_buffer_and_erode.json"
    ).open() as f:
        pols = json.load(f)
    for pol in pols:
        pol = wkt.loads(pol)
        result = SimLayout.buffer_and_erode_polygon(
            pol=pol, clipping_buffer=0.3, extra_buffer=0.3
        )
        assert isinstance(result, Polygon)


def test_get_polygon_of_spaces_and_doors(annotations_3_rooms_2_w_stairs):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_3_rooms_2_w_stairs),
        scaled=True,
    )

    clipping_geometries = layout.get_polygon_of_spaces_and_doors(layout=layout)
    expected = {
        "area": 78.54511053955221,
        "bounds": (
            -0.02490437367992663,
            10.320309680952798,
            14.452545054976767,
            15.851441069371646,
        ),
    }
    assert not DeepDiff(
        expected,
        {"area": clipping_geometries.area, "bounds": clipping_geometries.bounds},
        significant_digits=3,
    )


def test_get_polygon_of_connected_areas_1_single_area(annotations_box_data):
    """To fix the bug TECH-2092 where the PNG doesn't include the space polygon if there is only 1 space"""
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_box_data)
    )
    polygon = layout.get_polygon_of_spaces_and_doors(layout=layout)
    assert polygon.area == pytest.approx(1.903, abs=0.01)
    assert isinstance(polygon, Polygon)


def test_footprint_with_floating_point_precision_problems_creation(fixtures_path):
    """
    shapely's unary union created a weird shape when creating the union of all spaces
    and separators in the footprint method of the SimLayout. This was due to floating point precision
    problems. The solution is to round all coordinates at least to 12 digits.
    """
    with fixtures_path.joinpath(
        "footprint_unary_floating_point_issues.json"
    ).open() as f:
        data = json.load(f)

    footprint = SimLayout(
        separators={
            SimSeparator(footprint=polygon, separator_type=SeparatorType.WALL)
            for polygon in as_multipolygon(shape(data["walls"])).geoms
        },
        spaces={
            SimSpace(footprint=polygon)
            for polygon in as_multipolygon(shape(data["spaces"])).geoms
        },
    ).footprint

    assert isinstance(footprint, Polygon)
    assert footprint.area == pytest.approx(expected=141.82, abs=0.01)


def test_footprint_with_floating_point_precision_problems_creation_di_956(
    mocker, fixtures_path
):
    with fixtures_path.joinpath(
        "geometries/di_956_space_separator_footprints.json"
    ).open("r") as fh:
        data = json.load(fh)
        space_footprints = [wkt.loads(space_wkt) for space_wkt in data["spaces"]]
        separator_footprints = [
            wkt.loads(separator_wkt) for separator_wkt in data["separators"]
        ]

    result_footprint = SimLayout(
        separators={
            mocker.MagicMock(footprint=footprint) for footprint in separator_footprints
        },
        spaces={
            mocker.MagicMock(footprint=footprint) for footprint in space_footprints
        },
    ).footprint

    geometry = ensure_geometry_validity(
        MultiPolygon(space_footprints + separator_footprints)
    )
    symmetric_difference = geometry.symmetric_difference(result_footprint)
    assert symmetric_difference.area < 10**-6


def test_set_area_types_automatically_by_features(
    mock_working_dir, react_planner_background_image_full_plan
):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**react_planner_background_image_full_plan),
        scaled=True,
    )

    area_type_counter = Counter(
        [area.type.name for space in layout.spaces for area in space.areas]
    )
    assert area_type_counter == {
        AreaType.SHAFT.value: 1,
        AreaType.BATHROOM.value: 1,
        AreaType.ELEVATOR.value: 1,
        AreaType.STAIRCASE.value: 1,
        AreaType.NOT_DEFINED.value: 8,
    }


def test_layout__footprint_excluding_areas_is_polygon(mocker):
    """
    The following separators and areas were creating a multipolygon as a footprint due to the rounding of the
    decimal precision for the unary union
    Old footprint: https://user-images.githubusercontent.com/1510869/137864236-c119664b-0b5a-44ea-a150-f52a374cde87.png
    fixed footprint: https://user-images.githubusercontent.com/1510869/137864244-56888db3-484c-40f0-8806-f2342e70bd53.png

    """
    area = Polygon(
        (
            (2.4304786695865914, -3.4011390179512091),
            (5.3539495866280049, -4.1975100898998789),
            (4.7458651848137379, -6.4297551079071127),
            (4.4328107372857630, -6.3444761511636898),
            (4.1424190172692761, -6.2653707330464385),
            (4.1324444758938625, -6.3019867363036610),
            (1.8114742334000766, -5.6633340607513674),
            (2.4304786695865914, -3.4011390179512091),
        )
    )
    separators_polygons = [
        Polygon(
            (
                (4.1873748293146491, -6.4218556351261213),
                (1.6872990514384583, -5.7339191611972637),
                (1.7138296015327796, -5.6375027211615816),
                (4.2139053794089705, -6.3254391950904392),
                (4.1873748293146491, -6.4218556351261213),
            )
        ),
        Polygon(
            (
                (7.6536141324322671, 2.7187442248687148),
                (5.1325038530630991, -6.5361155335558578),
                (4.7465671945828944, -6.4309827813995071),
                (7.2676774738356471, 2.8238769770250656),
                (7.6536141324322671, 2.7187442248687148),
            )
        ),
        Polygon(
            (
                (
                    (5.0273711009649560, -6.9220521920942701),
                    (4.3274407689459622, -6.7313846292672679),
                    (4.4325735210441053, -6.3454479707288556),
                    (5.1325038530630991, -6.5361155335558578),
                    (5.0273711009649560, -6.9220521920942701),
                )
            )
        ),
        Polygon(
            (
                (
                    (4.4325735210441053, -6.3454479707288556),
                    (3.4842070024460554, -9.8268502707942389),
                    (3.1947545084403828, -9.7480007066624239),
                    (4.1431210270384327, -6.2665984065970406),
                    (4.4325735210441053, -6.3454479707288556),
                )
            )
        ),
    ]
    mocker.patch.object(
        SimLayout,
        "areas",
        mocker.PropertyMock(return_value={SimArea(footprint=area)}),
    )
    separators = {
        SimSeparator(footprint=separator, separator_type=SeparatorType.WALL)
        for separator in separators_polygons
    }
    footprint = SimLayout(separators=separators)._footprint_excluding_areas(
        areas_to_exclude=set()
    )
    assert isinstance(footprint, Polygon)
    assert footprint.area == pytest.approx(12.596394, abs=10.0**-6)


def test_empty_footprint_returned_as_empty_polygon(mocker):
    mocker.patch.object(
        SimLayout,
        "areas_separators",
        mocker.PropertyMock(return_value=dict()),
    )
    mocker.patch.object(
        SimLayout,
        "areas",
        mocker.PropertyMock(return_value=set()),
    )
    footprint = SimLayout()._footprint_excluding_areas(areas_to_exclude=set())

    assert isinstance(footprint, Polygon)
    assert footprint.is_empty
    assert footprint.is_valid


def test_get_spaces_union_returns_polygon():
    """
    Coming from a Real Prod case scenario (plan_id 13015):
    when generating the area patch for the unit in a dxf we call the get spaces union and clip the
    spaces geometries to the footprint of the layout. The footprint was though a multipolygon (root problem) due to a
    tiny gap. this gap is resolved by buffering unbuffering the clip to geometry before applying the clipping
    """
    small_gap = 0.05
    spaces = {SimSpace(footprint=box(0, 0, 2, 2)), SimSpace(footprint=box(2, 0, 4, 2))}
    geometry_to_clip_to = MultiPolygon([box(0, 0, 2, 2), box(2 + small_gap, 0, 4, 2)])
    layout = SimLayout()
    union = layout.get_spaces_union(
        spaces=spaces, public_space=False, clip_to=geometry_to_clip_to
    )
    assert isinstance(union, Polygon)


def test_footprints_buffered_n_rounded_for_union():
    invalid_geometry = Polygon(
        [
            (0, 0),
            (0, 3),
            (3, 3),
            (3, 0),
            (2, 0),
            (2, 2),
            (1, 2),
            (1, 1),
            (2, 1),
            (2, 0),
            (0, 0),
        ]
    )
    footprints = SimLayout._footprints_buffered_n_rounded_for_union(
        sim_elements=[
            SimSeparator(footprint=invalid_geometry, separator_type=SeparatorType.WALL)
        ]
    )
    assert all(f.is_valid for f in footprints)

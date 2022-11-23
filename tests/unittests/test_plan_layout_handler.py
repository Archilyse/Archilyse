import itertools
from collections import defaultdict
from unittest.mock import PropertyMock

import pytest
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.wkt import loads

from brooks.models import SimLayout, SimSpace
from brooks.types import AreaType
from common_utils.constants import REGION
from common_utils.exceptions import AreaMismatchException
from handlers import PlanLayoutHandler, ReactPlannerHandler
from handlers.db import PlanDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData


def test_prepare_layout_footprints(
    mocker, mock_working_dir, site_coordinates, annotations_plan_4836
):
    plan_info = {
        "id": 1258,
        "georef_rot_y": -1556.60648709976,
        "georef_y": site_coordinates["lat"],
        "georef_rot_x": 3672.62588831045,
        "georef_rot_angle": -113.0,
        "georef_scale": 1.07726400686458,
        "georef_x": site_coordinates["lon"],
        "site_id": 1,
    }
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_4836)
    )

    mocked_plan_handler = mocker.patch.object(
        PlanLayoutHandler,
        "get_layout",
        return_value=layout,
    )

    georeferenced_layout_footprint = PlanLayoutHandler(
        plan_id=plan_info["id"],
        plan_info=plan_info,
        site_info={"georef_region": REGION.CH.name},
    ).get_georeferenced_footprint()

    centroid = georeferenced_layout_footprint.centroid

    assert mocked_plan_handler.call_count == 1
    assert (centroid.x, centroid.y) == pytest.approx(
        (2738942.1024334123, 1198848.1613943132), abs=10**-5
    )


def test_get_georeferenced_footprint(mocker, plan_info):
    footprint = Polygon(((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))
    assert footprint.centroid == Point(0.5, 0.5)

    layout_stub = SimLayout(spaces={SimSpace(footprint=footprint)})
    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout_stub)

    georef_info = {
        "georef_rot_angle": 0,
        "georef_rot_x": 1,
        "georef_rot_y": 0,
        "georef_x": -19.917977050315827,
        "georef_y": 32.12450654922877,
    }
    # check translation and rotation
    new_fp = PlanLayoutHandler(
        plan_id=plan_info["id"],
        plan_info=georef_info,
        site_info={"georef_region": REGION.CH.name},
    ).get_georeferenced_footprint()
    assert (new_fp.centroid.x, new_fp.centroid.y) == pytest.approx(
        (1.9978, 2.000), abs=0.01
    )
    # check scale
    assert pytest.approx(new_fp.area) == 1.0040039


def test_apply_georef_to_footprint_valid_pol(mocker, plan_info):
    from tests.fixtures.geometries.footprints_as_wkt import site_741_plan_footprint

    footprint = loads(site_741_plan_footprint)
    layout_stub = SimLayout(spaces={SimSpace(footprint=footprint)})
    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout_stub)

    georef_info = {
        "georef_rot_angle": 16.1536900102477,
        "georef_rot_x": 6436.70048094716,
        "georef_x": 6.11616466506019,
        "georef_rot_y": -3491.36747194494,
        "georef_y": 46.23418109547382,
        "georef_scale": 0.000281409506443054,
    }
    mocker.patch.object(PlanDBHandler, "get_by", return_value=georef_info)

    # check translation and rotation
    new_fp = PlanLayoutHandler(
        plan_id=plan_info["id"], site_info={"georef_region": REGION.CH.name}
    ).get_georeferenced_footprint()
    assert new_fp.is_valid


def test_get_layout_with_area_types_differences_db_and_areas_sent(mocker):
    mocker.patch.object(
        ReactPlannerHandler,
        "pixels_to_meters_scale",
        PropertyMock(return_value=None),
    )
    mocker.patch.object(
        PlanLayoutHandler, "scaled_areas_db", PropertyMock(return_value=[])
    )
    with pytest.raises(AreaMismatchException):
        PlanLayoutHandler(plan_id=-999).get_layout_with_area_types(
            area_id_to_area_type={1: AreaType.ROOM.value}
        )


def test_get_layout_with_area_types_differences_db_and_brooks_model(
    mocker, layout_scaled_classified_wo_db_conn
):
    mocker.patch.object(
        PlanLayoutHandler, "scaled_areas_db", PropertyMock(return_value=[])
    )
    mocker.patch.object(
        PlanLayoutHandler,
        "get_layout",
        return_value=layout_scaled_classified_wo_db_conn(annotation_plan_id=332),
    )
    with pytest.raises(AreaMismatchException):
        PlanLayoutHandler(plan_id=-999).get_layout_with_area_types(
            area_id_to_area_type={1: AreaType.ROOM.value}
        )


def test_cached_layouts_are_unique(mocker, annotations_box_data):
    layout_mapper_spy = mocker.spy(ReactPlannerToBrooksMapper, "get_layout")
    mocker.patch.object(
        ReactPlannerHandler,
        "project",
        return_value={"data": annotations_box_data},
    )

    def mocked_classify(self, layout, areas_db, raise_on_inconsistency):
        return layout

    mocker.patch.object(PlanLayoutHandler, "map_and_classify_layout", mocked_classify)
    mocker.patch.object(PlanLayoutHandler, "scaled_areas_db")
    mocker.patch.object(PlanLayoutHandler, "plan_element_heights")

    layout_handler = PlanLayoutHandler(
        plan_id=1,
        plan_info={
            "georef_scale": 10**-5,
            "georef_rot_x": 50,
            "georef_rot_y": 50,
            "georef_rot_angle": 90,
            "georef_x": 8,
            "georef_y": 47,
        },
        site_info={"georef_region": REGION.CH.name},
    )
    all_possible_args = list(itertools.product([False, True], repeat=7))
    kwargs_by_object_id = defaultdict(list)
    all_layouts_by_scaled_and_georef = defaultdict(list)
    for args in all_possible_args:
        keywords = {
            "scaled",
            "validate",
            "classified",
            "georeferenced",
            "postprocessed",
            "set_area_types_by_features",
            "set_area_types_from_react_areas",
        }
        kwargs = dict(zip(keywords, args))

        layout = layout_handler.get_layout(**kwargs)
        kwargs_by_object_id[id(layout)].append(kwargs)

        # We make 2 calls to make sure the cache is working
        layout = layout_handler.get_layout(**kwargs)
        assert id(layout) in kwargs_by_object_id

        all_layouts_by_scaled_and_georef[
            (kwargs["scaled"], kwargs["georeferenced"])
        ].append(layout)

    # There are 3 arguments in the raw layout that will generate the only necessary calls to the raw layout method
    assert layout_mapper_spy.call_count == 8

    # 128 different possibilities, each one returning different objects
    assert len(kwargs_by_object_id) == len(all_possible_args)
    assert sum([len(values) for values in kwargs_by_object_id.values()]) == len(
        all_possible_args
    )
    # Assert react data was not modified
    assert layout_handler.react_planner_handler.get_data(plan_id=1) == ReactPlannerData(
        **annotations_box_data
    )

    assert (
        len(
            {
                tuple([round(bound, 3) for bound in x.footprint.bounds])
                for layout_list in all_layouts_by_scaled_and_georef.values()
                for x in layout_list
            }
        )
        == 4
    )

    # Make sure the footprints are overlapping when they could change positions (scaled, georeference)
    layouts_scaled_and_georef = all_layouts_by_scaled_and_georef[(True, True)]
    layouts_not_scaled_and_georef = all_layouts_by_scaled_and_georef[(False, True)]
    layouts_scaled_and_not_georef = all_layouts_by_scaled_and_georef[(True, False)]
    layouts_not_scaled_and_not_georef = all_layouts_by_scaled_and_georef[(False, False)]

    unified_scaled_georef = unary_union(
        [x.footprint for x in layouts_scaled_and_georef]
    )
    unified_scaled_not_georef = unary_union(
        [x.footprint for x in layouts_scaled_and_not_georef]
    )
    unified_not_scaled_not_georef = unary_union(
        [x.footprint for x in layouts_not_scaled_and_not_georef]
    )
    unified_not_scaled_georef = unary_union(
        [x.footprint for x in layouts_not_scaled_and_georef]
    )
    # We make sure that scaled footprints are matching in size as well as the not scaled, regardless of georeferencing
    assert (
        pytest.approx(unified_scaled_georef.area, abs=10**-3)
        == unified_scaled_not_georef.area
    )
    assert pytest.approx(unified_scaled_georef.area, abs=10**-3) == 0.3294607449986627

    assert (
        pytest.approx(unified_not_scaled_not_georef.area, abs=10**-3)
        == unified_not_scaled_georef.area
    )
    assert (
        pytest.approx(unified_not_scaled_not_georef.area, abs=10**-3)
        == 32946.07908891275
    )

    # now we make sure that georeferenced and not georeferenced footprints have specific bounds
    assert pytest.approx(unified_scaled_georef.bounds, abs=10**-3) == (
        2642743.4058572254,
        1205542.092387324,
        2642744.008095469,
        1205542.712310924,
    )
    assert pytest.approx(unified_scaled_not_georef.bounds, abs=10**-3) == (
        (1.5701001, 1.41205945649, 2.1900237, 2.0142977)
    )

    assert pytest.approx(unified_not_scaled_not_georef.bounds, abs=10**-3) == (
        (496.50924704581, 446.53240740741, 692.54630217493, 636.97686176385)
    )

    assert pytest.approx(unified_not_scaled_georef.bounds, abs=10**-3) == (
        (835708843.3899599, 381225882.7149079, 835709033.8344142, 381226078.751963)
    )

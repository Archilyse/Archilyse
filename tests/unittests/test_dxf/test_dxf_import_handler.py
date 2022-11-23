from collections import Counter
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from deepdiff import DeepDiff
from PIL import Image
from shapely.affinity import scale
from shapely.geometry import Polygon, box, mapping
from shapely.ops import unary_union

from handlers.dxf.dxf_constants import (
    BUFFER_DOOR_WINDOW_DIFFERENCE_IN_CM,
    SANITARY_FEATURES_LAYERS,
)
from handlers.dxf.dxf_import_handler import DXFImportHandler
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.schema import (
    ReactPlannerArea,
    ReactPlannerData,
    ReactPlannerName,
)
from handlers.shapely_to_react.editor_ready_entity import EditorReadyEntity
from tests.constants import TEST_SKELETONIZE_TIMEOUT_IN_SECS
from tests.utils import assert_image_phash


@pytest.fixture
def dxf_import_with_dxf_sample(dxf_sample):
    with NamedTemporaryFile() as tmp_file:
        dxf_file_path = Path(tmp_file.name)
        with dxf_file_path.open("wb") as f:
            f.write(dxf_sample)

        return DXFImportHandler(dxf_file_path=dxf_file_path, scale_factor=1 / 8 * 1e-4)


def test_dxf_import_handler_image_generation(fixtures_path, dxf_sample):
    with NamedTemporaryFile() as tmp_file:
        dxf_file_path = Path(tmp_file.name)
        with dxf_file_path.open("wb") as f:
            f.write(dxf_sample)

        dxf_import_handler = DXFImportHandler(
            dxf_file_path=dxf_file_path, scale_factor=4e-4
        )

        with BytesIO() as output_stream:
            dxf_import_handler.export_image(output_stream=output_stream)
            output_stream.seek(0)

            with Image.open(output_stream) as new_image_content:
                assert_image_phash(
                    expected_image_file=fixtures_path.joinpath("images/dxf_sample.png"),
                    new_image_content=new_image_content,
                )


@pytest.fixture()
def expected_items_properties():
    return [
        {
            "rotation": 180.0,
            "length": 61,
            "width": 224,
            "x": 6356.729600918925,
            "y": 3589.486206824782,
            "name": "Kitchen",
        },
        {
            "rotation": 90.0,
            "length": 49,
            "width": 224,
            "x": 3518.0005951772705,
            "y": 4613.738030933604,
            "name": "Kitchen",
        },
        {
            "rotation": 180.0,
            "length": 73,
            "width": 172,
            "x": 2110.1954785398248,
            "y": 3603.299962440655,
            "name": "Bathtub",
        },
        {
            "rotation": 90.0,
            "length": 73,
            "width": 172,
            "x": 4897.946086999931,
            "y": 4546.910641835869,
            "name": "Bathtub",
        },
        {
            "rotation": 180.0,
            "length": 87,
            "width": 87,
            "x": 4903.272863590646,
            "y": 4132.545212461347,
            "name": "Shower",
        },
        {
            "rotation": 0.0,
            "length": 44,
            "width": 49,
            "x": 2006.9592583533117,
            "y": 3187.7728848604725,
            "name": "Sink",
        },
        {
            "rotation": 1.116647312166386e-11,
            "length": 44,
            "width": 49,
            "x": 2006.9591735005026,
            "y": 3810.028176402042,
            "name": "Sink",
        },
        {
            "rotation": 90.0,
            "length": 44,
            "width": 49,
            "x": 4691.218748436742,
            "y": 4370.45949533183,
            "name": "Sink",
        },
        {
            "rotation": 179.99999986522636,
            "length": 44,
            "width": 97,
            "x": 5288.9022077816335,
            "y": 4726.592247653662,
            "name": "Sink",
        },
        {
            "rotation": -179.99590342159937,
            "length": 54,
            "width": 40,
            "x": 1744.0883569911393,
            "y": 3495.2754588968965,
            "name": "Toilet",
        },
        {
            "rotation": -0.004291653561767813,
            "length": 54,
            "width": 40,
            "x": 1744.088289941699,
            "y": 3717.6382696930805,
            "name": "Toilet",
        },
        {
            "rotation": 89.99590341741424,
            "length": 54,
            "width": 40,
            "x": 4677.5412417861435,
            "y": 4546.150622895698,
            "name": "Toilet",
        },
        {
            "rotation": -0.004291657944887711,
            "length": 54,
            "width": 40,
            "x": 5196.190350505432,
            "y": 4086.7485793200635,
            "name": "Toilet",
        },
        {
            "rotation": 90.0,
            "length": 115,
            "width": 131,
            "x": 4113.293155610764,
            "y": 3389.7963638464234,
            "name": "Elevator",
        },
        {
            "rotation": -90.0,
            "length": 113,
            "width": 320,
            "x": 4181.31697077157,
            "y": 4366.613644072229,
            "name": "Stairs",
        },
        {
            "rotation": 90.0,
            "length": 113,
            "width": 314,
            "x": 3820.6915167600832,
            "y": 4323.2737987610635,
            "name": "Stairs",
        },
        {
            "rotation": 180.0,
            "length": 23,
            "width": 126,
            "x": 4572.347732117153,
            "y": 4753.386249034837,
            "name": "Shaft",
        },
    ]


def test_dxf_import_handler_annotation_generation(
    dxf_import_with_dxf_sample, dxf_sample, expected_items_properties, mocker
):
    mocker.patch(
        "handlers.dxf.polylines_to_rectangles.SKELETONIZE_TIMEOUT_IN_SECS",
        TEST_SKELETONIZE_TIMEOUT_IN_SECS,
    )
    dxf_import_handler = dxf_import_with_dxf_sample
    react_annotation = dxf_import_handler.export_react_annotation()

    assert react_annotation.width == 11595
    assert react_annotation.height == 8031
    assert react_annotation.scale == 0.125

    # walls etc. regression
    layer = react_annotation.layers["layer-1"]

    assert len(layer.vertices) == 1272, (
        Counter(line.properties.width.value for line in layer.lines.values()),
        len(layer.lines),
    )
    assert len(layer.lines) == 212
    assert len(layer.holes) == 35
    assert len(layer.items) == 17

    assert Counter(line.properties.width.value for line in layer.lines.values()) == {
        13: 37,
        17: 35,
        37: 21,
        12: 19,
        16: 15,
        6: 12,
        7: 14,
        9: 11,
        32: 13,
        19: 7,
        5: 6,
        10: 1,
        15: 4,
        18: 8,
        22: 2,
        11: 1,
        8: 2,
        26: 1,
        20: 1,
        25: 1,
        27: 1,
    }

    windows = [
        hole
        for hole in layer.holes.values()
        if hole.name == ReactPlannerName.WINDOW.value
    ]

    assert Counter(window.properties.width.value for window in windows) == {
        32: 13,
        22: 1,
        27: 1,
    }
    assert Counter(window.properties.length.value for window in windows) == {
        191: 12,
        96: 2,
        101: 1,
    }

    doors = sorted(
        [
            hole
            for hole in layer.holes.values()
            if hole.name == ReactPlannerName.DOOR.value
        ],
        key=lambda hole: Polygon(hole.coordinates[0]).centroid.x,
    )
    assert Counter(door.properties.width.value for door in doors) == {
        17: 4,
        13: 4,
        7: 3,
        9: 3,
        16: 3,
        15: 1,
        18: 1,
        6: 1,
    }
    assert Counter(door.properties.length.value for door in doors) == {
        87: 10,
        72: 4,
        85: 3,
        97: 2,
        84: 1,
    }
    first_door = doors[0]
    assert first_door.door_sweeping_points.angle_point == pytest.approx(
        expected=[2453.8515, 1859.192], abs=0.01
    )
    assert first_door.door_sweeping_points.closed_point == pytest.approx(
        expected=[2213.434, 1859.19], abs=0.01
    )
    assert first_door.door_sweeping_points.opened_point == pytest.approx(
        expected=[2453.8515, 2099.609], abs=0.01
    )

    items_properties = []
    for item in layer.items.values():
        items_properties.append(
            {
                "rotation": item.rotation,
                "length": item.properties.length.value,
                "width": item.properties.width.value,
                "x": item.x,
                "y": item.y,
                "name": item.name,
            }
        )

    assert not DeepDiff(
        expected_items_properties,
        items_properties,
        ignore_order=True,
        significant_digits=2,
        ignore_numeric_type_changes=True,
    )


def test_get_inner_walls_polygon_experimental(mocker, dxf_import_with_dxf_sample):
    mocker.patch(
        "handlers.dxf.polylines_to_rectangles.SKELETONIZE_TIMEOUT_IN_SECS",
        TEST_SKELETONIZE_TIMEOUT_IN_SECS,
    )
    inner_walls = dxf_import_with_dxf_sample.mapper.get_polygons_from_hatches(
        allowed_layers={"0_SCHRAFFUR_INNEN"}, allowed_geometry_types={"HATCH"}
    )
    assert unary_union(inner_walls).area == pytest.approx(110501.72, abs=10**-2)
    assert len(inner_walls) == 95
    assert unary_union(inner_walls).bounds == (
        -814.001952,
        -432.000866,
        1109.001817,
        846.001673,
    )


def test_get_outer_walls_polygon_experimental(mocker, dxf_import_with_dxf_sample):
    mocker.patch(
        "handlers.dxf.polylines_to_rectangles.SKELETONIZE_TIMEOUT_IN_SECS",
        TEST_SKELETONIZE_TIMEOUT_IN_SECS,
    )
    outer_walls = dxf_import_with_dxf_sample.mapper.get_polygons_from_hatches(
        allowed_layers={"0_SCHRAFFUR_AUSSEN"}, allowed_geometry_types={"HATCH"}
    )
    assert pytest.approx(unary_union(outer_walls).area, abs=10**-3) == 133521.002
    assert len(outer_walls) == 62
    assert unary_union(outer_walls).bounds == (
        -835.001952,
        -688.04782,
        1235.002118,
        882.0017730000001,
    )


def test_get_sanitary_elements_without_walls_adjustment(dxf_import_with_dxf_sample):
    # In the example DXF file there are 12 sanitary elements, but there are 2 sinks together, so we can't atm
    # differentiate those
    (
        sanitary_elements,
        _,
    ) = dxf_import_with_dxf_sample.mapper.get_item_polygons_from_layer(
        layer=SANITARY_FEATURES_LAYERS, wall_polygons=[]
    )
    assert len(sanitary_elements) == 11
    # The areas are nicely grouped into 5 groups instead of 11 different areas,
    # which means we are recreating the elements consistently
    assert {round(x.area, 1) for x in sanitary_elements} == {
        12352.1,
        7396.4,
        2100.6,
        2423.4,
        5818.0,
    }
    # But we have 11 different positions

    assert {
        (round(x.centroid.x, 2), round(x.centroid.y, 2)) for x in sanitary_elements
    } == {
        (-769.94, 197.31),
        (267.19, 490.23),
        (-640.5, 156.88),
        (-677.0, 226.88),
        (347.0, 344.0),
        (275.12, 428.12),
        (-769.94, 118.69),
        (450.56, 327.81),
        (485.27, 556.0),
        (-677.0, 6.88),
        (345.12, 490.5),
    }


def test_georef_parameters(dxf_import_with_dxf_sample):
    params = dxf_import_with_dxf_sample.get_georef_parameters()
    assert {"georef_scale": 1.0, "georef_rot_angle": 315.18638094983226} == params


def test_remove_walls_overlap_with_openings():
    wall_1 = box(0, 0, 1, 0.5)
    wall_2 = box(2, 0, 5, 0.5)
    opening = box(0.8, -1, 2.2, 1)
    new_walls = DXFImportHandler._remove_overlap_with_windows(
        windows_polygons=[opening], separator_polygons=[wall_1, wall_2]
    )
    new_walls_sorted_by_size = sorted(new_walls, key=lambda wall: wall.area)
    assert len(new_walls) == 2
    assert (
        new_walls_sorted_by_size[0].symmetric_difference(box(0, 0, 0.8, 0.5)).area
        < 1e-6
    )
    assert (
        new_walls_sorted_by_size[1].symmetric_difference(box(2.2, 0, 5, 0.5)).area
        < 1e-6
    )


def test_discarding_empty_polygons_if_fully_overlapping():
    wall = box(0, 0, 1, 0.5)
    opening = box(0, 0, 1, 0.5)
    new_walls = DXFImportHandler._remove_overlap_with_windows(
        windows_polygons=[opening], separator_polygons=[wall]
    )
    assert len(new_walls) == 0


def test_create_glas_door():
    """
    Test for asserting that if a balcony door is represented in a dxf with a door & window on top of each other
    we:
    - don't create the window but only the doors
    - The underlying wall (which is created) extends over both the window and the door geometry. This is done to ensure
    that walls are closed.
    """
    planner_data = ReactPlannerData()
    window_geometry = box(0, 0, 200, 30)
    door_1_geometry = box(3, 0, 100, 30)
    door_2_geometry = box(100, 0, 197, 30)
    all_openings_elements = {
        ReactPlannerName.WINDOW: [
            EditorReadyEntity(geometry=window_geometry),
        ],
        ReactPlannerName.DOOR: [
            EditorReadyEntity(geometry=door_1_geometry),
            EditorReadyEntity(geometry=door_2_geometry),
        ],
    }
    holes = DXFImportHandler.create_holes_assigned_to_walls(
        planner_data=planner_data,
        all_opening_elements=all_openings_elements,
        scale_to_cm=1,
    )
    assert len(holes) == 2
    assert {hole.name for hole in holes.values()} == {"Door"}
    sorted_door_geometries = sorted(
        [Polygon(hole.coordinates[0]) for hole in holes.values()],
        key=lambda polygon: polygon.centroid.x,
    )

    assert sorted_door_geometries[0].symmetric_difference(door_1_geometry).area < 1e-6
    assert sorted_door_geometries[1].symmetric_difference(door_2_geometry).area < 1e-6
    walls = [line for line in planner_data.layers["layer-1"].lines.values()]
    assert len(walls) == 1
    wall = walls[0]
    wall_polygon = Polygon(wall.coordinates[0])
    assert wall_polygon.symmetric_difference(window_geometry).area < 1e-6


def test_create_door_window_composite_opening(mocker):
    """
    This test asserts that a opening composed of a larger window and an overlapping door
    creates the door + the 2 window pieces on the left and the right side
                         .    .
                     .       |
                   .    Door |
    ..............___________.....
    |                            |
    |         Window             |
    .............................
    """

    round_opening_length_spy = mocker.spy(
        ReactPlannerElementFactory, "_round_down_opening_length_to_nearest_int_in_cm"
    )

    window_polygon = box(0, 0, 400, 50)
    door_polygon = box(250, 20, 360, 48)
    all_openings_elements = {
        ReactPlannerName.WINDOW: [
            EditorReadyEntity(geometry=window_polygon),
        ],
        ReactPlannerName.DOOR: [
            EditorReadyEntity(geometry=door_polygon),
        ],
    }
    planner_data = ReactPlannerData()
    holes = DXFImportHandler.create_holes_assigned_to_walls(
        planner_data=planner_data,
        all_opening_elements=all_openings_elements,
        scale_to_cm=1,
    )

    assert len(holes) == 3
    assert round_opening_length_spy.call_count == 3
    windows = [
        hole for hole in holes.values() if hole.name == ReactPlannerName.WINDOW.value
    ]
    doors = [
        hole for hole in holes.values() if hole.name == ReactPlannerName.DOOR.value
    ]
    assert len(windows) == 2
    assert len(doors) == 1
    window_geometries = sorted(
        [Polygon(hole.coordinates[0]) for hole in windows],
        key=lambda polygon: polygon.centroid.x,
    )
    assert window_geometries[0].symmetric_difference(box(0, 0, 250, 50)).area < 1e-2
    assert window_geometries[1].symmetric_difference(box(360, 0, 400, 50)).area < 1e-2

    door = doors[0]
    door_geometry = Polygon(door.coordinates[0])
    assert door_geometry.symmetric_difference(box(250, 0, 360, 50)).area < 1e-6

    for window_geometry in window_geometries:
        assert not window_geometry.intersects(door_geometry)


def test_remaining_window_geometries():
    """
    We need to ensure here that the remaining window geometries are
    only the 2 pieces on the left and the right side of the door and not extending everything.
    For this We buffer the door a little before we take the difference.


    Window Door Window
    .....______......
    .    |      |   .
    .....|______|....

    """
    inprecission = BUFFER_DOOR_WINDOW_DIFFERENCE_IN_CM
    wall_geometry = box(
        0, 0, 400, 100
    )  # This wall geometry is build as the union from window and door geometry
    adjusted_door_geometry = box(200, 0, 300, 100 - inprecission)
    remaining_window_geoms = DXFImportHandler._remaing_window_geometries(
        wall_geometry=wall_geometry,
        adjusted_door_geometry=adjusted_door_geometry,
    )
    assert len(remaining_window_geoms) == 2
    sorted_windows = sorted(
        remaining_window_geoms, key=lambda window: window.centroid.x
    )
    assert sorted_windows[0].symmetric_difference(box(0, 0, 200, 100)).area < 0.02
    assert sorted_windows[1].symmetric_difference(box(300, 0, 400, 100)).area < 0.02


@pytest.mark.parametrize(
    "area_polygon,expected_nbr_of_shafts",
    [(box(0, 0, 0.1, 0.2), 1), (box(0, 0, 1, 2), 0)],
)
def test_create_shafts_for_small_areas(area_polygon, expected_nbr_of_shafts):
    pixels_per_meter = 1000
    area_polygon = scale(
        geom=area_polygon, xfact=pixels_per_meter, yfact=pixels_per_meter
    )
    assert (
        len(
            DXFImportHandler.create_shafts_for_small_areas(
                areas=[ReactPlannerArea(coords=mapping(area_polygon)["coordinates"])],
                pixels_per_meter=pixels_per_meter,
            )
        )
        == expected_nbr_of_shafts
    )


def test_create_shafts_for_non_rectangular_small_areas():
    pixels_per_meter = 1000
    l_shaped_area_polygon = scale(
        geom=Polygon([(0, 0), (0.4, 0), (0.4, 0.8), (0.3, 0.8), (0.3, 0.1), (0, 0.1)]),
        xfact=pixels_per_meter,
        yfact=pixels_per_meter,
        origin=(0, 0),
    )

    shafts = DXFImportHandler.create_shafts_for_small_areas(
        areas=[ReactPlannerArea(coords=mapping(l_shaped_area_polygon)["coordinates"])],
        pixels_per_meter=pixels_per_meter,
    )
    assert len(shafts) == 1
    assert (
        shafts[0].geometry.symmetric_difference(box(310.0, 10.0, 390.0, 790.0)).area
        < 0.01
    )

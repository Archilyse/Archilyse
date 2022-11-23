import pytest
from shapely.geometry import Point
from shapely.ops import unary_union

from brooks.util.geometry_ops import buffer_unbuffer_geometry
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from simulations.hexagonizer import Hexagonizer, HexagonizerGraph


def test_hexagons_no_connectivity(react_data_valid_square_space_with_entrance_door):
    layout = ReactPlannerToBrooksMapper().get_layout(
        planner_elements=ReactPlannerData(
            **react_data_valid_square_space_with_entrance_door
        ),
        scaled=True,
    )
    for area in sorted(
        list(layout.areas),
        key=lambda x: (  # 3 criteria to sort as there are areas with same area size
            x.footprint.area,
            x.footprint.centroid.x,
            x.footprint.centroid.y,
        ),
    ):
        hexagons = list(
            Hexagonizer.get_hexagons(z_coord=0, pol=area.footprint, resolution=0.5)
        )
        assert len(hexagons) == 27
        area_footprint = next(iter(layout.areas)).footprint
        points = [Point(hexagon.centroid) for hexagon in hexagons]
        for point in points:
            assert point.intersects(area_footprint)

        result = buffer_unbuffer_geometry(buffer=1.0, geometry=unary_union(points))
        assert result.intersection(area_footprint).area == result.area


@pytest.mark.parametrize(
    "area_index, num_nodes, num_edges",
    [(1, 18, 39), (2, 19, 46), (3, 26, 67), (4, 30, 84), (5, 63, 192)],
)
def test_hexagonizer_graph_nodes_edges_generation(
    react_planner_background_image_one_unit, area_index, num_nodes, num_edges
):
    layout = ReactPlannerToBrooksMapper().get_layout(
        planner_elements=ReactPlannerData(**react_planner_background_image_one_unit),
        scaled=True,
    )
    area = sorted(
        list(layout.areas),
        key=lambda x: (
            x.footprint.area,
            x.footprint.centroid.x,
            x.footprint.centroid.y,
        ),
    )[area_index]
    graph = HexagonizerGraph(polygon=area.footprint, resolution=0.5).connected_graph
    assert (len(graph.nodes), len(graph.edges)) == (num_nodes, num_edges)


def test_hexagonizer_graph_clean_non_connected_nodes(
    mocker, annotations_plan_4976, georef_plan_values
):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_4976), scaled=True
    )
    unit_polygon = layout.get_footprint_no_features()

    hex_graph = HexagonizerGraph(polygon=unit_polygon, resolution=0.5)

    # REMOVING NON CONNECTED NODES
    assert len(hex_graph.obs_points) == 1172

    # KEEPING NON CONNECTED NODES
    mocker.patch.object(HexagonizerGraph, "_clean_unconnected_nodes")

    hex_graph = HexagonizerGraph(polygon=unit_polygon, resolution=0.5)

    assert len(hex_graph.obs_points) == 1176

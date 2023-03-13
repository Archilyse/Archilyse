import pytest
from shapely.geometry import Polygon, box

from brooks.models import SimLayout, SimSpace
from simulations.hexagonizer import HexagonizerGraph
from tasks.connectivity_tasks import get_hex_graph_and_resolution


@pytest.mark.parametrize(
    "xymax, expected_resolution",
    [(10, 0.25), (25, 0.27), (40, 0.43), (50, 0.54)],
)
def test_connectivity_get_hex_graph_and_resolution(xymax, expected_resolution):
    space = SimSpace(footprint=box(0, 0, xymax, xymax))

    _, resolution = get_hex_graph_and_resolution(unit_layout=SimLayout(spaces={space}))
    assert resolution == expected_resolution


@pytest.fixture(scope="module")
def hex_graph():
    return HexagonizerGraph(
        polygon=Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
        resolution=0.25,
    )


@pytest.mark.parametrize(
    "pols, found",
    [
        (Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]), True),
        (Polygon([(-1, 0), (0, 0), (0, 1), (-1, 1)]), True),  # buffer
        (Polygon([(-2, 0), (-1, 0), (-1, 1), (-2, 1)]), False),  # Too far
    ],
)
def test_pois_distance2pols(pols, found, hex_graph):
    from simulations.connectivity import ConnectivitySimulator

    result = ConnectivitySimulator(graph=hex_graph.connected_graph).pois_distance2pols(
        [pols]
    )

    if found:
        assert sorted(result)[0] == 0.0
    else:
        assert sorted(result)[0] > 10

import random
from collections import defaultdict

import pytest
from shapely.affinity import scale
from shapely.geometry import MultiPolygon, box
from shapely.strtree import STRtree

from brooks.models import SimOpening
from brooks.types import AnnotationType
from handlers.ifc.importer.ifc_floor_plan_plot import IfcFloorPlanPlot
from ifc_reader.constants import IFC_DOOR, IFC_WALL, IFC_WINDOW
from ifc_reader.types import Ifc2DEntity


def test_regression_create_plot(mocker, ifc_file_reader_steiner_example):
    """
    Tests, that the geometries destined for plotting are sorted in IfcFloorplanPlot._create_plot and are passed to the
     _plot_extra_opening_geometry method with consistent ordering
    """
    import handlers.ifc.importer.ifc_floor_plan_plot as plotter_module

    mocker.patch.object(plotter_module, "STRtree")
    mocker.patch.object(plotter_module, "get_visual_center")

    expected_calls = defaultdict(list)
    geometries_by_ifc_type = defaultdict(list)
    polygon = box(0, 0, 1, 1)
    for ifc_type in [IFC_WINDOW, IFC_DOOR, IFC_WALL]:
        for i in range(1, 5):
            geometry = MultiPolygon([scale(polygon, xfact=i, yfact=i)])
            geometries_by_ifc_type[ifc_type].append(
                Ifc2DEntity(
                    geometry=geometry,
                    min_height=0.0,
                    max_height=1.0,
                    ifc_type=ifc_type,
                )
            )
            expected_calls[ifc_type].append(
                mocker.call(geometry=geometry, wall_strtree=mocker.ANY)
            )
        random.shuffle(geometries_by_ifc_type[ifc_type])

    plotter = IfcFloorPlanPlot(
        storey_entities=geometries_by_ifc_type, width=0, height=0
    )
    plot_opening_geom_spy = mocker.spy(plotter, "_plot_extra_opening_geometry")

    plotter.create_plot(scale_factor=1)
    plot_opening_geom_spy.assert_has_calls(
        expected_calls[AnnotationType.DOOR.name]
        + expected_calls[AnnotationType.WINDOW.name],
        any_order=False,
    )


@pytest.mark.parametrize(
    "wall_coordinates, should_adjust_opening",
    [((0, 0, 1, 10), True), ((0, 0, 5, 6), False), ((0, 0, 6, 10), False)],
)
def test_regression_plot_extra_opening_geometry(
    mocker, ifc_file_reader_steiner_example, wall_coordinates, should_adjust_opening
):
    """
    Tests, that the wall geometries passed to IfcFloorplanPlot._plot_extra_opening_geometry are always correctly
    recognized as square-shaped (or near-square-shaped) and that it calls adjust_geometry_to_wall consistently
    """
    mapper_mock = mocker.spy(SimOpening, "adjust_geometry_to_wall")

    opening_geometry = box(0, -1, 0.25, 1.25)
    wall_geometry = box(*wall_coordinates)
    wall_strtree = STRtree([wall_geometry])

    ifc_plotter = IfcFloorPlanPlot(storey_entities={}, width=0, height=0)
    list(
        ifc_plotter._plot_extra_opening_geometry(
            geometry=opening_geometry,
            wall_strtree=wall_strtree,
        )
    )
    if should_adjust_opening:
        mapper_mock.assert_called_once_with(
            opening=opening_geometry, wall=wall_geometry, buffer_width=1.05
        )
    else:
        mapper_mock.assert_not_called()

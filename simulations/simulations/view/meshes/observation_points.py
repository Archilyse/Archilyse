from typing import List, Optional, Set, Tuple

from numpy import array
from shapely.geometry import CAP_STYLE, JOIN_STYLE

from brooks.models import SimArea
from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.exceptions import InvalidShapeException, LayoutTriangulationException
from simulations.hexagonizer import Hexagonizer
from simulations.view.meshes import GeoreferencingTransformation


def get_observation_points_by_area(
    areas: Set[SimArea],
    level_baseline: float,
    georeferencing_parameters: GeoreferencingTransformation,
    resolution: float,
    obs_height: float,
    buffer: Optional[float] = None,
) -> List[Tuple[SimArea, array]]:
    observation_points: List[
        Tuple[SimArea, List[Tuple[float, float, float]]]
    ] = []  # (area, [p0, p1, ..., pn])

    buffer = buffer or resolution
    observation_height = level_baseline + obs_height

    for area in sorted(
        areas,
        key=lambda x: (  # 3 criteria to sort as there might be areas with same area size
            x.footprint.area,
            x.footprint.centroid.x,
            x.footprint.centroid.y,
        ),
    ):
        polygon = area.footprint.buffer(
            -1 * buffer,
            cap_style=CAP_STYLE.square,
            join_style=JOIN_STYLE.mitre,
            mitre_limit=2,
        )
        try:
            polygon = ensure_geometry_validity(geometry=polygon)
            if len(polygon.bounds) != 4:
                continue
        except InvalidShapeException:
            continue

        if area_observation_points := [
            hexagon.centroid
            for hexagon in Hexagonizer.get_hexagons(
                pol=polygon,
                z_coord=observation_height,
                resolution=resolution,
            )
        ]:
            observation_points.append((area, area_observation_points))

    if observation_points:
        return [
            (area, georeferencing_parameters.apply(points))
            for area, points in observation_points
        ]
    raise LayoutTriangulationException(
        "Couldn't find any observation points for layout area footprints."
    )

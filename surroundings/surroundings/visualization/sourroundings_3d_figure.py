from collections import defaultdict
from typing import Iterator, List, Optional

import matplotlib
import numpy as np
import plotly

from common_utils.constants import SurroundingType
from surroundings.utils import SurrTrianglesType

# Setup plotly.py to use external Orca
plotly.io.orca.config.use_xvfb = True
plotly.io.orca.config.save()


def create_3d_surroundings_from_triangles_per_type(
    filename: str,
    triangles_per_surroundings_type: Iterator[SurrTrianglesType],
    triangles_per_layout: Optional[Iterator[SurrTrianglesType]] = None,
    auto_open: bool = True,
):
    identifier_to_triangles = defaultdict(list)
    for identifier, triangle in triangles_per_surroundings_type:
        identifier_to_triangles[identifier.name].append(
            np.asanyarray(triangle)[:, [1, 0, 2]]
        )
    triangles_per_layout = triangles_per_layout or []
    for identifier, triangles in triangles_per_layout:
        identifier_to_triangles[identifier].extend(triangles)
    identifiers, triangles = map(list, zip(*identifier_to_triangles.items()))

    create_3d_figure(
        triangles=triangles,
        identifiers=identifiers,
        title="",
        filename=filename,
        opacity=1,
        auto_open=auto_open,
    )


color_by_type = {
    SurroundingType.BUILDINGS.name: "lightgray",
    SurroundingType.TREES.name: "green",
    SurroundingType.PARKS.name: "green",
    SurroundingType.FOREST.name: "green",
    SurroundingType.SEA.name: "darkblue",
    SurroundingType.RIVERS.name: "darkcyan",
    SurroundingType.LAKES.name: "darkcyan",
    SurroundingType.GROUNDS.name: "rosybrown",
    SurroundingType.MOUNTAINS.name: "gray",
    SurroundingType.STREETS.name: "black",
    SurroundingType.RAILROADS.name: "violet",
    SurroundingType.HIGHWAY.name: "gold",
    SurroundingType.PRIMARY_STREET.name: "red",
    SurroundingType.SECONDARY_STREET.name: "yellow",
    SurroundingType.TERTIARY_STREET.name: "black",
    SurroundingType.PEDESTRIAN.name: "darkgreen",
    SurroundingType.MOUNTAINS_CLASS_2.name: "white",
    SurroundingType.MOUNTAINS_CLASS_3.name: "grey",
    SurroundingType.MOUNTAINS_CLASS_4.name: "darkgreen",
    SurroundingType.MOUNTAINS_CLASS_5.name: "green",
    SurroundingType.MOUNTAINS_CLASS_6.name: "darkgreen",
}


def create_3d_figure(
    triangles: Iterator[Iterator[np.ndarray]],
    identifiers: List[str],
    title: str,
    filename: str,
    opacity: float = 0.9,
    add_edges: bool = False,
    auto_open: bool = True,
):
    traces = []
    vertices = []

    for triangle, identifier in zip(triangles, identifiers):
        triangle_vertices = np.vstack(triangle).reshape(-1, 3)
        if triangle_vertices.size == 0:
            continue

        x, y, z = triangle_vertices.T
        # view simulation uses north=+x,east=+y and plotly uses top=+x,right=-y
        y = (-1 * np.array(y)).tolist()
        i, j, k = np.arange(triangle_vertices.shape[0]).reshape(-1, 3).T
        vertices += list(zip(x, y, z))

        if add_edges:
            traces.append(
                plotly.graph_objs.Scatter3d(
                    x=[v[0] for v in vertices],
                    y=[v[1] for v in vertices],
                    z=[v[2] for v in vertices],
                    mode="lines",
                    surfacecolor="black",
                )
            )

        traces.append(
            plotly.graph_objs.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                opacity=opacity,
                name=identifier,
                color=color_by_type.get(identifier),
            )
        )

    axis_width = (
        np.array(vertices).max(axis=0) - np.array(vertices).min(axis=0)
    ).max() * 2
    xmin, ymin, zmin = np.array(vertices).min(axis=0)
    scene = dict(
        xaxis=dict(range=(xmin - axis_width, xmin + axis_width)),
        yaxis=dict(range=(ymin - axis_width, ymin + axis_width)),
        zaxis=dict(range=(zmin - axis_width, zmin + axis_width)),
    )

    title = plotly.graph_objs.layout.Title(text=f"{title} - 3D")
    camera = dict(eye=dict(x=0.0, y=0, z=10.0))
    layout = plotly.graph_objs.Layout(
        scene=scene, scene_camera=camera, width=2000, height=2000, title=title
    )
    fig = plotly.graph_objs.Figure(data=traces, layout=layout)
    plotly.offline.plot(fig, filename=filename, auto_open=auto_open)
    matplotlib.pyplot.close()

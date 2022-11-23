import click
from shapely.geometry import Point

from brooks.util.projections import project_geometry
from common_utils.constants import (
    PLOT_DIR,
    REGION,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
)
from handlers import SiteHandler
from handlers.db import PotentialSimulationDBHandler, SiteDBHandler
from handlers.quavis import PotentialViewQuavisHandler, SLAMQuavisHandler
from surroundings.surrounding_handler import generate_view_surroundings
from surroundings.visualization.sourroundings_3d_figure import (
    create_3d_surroundings_from_triangles_per_type,
)


@click.command()
@click.argument("site_id", envvar="site", required=False, type=click.INT)
@click.argument("simulation_id", envvar="simulation", required=False, type=click.INT)
@click.argument("x", envvar="x", required=False, type=click.FLOAT)
@click.argument("y", envvar="y", required=False, type=click.FLOAT)
@click.argument("lat", envvar="lat", required=False, type=click.FLOAT)
@click.argument("lon", envvar="lon", required=False, type=click.FLOAT)
@click.argument(
    "source",
    envvar="source",
    required=False,
    type=SURROUNDING_SOURCES,
)
@click.argument(
    "region",
    envvar="region",
    required=False,
    type=REGION,
)
@click.argument(
    "simulation_version",
    envvar="simulation_version",
    required=False,
    type=SIMULATION_VERSION,
)
@click.argument(
    "sample", envvar="sample", required=False, type=click.BOOL, default=True
)
def main(
    sample: bool,
    site_id: int | None,
    simulation_id: int | None,
    x: float | None,
    y: float | None,
    lat: float | None,
    lon: float | None,
    region: REGION | None,
    source: SURROUNDING_SOURCES | None,
    simulation_version: SIMULATION_VERSION | None,
):
    triangles_per_layout = None

    if (
        (
            simulation_id
            and any([site_id, x, y, lat, lon, region, source, simulation_version])
        )
        or (
            site_id
            and any([simulation_id, x, y, lat, lon, region, source, simulation_version])
        )
        or (x and y and region and any([simulation_id, lat, lon]))
        or (lat and lon and any([simulation_id, x, y]))
        or not (simulation_id or site_id or (((x and y) or (lat and lon)) and region))
    ):
        raise Exception(
            "Provide either a site_id OR simulation_id "
            "OR x, y, region, source (optionally) and simulation_version (optionally) "
            "OR lat, lon, region, source (optionally) and simulation_version (optionally)."
        )

    if site_id:
        site_info = SiteDBHandler.get_by(id=site_id)
        simulation_version = SIMULATION_VERSION[site_info["simulation_version"]]
        triangles_per_layout = SLAMQuavisHandler().get_site_triangles(
            entity_info=site_info, simulation_version=simulation_version
        )
        triangles_per_surroundings_type = SiteHandler.generate_view_surroundings(
            site_info=site_info, sample=sample
        )
        output_name = site_id
    elif simulation_id:
        simulation_info = PotentialSimulationDBHandler.get_by(id=simulation_id)
        simulation_version = SIMULATION_VERSION[simulation_info["simulation_version"]]
        triangles_per_layout = PotentialViewQuavisHandler().get_site_triangles(
            entity_info=simulation_info, simulation_version=simulation_version
        )
        triangles_per_surroundings_type = (
            PotentialViewQuavisHandler().get_surrounding_triangles(
                entity_info=simulation_info, simulation_version=simulation_version
            )
        )
        output_name = simulation_id
    else:
        if x and y and region:
            location = Point(x, y)
            output_name = f"{x}-{y}"
        else:
            location = project_geometry(
                geometry=Point(lon, lat),
                crs_from=REGION.LAT_LON,
                crs_to=region,
            )
            output_name = f"{lat}-{lon}"

        triangles_per_surroundings_type = generate_view_surroundings(
            location=location,
            region=region,
            surroundings_source=source,
            building_footprints=[],
            sample=sample,
            simulation_version=simulation_version or SIMULATION_VERSION.PH_2022_H1,
        )

    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    local_file_name = PLOT_DIR.joinpath(f"{output_name}-3d.html").as_posix()

    create_3d_surroundings_from_triangles_per_type(
        filename=local_file_name,
        triangles_per_layout=triangles_per_layout,
        triangles_per_surroundings_type=triangles_per_surroundings_type,
    )


if __name__ == "__main__":
    main(None, None)

import click
import geopandas

from handlers import PlanHandler


def get_geojson(plan_layout):
    areas = geopandas.GeoDataFrame(
        [(area.id, area.type.name, area.footprint) for area in plan_layout.areas],
        columns=["id", "type", "geometry"],
        crs={"init": "epsg:2056"},
    )
    separators = geopandas.GeoDataFrame(
        [
            (separator.id, separator.type.name, separator.footprint)
            for separator in plan_layout.separators
        ],
        columns=["id", "type", "geometry"],
        crs={"init": "epsg:2056"},
    )
    openings = geopandas.GeoDataFrame(
        [
            (opening.id, opening.type.name, opening.footprint)
            for opening in plan_layout.openings
        ],
        columns=["id", "type", "geometry"],
        crs={"init": "epsg:2056"},
    )
    features = geopandas.GeoDataFrame(
        [
            (feature.id, feature.type.name, feature.footprint)
            for feature in plan_layout.features
            if feature.type.name != "SHAFT"
        ],
        columns=["id", "type", "geometry"],
        crs={"init": "epsg:2056"},
    )

    areas["fill-opacity"] = 0.7
    areas["fill"] = "#ffffff"
    areas["stroke-width"] = 1

    separators["fill-opacity"] = 1
    separators["fill"] = "#333333"
    separators["stroke-width"] = 0

    openings["fill-opacity"] = 1
    openings["fill"] = "#ffffff"
    openings["stroke-width"] = 0

    features["stroke-width"] = 1

    result = areas
    result = result.append(separators)
    result = result.append(openings)
    result = result.append(features)

    return result


@click.command()
@click.option("--plan_id", prompt=True, type=click.INT)
def main(plan_id):
    plan_handler = PlanHandler(plan_id=plan_id)
    plan_layout_scaled = plan_handler.get_layout(
        validate=False,
        classified=True,
        scaled=True,
        georeferenced=False,
        raise_on_inconsistency=True,
    )
    with open(f"{plan_id}_metric_local.json", "w") as fh:
        fh.write(get_geojson(plan_layout_scaled).to_json())

    plan_layout_scaled.apply_georef_transformation(
        georeferencing_transformation=plan_handler.get_georeferencing_transformation(
            to_georeference=True
        )
    )
    with open(f"{plan_id}_lat_lon.json", "w") as fh:
        fh.write(get_geojson(plan_layout_scaled).to_crs(epsg=4326).to_json())


if __name__ == "__main__":
    main()

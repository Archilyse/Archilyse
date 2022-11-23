from functools import partial
from typing import Dict, Tuple, Union

import numpy as np
import pyproj
from methodtools import lru_cache
from pygeos import Geometry, apply
from pyproj import CRS, Transformer
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.ops import transform

from common_utils.constants import REGION

transformers: Dict[Tuple[REGION, REGION], Transformer] = {}


def _pygeos_projection(geometries, crs_from: CRS, crs_to: CRS) -> np.array:
    values = pyproj.transform(
        crs_from,
        crs_to,
        *geometries.T,
    )
    return np.array([*values]).T


def pygeos_project(
    geometries: list[Geometry], crs_from: REGION, crs_to: REGION, include_z: bool = True
) -> list[Geometry]:
    pygeos_transform_partial = partial(
        _pygeos_projection,
        crs_from=REGIONS_CRS[crs_from],
        crs_to=REGIONS_CRS[crs_to],
    )
    return apply(geometries, pygeos_transform_partial, include_z=include_z)


def project_geometry(
    geometry: Union[
        Point, LineString, MultiLineString, Polygon, MultiPolygon, MultiPoint
    ],
    crs_from: REGION,
    crs_to: REGION,
) -> Union[Point, LineString, MultiLineString, Polygon, MultiPolygon]:
    transformer = _get_or_set_transformer(crs_from=crs_from, crs_to=crs_to)
    return transform(transformer.transform, geometry)


def project_xy(
    xs,
    ys,
    crs_from: REGION,
    crs_to: REGION,
):
    transformer = _get_or_set_transformer(crs_from=crs_from, crs_to=crs_to)
    return transformer.transform(xx=xs, yy=ys)


def _get_or_set_transformer(crs_from: REGION, crs_to: REGION) -> Transformer:
    if not transformers.get((crs_from, crs_to)):
        transformers[crs_from, crs_to] = pyproj.Transformer.from_crs(
            crs_from=REGIONS_CRS[crs_from],
            crs_to=REGIONS_CRS[crs_to],
            always_xy=True,
        )
    return transformers[crs_from, crs_to]


_REGIONS_CRS_STR: Dict[REGION, str] = {}


def get_region_crs_str(region: REGION) -> str:
    """For performance reasons in serializers we have this caching method.
    It's also not defined directly as a constant to not increase startup time"""
    if crs_str := _REGIONS_CRS_STR.get(region):
        return crs_str

    _REGIONS_CRS_STR[region] = REGIONS_CRS[region].to_string()
    return _REGIONS_CRS_STR[region]


@lru_cache()
def get_all_crs_proj4():
    """Returns the proj4 string for every CRS. Used proj4 instead of WKT for compatibility with proj4.js in the FE"""
    result = {
        projection.to_string(): projection.to_proj4()
        for projection in REGIONS_CRS.values()
    }
    result["EPSG:2056"] += " +towgs84=674.374,15.056,405.346,0,0,0,0"
    return result


REGIONS_CRS = {
    # GLOBAL
    REGION.LAT_LON: CRS("EPSG:4326"),
    # COUNTRIES
    REGION.MC: CRS("EPSG:32632"),
    REGION.CH: CRS("EPSG:2056"),
    REGION.DK: CRS("EPSG:2198"),
    REGION.AT: CRS("EPSG:31287"),
    REGION.NO: CRS("EPSG:5942"),
    REGION.CZ: CRS("EPSG:5514"),
    REGION.ES: CRS("EPSG:3043"),
    REGION.AD: CRS("EPSG:3043"),
    # ****************** GERMANY **************************
    REGION.DE_BADEN_WURTTEMBERG: CRS("EPSG:5243"),
    REGION.DE_BAYERN: CRS("EPSG:5243"),
    REGION.DE_BERLIN: CRS("EPSG:5243"),
    REGION.DE_BRANDENBURG: CRS("EPSG:5243"),
    REGION.DE_BREMEN: CRS("EPSG:5243"),
    REGION.DE_HAMBURG: CRS("EPSG:5243"),
    REGION.DE_HESSEN: CRS("EPSG:5243"),
    REGION.DE_MECKLENBURG_VORPOMMERN: CRS("EPSG:5243"),
    REGION.DE_NIEDERSACHSEN: CRS("EPSG:5243"),
    REGION.DE_NORDRHEIN_WESTFALEN: CRS("EPSG:5243"),
    REGION.DE_RHEINLAND_PFALZ: CRS("EPSG:5243"),
    REGION.DE_SAARLAND: CRS("EPSG:5243"),
    REGION.DE_SACHSEN: CRS("EPSG:5243"),
    REGION.DE_SACHSEN_ANHALT: CRS("EPSG:5243"),
    REGION.DE_SCHLESWIG_HOLSTEIN: CRS("EPSG:5243"),
    REGION.DE_THURINGEN: CRS("EPSG:5243"),
    # ****************** UNITED STATES **************************
    REGION.US_GEORGIA: CRS("EPSG:26967"),
    REGION.US_PENNSYLVANIA: CRS("EPSG:32618"),
    # ****************** ASIA ***********************************
    REGION.SG: CRS("EPSG:3414"),
    # ****************** EUROPE *********************************
    REGION.EUROPE: CRS("EPSG:3035"),
}

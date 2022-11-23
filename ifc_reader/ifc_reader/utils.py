from typing import Tuple


def from_deg_min_sec_to_degrees(
    degrees: float,
    min: float,
    sec: float,
    micro_sec: float = 0.0,
):
    """
    according to the definiton of RefLatitude, RefLongitude in
    https://standards.buildingsmart.org/IFC/RELEASE/IFC4_1/FINAL/HTML/schema/ifcproductextension/lexical/ifcsite.htm
    """
    return degrees + (min / 60) + (sec / 3600) + (micro_sec / (1e6 * 3600))


def from_lat_lon_to_deg_min_sec(
    value,
) -> Tuple[int, int, int, int]:
    degrees = int(value)
    minutes = (value - degrees) * 60.0
    seconds = (minutes - int(minutes)) * 60.0
    micro_seconds = (seconds - int(seconds)) * 1e6

    return degrees, int(minutes), int(seconds), int(micro_seconds)

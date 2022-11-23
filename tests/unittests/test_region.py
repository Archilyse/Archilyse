from brooks.util.projections import REGIONS_CRS
from common_utils.constants import REGION
from surroundings.constants import OSM_REGIONS_FILENAMES


def test_regions_properly_setup():
    regions_without_osm = {REGION.LAT_LON, REGION.EUROPE}
    for region in REGION:
        assert REGIONS_CRS.get(region), f"region {region} does not have CRS defined"
        if region not in regions_without_osm:
            assert OSM_REGIONS_FILENAMES[region], f"region {region} not set for OSM"

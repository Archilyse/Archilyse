from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, ManualSurroundingTypes
from handlers.db import ManualSurroundingsDBHandler
from surroundings.manual_surroundings.constants import MANUAL_SURR_REGION


class FeatureProviderMixin:
    manual_surrounding_type: ManualSurroundingTypes = None

    def __init__(self, site_id: int, region: REGION):
        self.site_id = site_id
        self.region = region

    def get_features(self) -> list[dict]:
        if surroundings := ManualSurroundingsDBHandler.try_get_by(site_id=self.site_id):
            return [
                feature
                for feature in surroundings["surroundings"]["features"]
                if ManualSurroundingTypes[feature["properties"]["surrounding_type"]]
                == self.manual_surrounding_type
            ]
        return []

    def get_footprint(self) -> Polygon | MultiPolygon:
        return project_geometry(
            geometry=unary_union(
                [
                    Polygon(*feature["geometry"]["coordinates"])
                    for feature in self.get_features()
                ]
            ),
            crs_from=MANUAL_SURR_REGION,
            crs_to=self.region,
        )

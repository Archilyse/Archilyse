import pytest
from shapely.geometry import LineString, box

from brooks.models import SimArea, SimFeature, SimLayout, SimSpace
from brooks.types import AreaType, FeatureType
from handlers.create_area_splitter_for_kitchen import (
    CreateAreaSplittersFromKitchenElements,
)


class TestCreateAreaSplittersFromKitchenElements:
    def test_create_splitters(self):
        area = SimArea(footprint=box(0, 0, 10, 5), area_type=AreaType.NOT_DEFINED)
        kitchen_features = {
            SimFeature(footprint=box(0, 0, 1, 4), feature_type=FeatureType.KITCHEN),
            SimFeature(footprint=box(4, 0, 5, 3), feature_type=FeatureType.KITCHEN),
        }
        area.features = kitchen_features
        space = SimSpace(footprint=area.footprint)
        space.add_area(area)
        layout = SimLayout(spaces={space})
        splitters = [
            splitter
            for splitter in CreateAreaSplittersFromKitchenElements.create_splitters(
                layout=layout
            )
        ]
        assert len(splitters) == 1
        splitter = splitters[0]
        assert (
            splitter.symmetric_difference(
                LineString([(-0.02, 4.05), (5.05, 4.05), (5.05, -0.02)])
            ).area
            < 1e-9
        )

        spliter_extensions_over_area = splitter.difference(area.footprint)
        for splitter_extension in spliter_extensions_over_area.geoms:
            assert splitter_extension.length == pytest.approx(
                expected=0.02, abs=1e-9
            )  # This is necessary to ensure that the splitters are overlapping with the walls

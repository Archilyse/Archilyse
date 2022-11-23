from shapely.geometry import box

from common_utils.constants import REGION
from surroundings.v2.swisstopo.surroundings_mixin import SwissTopoSurroundingsMixin
from tests.surroundings_utils import flat_elevation_handler


class TestSwissTopoSurroundingsMixin:
    def test_generate_small_items(self, mock_surrounding_handlers):
        import surroundings.v2.swisstopo.surroundings_mixin as swisstopo_surroundings_mixin

        surrounding_handlers = [
            swisstopo_surroundings_mixin.SwissTopoParksHandler,
            swisstopo_surroundings_mixin.SwissTopoRailwayHandler,
            swisstopo_surroundings_mixin.SwissTopoRiverLinesHandler,
            swisstopo_surroundings_mixin.SwissTopoStreetsHandler,
            swisstopo_surroundings_mixin.SwissTopoBuildingsHandler,
            swisstopo_surroundings_mixin.SwissTopoTreeHandler,
            swisstopo_surroundings_mixin.SwissTopoForestHandler,
        ]
        fake_surrounding_handlers, fake_triangles = mock_surrounding_handlers(
            swisstopo_surroundings_mixin,
            surrounding_handler_types=surrounding_handlers,
        )

        bounding_box = box(0, 0, 1, 1)
        region = REGION.CH
        elevation_handler = flat_elevation_handler(
            bounds=bounding_box.bounds, elevation=1.0
        )

        triangles = set(
            SwissTopoSurroundingsMixin.generate_small_items(
                bounding_box=bounding_box,
                region=region,
                elevation_handler=elevation_handler,
            )
        )

        assert triangles == fake_triangles
        for fake_surrounding_handler in fake_surrounding_handlers:
            fake_surrounding_handler.assert_called_once_with(
                bounding_box=bounding_box,
                region=region,
                elevation_handler=elevation_handler,
            )

    def test_generate_big_items(self, mock_surrounding_handlers):
        import surroundings.v2.swisstopo.surroundings_mixin as swisstopo_surroundings_mixin

        surrounding_handlers = [
            swisstopo_surroundings_mixin.SwissTopoWaterHandler,
        ]
        fake_surrounding_handlers, fake_triangles = mock_surrounding_handlers(
            swisstopo_surroundings_mixin,
            surrounding_handler_types=surrounding_handlers,
        )

        bounding_box = box(0, 0, 1, 1)
        region = REGION.CH
        elevation_handler = flat_elevation_handler(
            bounds=bounding_box.bounds, elevation=1.0
        )

        triangles = set(
            SwissTopoSurroundingsMixin.generate_big_items(
                bounding_box=bounding_box,
                region=region,
                elevation_handler=elevation_handler,
            )
        )

        assert triangles == fake_triangles
        for mocked_surrounding_handler in fake_surrounding_handlers:
            mocked_surrounding_handler.assert_called_once_with(
                bounding_box=bounding_box,
                region=region,
                elevation_handler=elevation_handler,
            )

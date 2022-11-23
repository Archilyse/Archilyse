from rasterio.windows import Window

from common_utils.constants import SurroundingType
from surroundings.v2.grounds import GroundHandler
from surroundings.v2.grounds.ground_handler import LOWERING_CONSTRUCTION_SITE


class TestGroundHandler:
    def test_get_triangles(self, mocker):
        import surroundings.v2.grounds.ground_handler as gh

        fake_raster_window = mocker.MagicMock()
        fake_raster_window.width = 1
        fake_raster_window.height = 2

        fake_triangle = mocker.MagicMock()
        fake_excavator = mocker.MagicMock()
        fake_excavator.excavate.return_value = iter([fake_triangle])

        mocked_excavator = mocker.patch.object(
            gh, "GroundExcavator", return_value=fake_excavator
        )
        mocked_get_triangles = mocker.patch.object(gh, "get_triangles")

        building_footprints = [mocker.ANY]
        ground_handler = GroundHandler(raster_window=fake_raster_window)
        triangles = list(
            ground_handler.get_triangles(building_footprints=building_footprints)
        )

        mocked_get_triangles.assert_called_once_with(
            transform=fake_raster_window.transform,
            grid_values=fake_raster_window.grid_values,
            window=Window(col_off=0, row_off=0, width=1, height=2),
        )
        mocked_excavator.assert_called_once_with(
            building_footprints=building_footprints
        )
        mocked_excavator.return_value.excavate.assert_called_once_with(
            triangles=mocked_get_triangles.return_value,
            lowering_construction_site=LOWERING_CONSTRUCTION_SITE,
        )
        assert triangles == [(SurroundingType.GROUNDS, fake_triangle)]

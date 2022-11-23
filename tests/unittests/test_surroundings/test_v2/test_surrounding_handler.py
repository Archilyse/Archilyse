from typing import Collection

import pytest
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, Polygon, box
from shapely.ops import unary_union

from common_utils.constants import REGION, SurroundingType
from surroundings.srtm.raster_window_provider import SRTMRasterWindowProvider
from surroundings.swisstopo.raster_window_provider import (
    SwissTopoGroundsRasterWindowProvider,
)
from surroundings.v2.constants import (
    DEFAULT_SAFETY_BUFFER,
    SAFETY_BUFFER_BY_SURROUNDING_TYPE,
)
from surroundings.v2.surrounding_handler import (
    OSMSlamSurroundingHandler,
    OSMSurroundingHandler,
    SlamSurroundingHandler,
    SurroundingHandler,
    SwissTopoSlamSurroundingHandler,
    SwissTopoSurroundingHandler,
)


class _TestSurroundingHandler:
    instance_cls = SurroundingHandler

    def get_instance(
        self,
        region: REGION | None = None,
        location: Point | None = None,
        building_footprints: Collection[Polygon] | None = None,
        sample: bool = False,
    ) -> SurroundingHandler:
        return self.instance_cls(
            region=region,
            location=location or Point(0, 0),
            building_footprints=building_footprints or [],
            sample=sample,
        )

    @pytest.fixture
    def mocked_small_items_elevation_handler(self, mocker):
        fake_small_items_elevation_handler = mocker.patch.object(
            self.instance_cls, "_small_items_elevation_handler"
        )
        return fake_small_items_elevation_handler

    @pytest.fixture
    def mocked_big_items_elevation_handler(self, mocker):
        fake_big_items_elevation_handler = mocker.patch.object(
            self.instance_cls, "_big_items_elevation_handler"
        )
        return fake_big_items_elevation_handler

    @pytest.fixture
    def mocked_small_items_triangles(self, mocker):
        fake_small_items_triangles = [mocker.MagicMock()]
        mocked_generate_small_items = mocker.patch.object(
            self.instance_cls,
            "generate_small_items",
            return_value=iter(fake_small_items_triangles),
        )
        return mocked_generate_small_items, fake_small_items_triangles

    @pytest.fixture
    def mocked_big_items_triangles(self, mocker):
        fake_big_items_triangles = [mocker.MagicMock()]
        mocked_generate_big_items = mocker.patch.object(
            self.instance_cls,
            "generate_big_items",
            return_value=iter(fake_big_items_triangles),
        )
        return mocked_generate_big_items, fake_big_items_triangles

    @pytest.fixture
    def mocked_grounds_raster_window(self, mocker):
        return mocker.patch.object(
            self.instance_cls,
            "_grounds_raster_window",
        )

    @pytest.fixture
    def mocked_extended_grounds_raster_window(self, mocker):
        return mocker.patch.object(
            self.instance_cls,
            "_extended_grounds_raster_window",
        )

    @pytest.fixture
    def mocked_ground_handler(self, mocker):
        import surroundings.v2.surrounding_handler

        fake_ground_triangles = [mocker.MagicMock()]
        fake_ground_handler = mocker.MagicMock()
        fake_ground_handler.get_triangles.return_value = iter(fake_ground_triangles)
        mocked_ground_handler = mocker.patch.object(
            surroundings.v2.surrounding_handler,
            "GroundHandler",
            return_value=fake_ground_handler,
        )
        return mocked_ground_handler, fake_ground_triangles

    @pytest.fixture
    def patch_raster_window_provider(self, mocker):
        def _internal(raster_window_provider_name: str, raster_window):
            import surroundings.v2.surrounding_handler

            fake_raster_window_provider = mocker.MagicMock()
            fake_raster_window_provider.get_raster_window.return_value = raster_window
            mocked_raster_window_provider = mocker.patch.object(
                surroundings.v2.surrounding_handler,
                raster_window_provider_name,
                return_value=fake_raster_window_provider,
            )

            return mocked_raster_window_provider

        return _internal

    @pytest.mark.parametrize(
        "sample, expected_bbox_bounds",
        [
            (True, (-200.0, -200.0, 200.0, 200.0)),
            (False, (-500.0, -500.0, 500.0, 500.0)),
        ],
    )
    def test_small_items_bbox(self, sample, expected_bbox_bounds):
        assert self.get_instance(
            location=Point(0, 0), sample=sample
        )._small_items_bbox == box(*expected_bbox_bounds)

    @pytest.mark.parametrize(
        "sample, expected_bbox_bounds",
        [
            (True, (-200.0, -200.0, 200.0, 200.0)),
            (False, (-5000.0, -5000.0, 5000.0, 5000.0)),
        ],
    )
    def test_big_items_bbox(self, sample, expected_bbox_bounds):
        assert self.get_instance(
            location=Point(0, 0), sample=sample
        )._big_items_bbox == box(*expected_bbox_bounds)

    @pytest.mark.parametrize(
        "sample, expected_bounds",
        [
            (True, (-200.0, -200.0, 200.0, 200.0)),
            (False, (-500.0, -500.0, 500.0, 500.0)),
        ],
    )
    @pytest.mark.parametrize(
        "region, expected_raster_window_provider",
        [
            ("ANY OTHER REGION", SRTMRasterWindowProvider),
            (REGION.CH, SwissTopoGroundsRasterWindowProvider),
        ],
    )
    def test_grounds_raster_window(
        self,
        region,
        expected_raster_window_provider,
        sample,
        expected_bounds,
        patch_raster_window_provider,
        mocker,
    ):
        fake_raster_window = mocker.MagicMock()
        mocked_raster_window_provider = patch_raster_window_provider(
            expected_raster_window_provider.__name__, raster_window=fake_raster_window
        )

        grounds_raster_window = self.get_instance(
            region=region, location=Point(0, 0), sample=sample
        )._grounds_raster_window

        assert grounds_raster_window == fake_raster_window
        mocked_raster_window_provider.assert_called_once_with(
            region=region, bounds=expected_bounds
        )

    @pytest.mark.parametrize("region", list(REGION))
    def test_extended_grounds_raster_window(
        self,
        region,
        patch_raster_window_provider,
        mocker,
    ):
        fake_raster_window = mocker.MagicMock()
        mocked_raster_window_provider = patch_raster_window_provider(
            SRTMRasterWindowProvider.__name__, raster_window=fake_raster_window
        )

        extended_grounds_raster_window = self.get_instance(
            region=region,
            location=Point(0, 0),
        )._extended_grounds_raster_window

        assert extended_grounds_raster_window == fake_raster_window
        mocked_raster_window_provider.assert_called_once_with(
            region=region, resolution=300, bounds=(-50000.0, -50000.0, 50000.0, 50000.0)
        )

    def test_small_items_elevation_handler(self, mocked_grounds_raster_window, mocker):
        import surroundings.v2.surrounding_handler

        spy_elevation_handler = mocker.spy(
            surroundings.v2.surrounding_handler, "ElevationHandler"
        )

        small_items_elevation_handler = (
            self.get_instance()._small_items_elevation_handler
        )

        spy_elevation_handler.assert_called_once_with(
            raster_window=mocked_grounds_raster_window
        )
        assert small_items_elevation_handler == spy_elevation_handler.spy_return

    def test_big_items_elevation_handler(
        self,
        mocked_grounds_raster_window,
        mocked_extended_grounds_raster_window,
        mocker,
    ):
        import surroundings.v2.surrounding_handler

        mocked_elevation_handler = mocker.patch.object(
            surroundings.v2.surrounding_handler, "MultiRasterElevationHandler"
        )

        big_items_elevation_handler = self.get_instance()._big_items_elevation_handler

        mocked_elevation_handler.assert_called_once_with(
            primary_window=mocked_grounds_raster_window,
            secondary_window=mocked_extended_grounds_raster_window,
        )
        assert big_items_elevation_handler == mocked_elevation_handler.return_value

    def test_big_items_elevation_handler_sample_mode(
        self, mocked_grounds_raster_window, mocker
    ):
        import surroundings.v2.surrounding_handler

        spy_elevation_handler = mocker.spy(
            surroundings.v2.surrounding_handler, "ElevationHandler"
        )
        surrounding_handler = self.get_instance(sample=True)

        big_items_elevation_handler = surrounding_handler._big_items_elevation_handler

        assert big_items_elevation_handler == spy_elevation_handler.spy_return
        spy_elevation_handler.assert_called_once_with(
            raster_window=mocked_grounds_raster_window
        )

    def test_generate_items_triangles(
        self,
        mocked_small_items_triangles,
        mocked_big_items_triangles,
        mocked_small_items_elevation_handler,
        mocked_big_items_elevation_handler,
        mocker,
    ):
        (
            mocked_generate_small_items,
            fake_small_items_triangles,
        ) = mocked_small_items_triangles
        mocked_generate_big_items, fake_big_items_triangles = mocked_big_items_triangles

        region = REGION.CH
        location = Point(0, 0)
        surrounding_handler = self.get_instance(region=region, location=location)

        triangles = list(surrounding_handler._generate_items_triangles())

        assert triangles == fake_small_items_triangles + fake_big_items_triangles
        mocked_generate_small_items.assert_called_once_with(
            region=region,
            bounding_box=box(-500.0, -500.0, 500.0, 500.0),
            elevation_handler=mocked_small_items_elevation_handler,
        )
        mocked_generate_big_items.assert_called_once_with(
            region=region,
            bounding_box=box(-5000.0, -5000.0, 5000.0, 5000.0),
            elevation_handler=mocked_big_items_elevation_handler,
        )

    def test_generate_ground_triangles(
        self,
        mocked_grounds_raster_window,
        mocked_extended_grounds_raster_window,
        mocked_ground_handler,
        mocker,
    ):
        import surroundings.v2.surrounding_handler

        fake_un_mountains_triangles = [mocker.MagicMock()]
        fake_un_mountains_handler = mocker.MagicMock()
        fake_un_mountains_handler.get_triangles.return_value = iter(
            fake_un_mountains_triangles
        )
        mocked_un_mountains_handler = mocker.patch.object(
            surroundings.v2.surrounding_handler,
            "UNMountainsHandler",
            return_value=fake_un_mountains_handler,
        )

        mocked_ground_handler, fake_ground_triangles = mocked_ground_handler

        location = Point(0, 0)
        building_footprints = [box(0, 0, 1, 1)]

        surrounding_handler = self.get_instance(
            location=location, building_footprints=building_footprints
        )
        triangles = list(surrounding_handler._generate_ground_triangles())

        assert triangles == fake_ground_triangles + fake_un_mountains_triangles
        mocked_ground_handler.assert_called_once_with(
            raster_window=mocked_grounds_raster_window,
        )
        mocked_ground_handler.return_value.get_triangles.assert_called_once_with(
            building_footprints=building_footprints
        )
        mocked_un_mountains_handler.assert_called_once_with(
            raster_window=mocked_extended_grounds_raster_window,
            exclusion_bounds=surrounding_handler._small_items_bbox.bounds,
        )
        fake_un_mountains_handler.get_triangles.assert_called_once_with()

    def test_generate_ground_triangles_sample_mode(
        self,
        mocked_grounds_raster_window,
        mocked_extended_grounds_raster_window,
        mocked_ground_handler,
    ):
        mocked_ground_handler, fake_ground_triangles = mocked_ground_handler

        location = Point(0, 0)
        building_footprints = [box(0, 0, 1, 1)]

        surrounding_handler = self.get_instance(
            location=location, building_footprints=building_footprints, sample=True
        )
        triangles = list(surrounding_handler._generate_ground_triangles())

        assert triangles == fake_ground_triangles
        mocked_ground_handler.assert_called_once_with(
            raster_window=mocked_grounds_raster_window,
        )
        mocked_ground_handler.return_value.get_triangles.assert_called_once_with(
            building_footprints=building_footprints
        )

    def test_exclusion_area_by_surrounding_type(self):
        building_footprints = [box(0, 0, 1, 1), box(2, 2, 3, 3)]
        surrounding_handler = self.get_instance(building_footprints=building_footprints)
        building_footprints_union = unary_union(building_footprints)
        assert surrounding_handler._exclusion_area_by_surrounding_type == {
            surrounding_type: building_footprints_union.buffer(
                SAFETY_BUFFER_BY_SURROUNDING_TYPE.get(
                    surrounding_type, DEFAULT_SAFETY_BUFFER
                ),
                join_style=JOIN_STYLE.mitre,
                cap_style=CAP_STYLE.square,
            )
            for surrounding_type in SurroundingType
        }

    # def test_crop_triangles(self):
    #     raise NotImplementedError

    def test_generate_view_surroundings(self, mocker):
        fake_exclusion_area_by_surrounding_type = mocker.patch.object(
            self.instance_cls,
            "_exclusion_area_by_surrounding_type",
        )

        items_triangles = iter([mocker.MagicMock()])
        cropped_items_triangles = [mocker.MagicMock()]
        ground_triangles = [mocker.MagicMock()]

        mocked_generate_items_triangles = mocker.patch.object(
            self.instance_cls, "_generate_items_triangles", return_value=items_triangles
        )
        mocked_crop_triangles = mocker.patch.object(
            self.instance_cls,
            "_crop_triangles",
            return_value=iter(cropped_items_triangles),
        )
        mocked_generate_ground_triangles = mocker.patch.object(
            self.instance_cls,
            "_generate_ground_triangles",
            return_value=iter(ground_triangles),
        )

        view_surroundings = list(self.get_instance().generate_view_surroundings())

        assert view_surroundings == cropped_items_triangles + ground_triangles

        mocked_generate_items_triangles.assert_called_once_with()
        mocked_generate_ground_triangles.assert_called_once_with()
        mocked_crop_triangles.assert_called_once_with(
            triangles=items_triangles,
            exclusion_area_by_surrounding_type=fake_exclusion_area_by_surrounding_type,
        )


class _TestSlamSurroundingHandler(_TestSurroundingHandler):
    instance_cls = SlamSurroundingHandler

    def get_instance(
        self,
        site_id: int | None = None,
        region: REGION | None = None,
        location: Point | None = None,
        building_footprints: Collection[Polygon] | None = None,
        sample: bool = False,
    ) -> SurroundingHandler:
        return self.instance_cls(
            site_id=site_id or 1,
            region=region,
            location=location or Point(0, 0),
            building_footprints=building_footprints or [],
            sample=sample,
        )

    def test_generate_items_triangles(
        self,
        mocked_small_items_triangles,
        mocked_big_items_triangles,
        mocked_small_items_elevation_handler,
        mocked_big_items_elevation_handler,
        mocker,
    ):
        (
            mocked_generate_small_items,
            fake_small_items_triangles,
        ) = mocked_small_items_triangles
        mocked_generate_big_items, fake_big_items_triangles = mocked_big_items_triangles

        fake_manual_surroundings_triangles = [mocker.MagicMock()]
        mocked_manual_surroundings = mocker.patch.object(
            self.instance_cls,
            "_generate_manual_surroundings_triangles",
            return_value=iter(fake_manual_surroundings_triangles),
        )

        site_id = 1000
        region = REGION.CH
        location = Point(0, 0)
        surrounding_handler = self.get_instance(
            site_id=site_id, region=region, location=location
        )

        triangles = list(surrounding_handler._generate_items_triangles())

        assert (
            triangles
            == fake_small_items_triangles
            + fake_big_items_triangles
            + fake_manual_surroundings_triangles
        )
        mocked_generate_small_items.assert_called_once_with(
            region=region,
            bounding_box=surrounding_handler._small_items_bbox,
            elevation_handler=mocked_small_items_elevation_handler,
        )
        mocked_generate_big_items.assert_called_once_with(
            region=region,
            bounding_box=surrounding_handler._big_items_bbox,
            elevation_handler=mocked_big_items_elevation_handler,
        )
        mocked_manual_surroundings.assert_called_once_with()

    def test_exclusion_area_by_surrounding_type(self, mocker):
        import surroundings.v2.surrounding_handler

        site_id = 1000
        region = REGION.CH
        building_footprints = [box(0, 0, 1, 1), box(2, 2, 3, 3)]

        manual_exclusion_footprint = box(0, 0, 2, 1)

        fake_manual_exclusion_handler = mocker.MagicMock()
        fake_manual_exclusion_handler.get_footprint.return_value = (
            manual_exclusion_footprint
        )

        mocked_manual_exclusion_handler = mocker.patch.object(
            surroundings.v2.surrounding_handler,
            "ManualExclusionSurroundingHandler",
            return_value=fake_manual_exclusion_handler,
        )

        surrounding_handler = self.get_instance(
            site_id=site_id, region=region, building_footprints=building_footprints
        )

        building_footprints_union = unary_union(building_footprints)
        assert surrounding_handler._exclusion_area_by_surrounding_type == {
            surrounding_type: building_footprints_union.buffer(
                SAFETY_BUFFER_BY_SURROUNDING_TYPE.get(
                    surrounding_type, DEFAULT_SAFETY_BUFFER
                ),
                join_style=JOIN_STYLE.mitre,
                cap_style=CAP_STYLE.square,
            ).union(manual_exclusion_footprint)
            for surrounding_type in SurroundingType
        }
        fake_manual_exclusion_handler.get_footprint.assert_called_once_with()
        mocked_manual_exclusion_handler.assert_called_once_with(
            site_id=site_id,
            region=region,
        )


class TestSwissTopoSurroundingHandler(_TestSurroundingHandler):
    instance_cls = SwissTopoSurroundingHandler


class TestOSMSurroundingHandler(_TestSurroundingHandler):
    instance_cls = OSMSurroundingHandler


class TestSwissTopoSlamSurroundingHandler(_TestSlamSurroundingHandler):
    instance_cls = SwissTopoSlamSurroundingHandler


class TestOSMSlamSurroundingHandler(_TestSlamSurroundingHandler):
    instance_cls = OSMSlamSurroundingHandler

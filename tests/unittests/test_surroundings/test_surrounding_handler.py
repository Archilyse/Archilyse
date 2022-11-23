import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import pytest
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, box, shape

from common_utils.constants import (
    REGION,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
    SurroundingType,
)
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.constants import BOUNDING_BOX_EXTENSION_SAMPLE
from surroundings.manual_surroundings import (
    ManualBuildingSurroundingHandler,
    ManualExclusionSurroundingHandler,
)
from surroundings.surrounding_handler import (
    ManualSurroundingsHandler,
    OSMSurroundingHandler,
    SurroundingStorageHandler,
    SwissTopoSurroundingHandler,
    generate_view_surroundings,
)
from surroundings.swisstopo import SwissTopoForestSurroundingHandler
from surroundings.v2.surrounding_handler import OSMSlamSurroundingHandler
from surroundings.v2.surrounding_handler import (
    OSMSurroundingHandler as OSMPotentialSurroundingHandler,
)
from surroundings.v2.surrounding_handler import SwissTopoSlamSurroundingHandler
from surroundings.v2.surrounding_handler import (
    SwissTopoSurroundingHandler as SwissTopoPotentialSurroundingHandler,
)
from tests.utils import random_simulation_version


def test_write_and_read_triangle_to_from_surrounding_file():
    type_triangle_tuples = [
        (SurroundingType.LAKES, [(0.0, 0.0, 10), (1.0, 1.0, 10), (2.0, 2.0, 10)])
    ] * 2

    with NamedTemporaryFile() as f:
        SurroundingStorageHandler.dump(
            filepath=Path(f.name), triangles=type_triangle_tuples
        )

        triangles = list(SurroundingStorageHandler.load(filepath=Path(f.name)))

    assert triangles == type_triangle_tuples


def test_filter_invalid_intersected_polygon():
    entity = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[(0.0, 1.0), (0.0, 2.0), (0.0, 1.0), (0.0, 1.0)]],
        }
    }
    assert (
        SwissTopoForestSurroundingHandler(
            location=(Point(0, 0)), simulation_version=random_simulation_version()
        ).valid_geometry_intersected_without_z(geom=shape(entity["geometry"]))
        is None
    )


class TestManualSurroundingsHandler:
    dummy_exclusion_polygon = box(0, 0, 0.5, 0.5)
    dummy_surrounding_triangles = [
        (SurroundingType.LAKES, [(0, 0, 0), (1, 0, 0), (1, 1, 0)]),
        (SurroundingType.LAKES, [(0, 0, 0), (0, 1, 0), (1, 1, 0)]),
    ]
    expected_surrounding_triangles_ex_exclusion_polygon = [
        (
            SurroundingType.LAKES,
            [(0.5, 0.5, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0)],
        ),
        (
            SurroundingType.LAKES,
            [(1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.5, 0.5, 0.0)],
        ),
        (
            SurroundingType.LAKES,
            [(0.0, 1.0, 0.0), (0.0, 0.5, 0.0), (0.5, 0.5, 0.0)],
        ),
        (
            SurroundingType.LAKES,
            [(0.5, 0.5, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
        ),
    ]
    expected_manual_triangles_ex_buffered_layout_footprint = [
        (
            SurroundingType.LAKES,
            [(0.6, 0.6, 0.0), (0.6, 0.0, 0.0), (1.0, 0.0, 0.0)],
        ),
        (
            SurroundingType.LAKES,
            [(1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.6, 0.6, 0.0)],
        ),
        (
            SurroundingType.LAKES,
            [(0.0, 1.0, 0.0), (0.0, 0.6, 0.0), (0.6, 0.6, 0.0)],
        ),
        (
            SurroundingType.LAKES,
            [(0.6, 0.6, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
        ),
    ]

    @pytest.mark.parametrize(
        "exclusion_polygon, triangles_in, expected_triangles_out",
        [
            (
                dummy_exclusion_polygon,
                dummy_surrounding_triangles,
                expected_surrounding_triangles_ex_exclusion_polygon,
            ),
            (None, dummy_surrounding_triangles, dummy_surrounding_triangles),
        ],
    )
    def test_apply_exclusion_polygon(
        self, mocker, exclusion_polygon, triangles_in, expected_triangles_out
    ):
        import surroundings.surrounding_handler as surrounding_handler_module

        # Given
        fake_site_id = -999
        mocked_exclusion_handler = mocker.patch.object(
            surrounding_handler_module,
            ManualExclusionSurroundingHandler.__name__,
        )
        mocked_exclusion_footprint = mocked_exclusion_handler().get_footprint
        mocked_exclusion_footprint.return_value = exclusion_polygon

        # When
        triangles_out = list(
            ManualSurroundingsHandler._apply_exclusion_polygon(
                site_id=fake_site_id, region=REGION.LAT_LON, triangles=triangles_in
            )
        )

        # Then
        mocked_exclusion_handler.assert_called_with(
            site_id=fake_site_id,
            region=REGION.LAT_LON,
        )
        mocked_exclusion_footprint.assert_called_once()
        assert triangles_out == expected_triangles_out

    def test_generate_manual_surroundings(self, mocker):
        # Given
        mocked_get_building_triangles = mocker.patch.object(
            ManualBuildingSurroundingHandler,
            ManualBuildingSurroundingHandler.get_triangles.__name__,
            return_value=self.dummy_surrounding_triangles,
        )

        # When
        building_triangles_out = list(
            ManualSurroundingsHandler._generate_manual_surroundings(
                site_id=mocker.ANY,
                region=REGION.LAT_LON,
                layout_footprint=self.dummy_exclusion_polygon,
                elevation_handler=ZeroElevationHandler(
                    location=Point(0, 0),
                    region=REGION.LAT_LON,
                    simulation_version=mocker.ANY,
                ),
            )
        )

        # Then
        assert mocked_get_building_triangles.call_count == 1
        assert (
            building_triangles_out
            == self.expected_surrounding_triangles_ex_exclusion_polygon
        )

    def test_apply_manual_adjustments(self, mocker):
        fake_site_id = -999
        elevation_handler = ZeroElevationHandler(
            location=Point(0, 0), region=REGION.LAT_LON, simulation_version=mocker.ANY
        )
        mocked_apply_exclusion_polygon = mocker.patch.object(
            ManualSurroundingsHandler,
            ManualSurroundingsHandler._apply_exclusion_polygon.__name__,
            return_value=self.expected_surrounding_triangles_ex_exclusion_polygon,
        )
        mocked_generate_manual_surroundings = mocker.patch.object(
            ManualSurroundingsHandler,
            ManualSurroundingsHandler._generate_manual_surroundings.__name__,
            return_value=self.expected_manual_triangles_ex_buffered_layout_footprint,
        )

        triangles_out = list(
            ManualSurroundingsHandler.apply_manual_adjustments(
                site_id=mocker.ANY,
                region=REGION.LAT_LON,
                triangles=self.dummy_surrounding_triangles,
                building_footprints=[self.dummy_exclusion_polygon],
                elevation_handler=elevation_handler,
            )
        )

        assert triangles_out == (
            self.expected_surrounding_triangles_ex_exclusion_polygon
            + self.expected_manual_triangles_ex_buffered_layout_footprint
        )
        mocked_apply_exclusion_polygon.assert_called_once_with(
            site_id=fake_site_id,
            region=REGION.LAT_LON,
            triangles=self.dummy_surrounding_triangles,
        )
        mocked_generate_manual_surroundings.assert_called_once_with(
            site_id=fake_site_id,
            region=REGION.LAT_LON,
            layout_footprint=self.dummy_exclusion_polygon.buffer(
                distance=0.1,
                cap_style=CAP_STYLE.square,
                join_style=JOIN_STYLE.mitre,
            ),
            elevation_handler=elevation_handler,
        )


def test_upload_generates_correct_file_names(mocked_gcp_upload_file_to_bucket):
    triangles = [
        (
            SurroundingType.LAKES,
            [(0.6, 0.6, 0.0), (0.6, 0.0, 0.0), (1.0, 0.0, 0.0)],
        )
    ]
    SurroundingStorageHandler.upload(triangles=triangles, remote_path=Path("my_site"))
    with ZipFile(
        mocked_gcp_upload_file_to_bucket.call_args.kwargs["local_file_path"]
    ) as myzip:
        surroundings_file_member = myzip.namelist()[0]
        # if not a valid uuid this will raise an exception
        uuid.UUID(Path(surroundings_file_member).stem)


@pytest.mark.parametrize("sample", [True, False])
@pytest.mark.parametrize(
    "simulation_version",
    [SIMULATION_VERSION.EXPERIMENTAL, SIMULATION_VERSION.PH_2022_H1],
)
@pytest.mark.parametrize(
    "site_id, region, surroundings_source, expected_handler",
    [
        (None, REGION.CH, None, SwissTopoPotentialSurroundingHandler),
        (
            None,
            REGION.CH,
            SURROUNDING_SOURCES.SWISSTOPO,
            SwissTopoPotentialSurroundingHandler,
        ),
        (None, REGION.CH, SURROUNDING_SOURCES.OSM, OSMPotentialSurroundingHandler),
        (-999, REGION.CH, None, SwissTopoSlamSurroundingHandler),
        (
            -999,
            REGION.CH,
            SURROUNDING_SOURCES.SWISSTOPO,
            SwissTopoSlamSurroundingHandler,
        ),
        (-999, REGION.CH, SURROUNDING_SOURCES.OSM, OSMSlamSurroundingHandler),
        *[
            (
                site_id,
                "ANY OTHER REGION",
                surrounding_source,
                OSMPotentialSurroundingHandler
                if site_id is None
                else OSMSlamSurroundingHandler,
            )
            for site_id in [None, -999]
            for surrounding_source in [SURROUNDING_SOURCES.OSM, None]
        ],
    ],
)
def test_generate_view_surroundings_ph_2022_h1(
    site_id,
    sample,
    simulation_version,
    region,
    surroundings_source,
    expected_handler,
    mocker,
):
    import surroundings.v2.surrounding_handler

    fake_view_surroundings = [mocker.MagicMock()]
    fake_surrounding_handler = mocker.MagicMock()
    fake_surrounding_handler.generate_view_surroundings.return_value = iter(
        fake_view_surroundings
    )

    mocked_surrounding_handler = mocker.patch.object(
        surroundings.v2.surrounding_handler,
        expected_handler.__name__,
        return_value=fake_surrounding_handler,
    )

    fake_location = Point(0, 0)
    fake_building_footprints = [box(0, 0, 1, 1)]

    view_surroundings = list(
        generate_view_surroundings(
            site_id=site_id,
            region=region,
            location=fake_location,
            building_footprints=fake_building_footprints,
            simulation_version=simulation_version,
            surroundings_source=surroundings_source,
            sample=sample,
        )
    )

    assert view_surroundings == fake_view_surroundings
    mocked_surrounding_handler.assert_called_once_with(
        region=region,
        location=fake_location,
        building_footprints=fake_building_footprints,
        sample=sample,
        **({"site_id": site_id} if site_id else {})
    )


@pytest.mark.parametrize("sample", [True, False])
@pytest.mark.parametrize("site_id", [-999, None])
@pytest.mark.parametrize("simulation_version", [SIMULATION_VERSION.PH_01_2021])
@pytest.mark.parametrize(
    "region, surroundings_source, expected_handler",
    [
        (REGION.CH, None, SwissTopoSurroundingHandler),
        (REGION.CH, SURROUNDING_SOURCES.SWISSTOPO, SwissTopoSurroundingHandler),
        (REGION.CH, SURROUNDING_SOURCES.OSM, OSMSurroundingHandler),
        *[
            (region, surrounding_source, OSMSurroundingHandler)
            for region in REGION
            if region != REGION.CH
            for surrounding_source in [SURROUNDING_SOURCES.OSM, None]
        ],
    ],
)
def test_generate_view_surroundings_ph_01_2021(
    site_id,
    sample,
    simulation_version,
    region,
    surroundings_source,
    expected_handler,
    mocker,
):
    fake_view_surroundings = [mocker.MagicMock()]
    mocked_generate_view_surroundings = mocker.patch.object(
        expected_handler,
        "generate_view_surroundings",
        return_value=iter(fake_view_surroundings),
    )

    fake_location = Point(0, 0)
    fake_building_footprints = [box(0, 0, 1, 1), box(1, 1, 2, 2)]

    view_surroundings = list(
        generate_view_surroundings(
            site_id=site_id,
            region=region,
            location=fake_location,
            building_footprints=fake_building_footprints,
            simulation_version=simulation_version,
            surroundings_source=surroundings_source,
            sample=sample,
        )
    )

    assert view_surroundings == fake_view_surroundings
    mocked_generate_view_surroundings.assert_called_once_with(
        site_id=site_id,
        region=region,
        location=fake_location,
        simulation_version=simulation_version,
        building_footprints=fake_building_footprints,
        bounding_box_extension=BOUNDING_BOX_EXTENSION_SAMPLE if sample else None,
        include_mountains=not sample,
    )

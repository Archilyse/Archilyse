import fiona
import pytest
from deepdiff import DeepDiff
from shapely.geometry import LineString, Point, mapping

import surroundings.eu_noise.noise_source_geometry_provider
from common_utils.constants import NOISE_SOURCE_TYPE, REGION
from surroundings.eu_noise import EUNoiseSourceGeometryProvider


@pytest.fixture
def mocked_shape_files(mocker):
    def _internal(noise_source_geometries):
        mocker.patch.object(
            surroundings.eu_noise.noise_source_geometry_provider,
            "download_files_if_not_exists",
            return_value=["fake-file"],
        )
        mocker.patch.object(fiona, "open").return_value.__enter__.return_value = [
            {
                "geometry": mapping(noise_source_geometry),
            }
            for noise_source_geometry in noise_source_geometries
        ]

    return _internal


class TestEUNoiseSourceGeometryProvider:
    @pytest.mark.parametrize(
        "noise_type",
        [NOISE_SOURCE_TYPE.TRAFFIC, NOISE_SOURCE_TYPE.TRAIN],
    )
    def test_get_source_geometries(self, noise_type, mocked_shape_files):
        bounding_box_extension = 500
        noise_source_geom_within_bbox = LineString([(0, 0), (1, 1)])
        noise_source_geom_partially_within_bbox = LineString([(0, 0), (1000, 1000)])
        noise_source_geom_outside_bbox = LineString([(1000, 1000), (2000, 2000)])

        mocked_shape_files(
            noise_source_geometries=[
                noise_source_geom_within_bbox,
                noise_source_geom_outside_bbox,
                noise_source_geom_partially_within_bbox,
            ]
        )

        source_geometries = EUNoiseSourceGeometryProvider(
            region=REGION.EUROPE,  # just to avoid projections
            location=Point(0, 0),
            bounding_box_extension=bounding_box_extension,
        ).get_source_geometries(noise_source_type=noise_type)

        assert list(source_geometries) == [
            noise_source_geom_within_bbox,
            LineString([(0, 0), (500, 500)]),
        ]

    def test_get_source_geometries_projects_region_crs_to_dataset_crs(
        self, mocked_shape_files
    ):
        # GIVEN
        location_hamburg_crs = Point(
            -4953645.793711991, -3137629.025380387
        )  # resolves to 0.0, 0.0 in REGION.EUROPE crs
        noise_source_geom_europe_crs = LineString([(0, 0), (1, 1)])
        bounding_box_extension = 500

        mocked_shape_files(noise_source_geometries=[noise_source_geom_europe_crs])
        expected_source_geometry_hamburg_crs = LineString(
            [
                (-4953645.793711991, -3137629.025380387),
                (-4953644.261153789, -3137627.933570106),
            ]
        )

        # WHEN initializing with Hamburg region and location
        noise_location_provider = EUNoiseSourceGeometryProvider(
            region=REGION.DE_HAMBURG,
            location=location_hamburg_crs,
            bounding_box_extension=bounding_box_extension,
        )
        # THEN the returned source geometries are projected to DE_HAMBURG crs
        source_geometries = list(
            noise_location_provider.get_source_geometries(
                noise_source_type=NOISE_SOURCE_TYPE.TRAIN
            )
        )
        assert not DeepDiff(
            expected_source_geometry_hamburg_crs.coords[:],
            source_geometries[0].coords[:],
            significant_digits=3,
        )

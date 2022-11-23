import numpy as np
import pytest
from shapely.geometry import LineString, Polygon

from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.v2.geometry import Geometry
from surroundings.v2.grounds import ElevationHandler
from surroundings.v2.swisstopo.constants import SWISSTOPO_BRIDGE_TYPES
from surroundings.v2.swisstopo.geometry_transformer import StreetAndRailwayTransformer
from tests.surroundings_utils import create_raster_window


class _TestStreetsAndRailwayTransformer:
    instance_cls = StreetAndRailwayTransformer

    def get_instance(self, elevation_handler=None, ground_offset=None):
        return self.instance_cls(
            elevation_handler=elevation_handler, ground_offset=ground_offset
        )

    @pytest.mark.parametrize(
        "properties, expected_transformed",
        [
            (
                # Bridges use the existing z values / are NOT projected over the ground
                {
                    "KUNSTBAUTE": bridge_type,
                },
                [
                    [
                        (-3.0, 0.0, 1.0),
                        (3.0, 0.0, 1.0),
                        (3.0, 1.0, 1.0),
                        (-3.0, 1.0, 1.0),
                        (-3.0, 0.0, 1.0),
                    ]
                ],
            )
            for bridge_type in SWISSTOPO_BRIDGE_TYPES
        ]
        + [
            (
                # Everything else is projected over the ground
                {
                    "KUNSTBAUTE": "FAKE-WILL-PROJECT-TO-GROUND",
                },
                [
                    [
                        (0.0, 0.0, -0.80),
                        (-3.0, 0.0, -0.80),
                        (-3.0, 1.0, -0.80),
                        (1.0, 1.0, -0.80),
                        (0.0, 0.0, -0.80),
                    ],
                    [
                        (1.0, 1.0, -0.80),
                        (3.0, 1.0, -0.80),
                        (3.0, 0.0, -0.80),
                        (0.0, 0.0, -0.80),
                        (1.0, 1.0, -0.80),
                    ],
                ],
            )
        ],
    )
    def test_transform_geometry(self, properties, expected_transformed, mocker):
        mocker.patch.object(self.instance_cls, "get_width", return_value=6.0)
        mocker.patch.object(
            self.instance_cls,
            "get_extension_type",
            return_value=LINESTRING_EXTENSION.SYMMETRIC,
        )

        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                data=np.full((1, 2, 2), -1.0),
                bounds=(-20, -20, 20, 20),
            )
        )

        instance = self.get_instance(
            elevation_handler=elevation_handler, ground_offset=0.2
        )
        transformed = list(
            instance.transform_geometry(
                Geometry(geom=LineString([(0, 0, 1), (0, 1, 1)]), properties=properties)
            )
        )
        assert len(transformed) == len(expected_transformed)
        assert all(
            actual.equals(expected)
            for actual, expected in zip(transformed, map(Polygon, expected_transformed))
        )

from pathlib import Path
from tempfile import TemporaryDirectory

import fiona
import pytest
from deepdiff import DeepDiff
from shapely.geometry import MultiPolygon, box

from common_utils.constants import SIMULATION_TYPE
from handlers.simulations.potential_tile_exporter import (
    SIMULATION_TYPE_SCHEMA,
    PotentialEntityProvider,
    PotentialTileExporter,
)
from tests.constants import SUN_ENTITY, VIEW_ENTITY


class TestPotentialTileExporter:
    @pytest.mark.parametrize(
        "simulation_type, bottom, left, expected_filename",
        [
            (SIMULATION_TYPE.SUN, 46.99, 8, "sun_N04699_E00800.fgb"),
            (SIMULATION_TYPE.SUN, 46.999, 8, "sun_N04700_E00800.fgb"),
            (SIMULATION_TYPE.SUN, 47, 8, "sun_N04700_E00800.fgb"),
            (SIMULATION_TYPE.VIEW, 47, 8, "view_N04700_E00800.fgb"),
            (SIMULATION_TYPE.VIEW, 0, 0, "view_N00000_E00000.fgb"),
            (SIMULATION_TYPE.VIEW, -1, -1, "view_S00100_W00100.fgb"),
        ],
    )
    def test_get_dump_filename(self, simulation_type, bottom, left, expected_filename):
        assert (
            PotentialTileExporter._get_dump_filename(
                simulation_type=simulation_type, bottom=bottom, left=left
            )
            == expected_filename
        )

    @pytest.mark.parametrize(
        "polygon, expected_tile_bounds",
        [
            (
                box(0, 0, 0.01, 0.01),
                [(0.00, 0.00, 0.01, 0.01)],
            ),
            (
                box(0, 0, 0.01, 0.02),
                [
                    (0.00, 0.00, 0.01, 0.01),
                    (0.00, 0.01, 0.01, 0.02),
                ],
            ),
            (
                box(0.001, 0.001, 0.005, 0.005),
                [(0.00, 0.00, 0.01, 0.01)],
            ),
            (
                box(-0.001, 0.0, 0.005, 0.005),
                [(-0.01, 0.00, 0.00, 0.01), (0.00, 0.00, 0.01, 0.01)],
            ),
        ],
    )
    def test_get_tile_bounds(self, polygon, expected_tile_bounds):
        tile_bounds = list(PotentialTileExporter.get_tile_bounds(polygon=polygon))
        assert tile_bounds == expected_tile_bounds

    @pytest.mark.parametrize(
        "dump_shape, expected_tile_shape",
        [
            (box(0, 0, 0.5, 0.5), MultiPolygon([box(0, 0, 0.5, 0.5)])),
            (box(-0.5, -0.5, 0.5, 0.5), MultiPolygon([box(0, 0, 0.5, 0.5)])),
            (
                MultiPolygon(
                    [
                        box(-0.5, -0.5, 0.5, 0.5),
                        box(-0.5, 0.6, 0.5, 1.0),
                    ]
                ),
                MultiPolygon(
                    [
                        box(0, 0, 0.5, 0.5),
                        box(0, 0.6, 0.5, 1.0),
                    ]
                ),
            ),
            (
                MultiPolygon(
                    [
                        box(-0.5, -0.5, 0.5, 0.5),
                        box(-0.5, 0.6, 0, 1.0),
                    ]
                ),
                MultiPolygon([box(0, 0, 0.5, 0.5)]),
            ),
        ],
    )
    def test_get_tile_shape(self, dump_shape, expected_tile_shape):
        tile_shape = PotentialTileExporter._get_tile_shape(
            dump_shape=dump_shape, tile_bounds=(0.0, 0.0, 1.0, 1.0)
        )
        assert tile_shape.equals(expected_tile_shape)

    @pytest.mark.parametrize(
        "filename, schema, entities",
        [
            (
                "view_file.fgb",
                SIMULATION_TYPE_SCHEMA[SIMULATION_TYPE.VIEW],
                [VIEW_ENTITY],
            ),
            ("sun_file.fgb", SIMULATION_TYPE_SCHEMA[SIMULATION_TYPE.SUN], [SUN_ENTITY]),
        ],
    )
    def test_dump_to_shapefile(self, filename, schema, entities):
        with TemporaryDirectory() as temp_dir:
            filename = Path(temp_dir).joinpath(filename)
            PotentialTileExporter._dump_to_shapefile(
                filename=filename, schema=schema, entities=iter(entities)
            )
            with fiona.open(filename) as shp_file:
                assert shp_file.schema == schema
                assert shp_file.crs == {"init": "epsg:4326"}
                assert not DeepDiff(
                    entities,
                    list(shp_file),
                    exclude_paths=["root[0]['id']", "root[0]['type']"],
                )

    def test_dump_to_vector_tile(self, mocker):
        fake_dir = Path("some")
        entities_by_type = {
            SIMULATION_TYPE.SUN: [SUN_ENTITY],
            SIMULATION_TYPE.VIEW: [VIEW_ENTITY],
        }
        file_by_type = {
            SIMULATION_TYPE.SUN: "sun_N00000_E00000.fgb",
            SIMULATION_TYPE.VIEW: "view_N00000_E00000.fgb",
        }

        mocked_dump_to_shapefile = mocker.patch.object(
            PotentialTileExporter, PotentialTileExporter._dump_to_shapefile.__name__
        )
        mocker.patch.object(
            PotentialTileExporter,
            PotentialTileExporter._get_filtered_entities.__name__,
            side_effect=lambda simulation_type, tile_shape, tile_bounds: entities_by_type[
                simulation_type
            ],
        )

        PotentialTileExporter.dump_to_vector_tile(
            directory=fake_dir,
            tile_bounds=(0.00, 0.00, 0.01, 0.01),
            dump_shape=box(0.00, 0.00, 0.01, 0.01),
        )

        assert mocked_dump_to_shapefile.call_args_list == [
            mocker.call(
                filename=fake_dir.joinpath(file_by_type[sim_type]),
                schema=SIMULATION_TYPE_SCHEMA[sim_type],
                entities=entities_by_type[sim_type],
            )
            for sim_type in SIMULATION_TYPE
        ]


class TestPotentialEntityProvider:
    @pytest.mark.parametrize("simulation_type", list(SIMULATION_TYPE))
    def test_make_entities(
        self, simulation_type, potential_sun_results, potential_view_results
    ):
        result_by_type = {
            SIMULATION_TYPE.SUN: potential_sun_results,
            SIMULATION_TYPE.VIEW: potential_view_results,
        }
        entities_by_type = {
            SIMULATION_TYPE.SUN: [SUN_ENTITY],
            SIMULATION_TYPE.VIEW: [VIEW_ENTITY],
        }

        simulation_info = {
            "type": simulation_type.value,
            "building_footprint": box(0, 0, 1, 1).wkt,
            "floor_number": 0,
            "result": result_by_type[simulation_type],
        }
        entities = list(
            PotentialEntityProvider.make_entities(simulation_info=simulation_info)
        )
        assert entities == entities_by_type[simulation_type]

import logging
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import List

from tqdm.contrib.concurrent import process_map

from common_utils.constants import ADMIN_SIM_STATUS, RESULT_VECTORS, SIMULATION_VERSION
from common_utils.logger import logger
from handlers.db import SiteDBHandler
from handlers.ph_vector.ph2022 import (
    NeufertAreaVectorSchema,
    NeufertResultVectorHandler,
    PHResultVectorCSVWriter,
)
from handlers.ph_vector.ph2022.area_vector_schema import NeufertGeometryVectorSchema

logger.setLevel(logging.WARNING)


def _generate_neufert_site_vector(client_id: int, site_id: int, vector_dir: Path):
    directory = vector_dir.joinpath(str(client_id)).joinpath(str(site_id))
    if directory.exists():
        return PHResultVectorCSVWriter.read_from_csv(
            result_vector_type=RESULT_VECTORS.NEUFERT_AREA_SIMULATIONS,
            directory=directory,
            schema=NeufertAreaVectorSchema,
        )

    try:
        vectors = NeufertResultVectorHandler.generate_vectors(
            site_id=site_id, representative_units_only=False
        )
    except Exception as e:
        logger.warning(f"Failed to generate vector for site {site_id}: {e}")
        return

    directory.mkdir(parents=True, exist_ok=True)
    PHResultVectorCSVWriter.write_to_csv(
        vectors=vectors, directory=directory, schema=NeufertAreaVectorSchema
    )
    return vectors[RESULT_VECTORS.NEUFERT_AREA_SIMULATIONS]


def _generate_neufert_site_geometry_vector(
    client_id: int, site_id: int, geometry_dir: Path
):
    directory = geometry_dir.joinpath(str(client_id)).joinpath(str(site_id))
    if directory.exists():
        return PHResultVectorCSVWriter.read_from_csv(
            result_vector_type=RESULT_VECTORS.NEUFERT_UNIT_GEOMETRY,
            directory=directory,
            schema=NeufertGeometryVectorSchema,
        )

    try:
        vectors = NeufertResultVectorHandler.generate_geometry_vectors(
            site_id=site_id, representative_units_only=False
        )
    except Exception as e:
        logger.warning(f"Failed to generate vector for site {site_id}: {e}")
        return

    directory.mkdir(parents=True, exist_ok=True)
    PHResultVectorCSVWriter.write_to_csv(
        vectors=vectors, directory=directory, schema=NeufertGeometryVectorSchema
    )
    return vectors[RESULT_VECTORS.NEUFERT_UNIT_GEOMETRY]


class VectorGenerator:
    MAX_WORKERS = 8

    def __init__(
        self,
        client_ids: List[int],
        vector_dir: Path,
    ):
        self.client_ids = client_ids
        self.vector_dir = vector_dir

        self.simulation_vector_dir = vector_dir.joinpath("simulations")
        self.simulation_vector_dir.mkdir(parents=True, exist_ok=True)

        self.geometry_vector_dir = vector_dir.joinpath("geometries")
        self.geometry_vector_dir.mkdir(parents=True, exist_ok=True)

    @cached_property
    def site_infos(self):
        return list(
            SiteDBHandler.find_in(
                client_id=self.client_ids,
                full_slam_results=[ADMIN_SIM_STATUS.SUCCESS],
                simulation_version=[SIMULATION_VERSION.PH_2022_H1.value],
                output_columns=["client_id", "id", "client_site_id"],
            )
        )

    def generate_vectors(self):
        vectors = chain(
            *process_map(
                _generate_neufert_site_vector,
                [site["client_id"] for site in self.site_infos],
                [site["id"] for site in self.site_infos],
                [self.simulation_vector_dir for _ in self.site_infos],
                max_workers=self.MAX_WORKERS,
            )
        )

        PHResultVectorCSVWriter.write_to_csv(
            vectors={RESULT_VECTORS.NEUFERT_AREA_SIMULATIONS: vectors},
            directory=self.vector_dir,
            schema=NeufertAreaVectorSchema,
        )

    def generate_geometries(self):
        vectors = chain(
            *process_map(
                _generate_neufert_site_geometry_vector,
                [site["client_id"] for site in self.site_infos],
                [site["id"] for site in self.site_infos],
                [self.geometry_vector_dir for _ in self.site_infos],
                max_workers=self.MAX_WORKERS,
            )
        )

        PHResultVectorCSVWriter.write_to_csv(
            vectors={RESULT_VECTORS.NEUFERT_UNIT_GEOMETRY: vectors},
            directory=self.vector_dir,
            schema=NeufertGeometryVectorSchema,
        )


if __name__ == "__main__":
    DATA_DIR = Path().home().joinpath("projects/datastory/data/2022-09-19")
    vector_dir = DATA_DIR.joinpath("vectors")
    generator = VectorGenerator(
        client_ids={1, 145, 163, 158, 152, 65}, vector_dir=vector_dir
    )
    generator.generate_geometries()
    generator.generate_vectors()

from typing import Dict, List

from common_utils.constants import RESULT_VECTORS
from handlers.ph_vector.ph2022 import (
    AreaVector,
    NeufertAreaVector,
    NeufertGeometryVector,
)


class PH2022ResultVectorHandler:
    @staticmethod
    def generate_vectors(
        site_id: int, representative_units_only: bool
    ) -> Dict[RESULT_VECTORS, List[Dict]]:
        return {
            RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY: AreaVector(
                site_id=site_id
            ).get_vector(representative_units_only=representative_units_only),
        }


class NeufertResultVectorHandler:
    @staticmethod
    def generate_vectors(
        site_id: int, representative_units_only: bool, anonymized: bool = True
    ) -> Dict[RESULT_VECTORS, List[Dict]]:
        return {
            RESULT_VECTORS.NEUFERT_AREA_SIMULATIONS: NeufertAreaVector(
                site_id=site_id
            ).get_vector(
                representative_units_only=representative_units_only,
                anonymized=anonymized,
            ),
        }

    @staticmethod
    def generate_geometry_vectors(
        site_id: int, representative_units_only: bool, anonymized: bool = True
    ) -> Dict[RESULT_VECTORS, List[Dict]]:
        return {
            RESULT_VECTORS.NEUFERT_UNIT_GEOMETRY: NeufertGeometryVector(
                site_id=site_id
            ).get_vector(
                representative_units_only=representative_units_only,
                anonymized=anonymized,
            ),
        }

from typing import Any, Dict, List, Optional, Tuple, Union

import pytest
from deepdiff import DeepDiff
from shapely.geometry import Polygon, box

from brooks.classifications import CLASSIFICATIONS, UnifiedClassificationScheme
from brooks.models import SimArea
from brooks.types import AreaType
from common_utils.constants import TASK_TYPE
from handlers.ph_vector import PHResultVectorHandler
from tests.constants import CLIENT_ID_1


class TestPHResultVectorHandler:
    @pytest.fixture
    def mock_dependencies(self, mocker):
        def _internal(
            unit_area_stats: Optional[Dict[int, Dict[int, Any]]] = None,
            unit_areas: Optional[Dict[int, Dict[int, SimArea]]] = None,
            unit_client_ids: Optional[List[Dict[str, Union[int, str]]]] = None,
            basic_features: Optional[List[Dict[str, Any]]] = None,
            simulation_categories: Optional[List[Tuple[str, TASK_TYPE, List]]] = None,
        ):
            from handlers.ph_vector.ph_result_vector_handler import (
                StatsHandler,
                UnitDBHandler,
            )

            mocker.patch.object(
                StatsHandler,
                "get_area_stats",
                return_value=unit_area_stats or {},
            )
            mocker.patch.object(
                PHResultVectorHandler,
                "unit_areas",
                mocker.PropertyMock(return_value=unit_areas or {}),
            )
            mocker.patch.object(
                UnitDBHandler, "find", return_value=unit_client_ids or []
            )
            mocker.patch.object(
                PHResultVectorHandler,
                "_get_simulation_categories",
                return_value=simulation_categories or [],
            )
            mocker.patch.object(
                PHResultVectorHandler,
                "basic_features",
                mocker.PropertyMock(return_value=basic_features or {}),
            )

        return _internal

    @pytest.mark.parametrize(
        "interior_only",
        [True, False],
    )
    @pytest.mark.parametrize("area_type", [a for a in AreaType])
    def test_get_unit_area_stats_interior_only(
        self, mock_dependencies, interior_only, area_type
    ):
        # Given
        classification_scheme = CLASSIFICATIONS.UNIFIED
        mock_dependencies(
            unit_area_stats={
                1: {1: "dummy-stats-1"},
                2: {2: "dummy-stats-2"},
            },
            unit_areas={
                1: {1: SimArea(area_type=area_type, footprint=Polygon())},
                2: {2: SimArea(area_type=area_type, footprint=Polygon())},
            },
        )
        # When
        result = list(
            PHResultVectorHandler(site_id=-999)._get_unit_area_stats(
                interior_only=interior_only, task_type=None, dimensions=None
            )
        )
        # Then
        if interior_only and area_type in classification_scheme.value().BALCONY_AREAS:
            assert not result
        else:
            assert result == [(1, 1, "dummy-stats-1"), (2, 2, "dummy-stats-2")]

    @pytest.mark.parametrize("area_type", [a for a in AreaType])
    def test_generate_area_vector_excludes_non_ph_areas(
        self, mock_dependencies, area_type
    ):
        mock_dependencies(
            unit_area_stats={
                1: {
                    1: {
                        "dummy-dimension": {
                            "min": 0,
                            "max": 1,
                            "stddev": 0.5,
                            "mean": 0.5,
                            "count": 2,
                        }
                    }
                }
            },
            unit_areas={
                1: {1: SimArea(area_type=area_type, footprint=box(0, 0, 1, 1))},
            },
            simulation_categories=[
                ("dummy-prefix", TASK_TYPE.VIEW_SUN, ["dummy-dimension"])
            ],
            unit_client_ids=[{"id": 1, "client_id": "dummy-apartment-id"}],
        )
        room_vector_names = UnifiedClassificationScheme().ROOM_VECTOR_NAMING

        result = PHResultVectorHandler(site_id=-999)._generate_area_vector(
            interior_only=False
        )
        if area_type not in room_vector_names:
            assert result == {"dummy-apartment-id": []}
        else:
            assert result == {
                "dummy-apartment-id": [
                    {
                        "AreaBasics.area_size": 1.0,
                        "AreaBasics.area_type": str(room_vector_names[area_type]),
                        "AreaShape.compactness": 0.7853981633974483,
                        "AreaShape.mean_walllengths": 1.0,
                        "AreaShape.std_walllengths": 0.0,
                        "area_index": 1,
                        "dummy-prefix.max.dummy-dimension": 1,
                        "dummy-prefix.mean.dummy-dimension": 0.5,
                        "dummy-prefix.min.dummy-dimension": 0,
                        "dummy-prefix.std.dummy-dimension": 0.5,
                    }
                ],
            }

    def test_generate_full_vector_with_balcony(
        self,
        expected_apartment_vector_with_balcony,
        expected_room_vector_with_balcony,
        expected_full_vector_with_balcony,
    ):
        assert not DeepDiff(
            expected_full_vector_with_balcony[CLIENT_ID_1],
            PHResultVectorHandler._generate_full_vector(
                area_vector=expected_room_vector_with_balcony[CLIENT_ID_1],
                apartment_vector=expected_apartment_vector_with_balcony[CLIENT_ID_1],
            ),
        )

    def test_generate_full_vector_no_balcony(
        self,
        expected_apartment_vector_no_balcony,
        expected_room_vector_no_balcony,
        expected_full_vector_no_balcony,
    ):
        assert not DeepDiff(
            expected_full_vector_no_balcony[CLIENT_ID_1],
            PHResultVectorHandler._generate_full_vector(
                area_vector=expected_room_vector_no_balcony[CLIENT_ID_1],
                apartment_vector=expected_apartment_vector_no_balcony[CLIENT_ID_1],
            ),
        )

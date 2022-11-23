from enum import Enum
from typing import Set

import pytest

from brooks.models import SimLayout
from brooks.types import AREA_TYPE_USAGE, AreaType, FeatureType


@pytest.mark.parametrize(
    "features,area_expected",
    [
        ({FeatureType.ELEVATOR}, AreaType.ELEVATOR),
        ({FeatureType.KITCHEN}, AreaType.NOT_DEFINED),
        ({FeatureType.TOILET}, AreaType.BATHROOM),
        ({FeatureType.TOILET}, AreaType.BATHROOM),
        ({FeatureType.BATHTUB}, AreaType.BATHROOM),
        ({FeatureType.SHOWER}, AreaType.BATHROOM),
        ({FeatureType.SINK}, AreaType.BATHROOM),
        ({FeatureType.SHAFT}, AreaType.SHAFT),
        ({FeatureType.STAIRS}, AreaType.STAIRCASE),
        ({}, AreaType.NOT_DEFINED),
    ],
)
def test_from_feature_types_to_area_types(features: Set[Enum], area_expected: Enum):
    area_type = SimLayout()._from_feature_types_to_area_types(feature_types=features)
    assert area_type == area_expected


@pytest.mark.parametrize(
    "feature, area_expected",
    [
        (
            FeatureType.STAIRS,
            AreaType.STAIRCASE,
        ),
        (FeatureType.STAIRS, AreaType.STAIRCASE),
        (FeatureType.SHAFT, AreaType.SHAFT),
        (FeatureType.SHAFT, AreaType.SHAFT),
    ],
)
def test_from_feature_types_to_area_types_shaft(feature, area_expected):
    area_type = SimLayout()._from_feature_types_to_area_types({feature})
    assert area_type == area_expected


@pytest.mark.parametrize("area_type", [area_type for area_type in AreaType])
def test_all_areas_are_part_of_area_types_usage(area_type):
    areas_to_ignore = {
        "HNF",
        "UUF11_1_UNBEARB__AUSSENFLAECHE",
        "UF_UMGEBUNGSFLAECHE",
        "NF",
        "NNF7_SONSTIGE_NUTZUNG",
        "HNF5_BILDUNG_UNTERRICHT_UND_KULTUR",
        "FF8_BETRIEBSTECHN__ANLAGEN",
        "BUF10_4_AUSSEN_PP_FAHRRAD",
        "VF9_VERKEHRSERSCHLIESSUNG",
        "AGF1_TERRASSEN_UND_BALKONE",
        "HNF3_PRODUKTION__HANDEL__M__ARB_",
        "NGF",
        "GGF_GEBAEUDEGRUNDFLAECHE",
        "GSF_GRUNDSTUECKSFLAECHE",
        "NOT_DEFINED",
        "UUF11_UNBEARB__UMGEBUNGSFL_",
        "BUF10_1_AUSSEN_PP_FAHRZEUG",
        "BUF10_VERSCHIEDENE_NUTZUNG",
        "VF",
        "AGF",
        "BUF10_3_AUSSEN_PP_MOTO",
        "BUF10_2_UEBERDACHTE_AUSSEN_PP_FAHRZEUG",
        "HNF6_HEILEN_UND_PFLEGEN",
        "MOTORCYCLE_PARKING",
        "UUF_UNBEARBEITETE_UMGEBUNGSFL_",
        "KF",
        "ANF",
        "HNF4_LAGERN__VERTEILEN_UND_VERKAUFEN",
        "BUF10_5_BEARB__AUSSENFLAECHE",
        "FF",
        "HNF1_WOHNEN_UND_AUFENTHALT",
        "NNF",
        "NC_NO_CLASSIFICATION",
        "GF",
        "HNF2_BUEROARBEIT",
        "BUF_BEARBEITETE_UMGEBUNGSFL_",
    }
    if area_type.name not in areas_to_ignore:
        assert area_type in AREA_TYPE_USAGE

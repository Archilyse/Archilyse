from typing import List

import pytest
from shapely.affinity import scale
from shapely.geometry import LineString, Polygon, box, shape

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from brooks.visualization.floorplans.layouts.assetmanager_layout_text import (
    BaseAssetManagerTextGenerator,
)
from brooks.visualization.floorplans.patches.door import (
    DoorOpeningDirection,
    DoorPatches,
)
from brooks.visualization.floorplans.patches.generators import (
    apply_area_name_logic,
    generate_room_texts,
)
from common_utils.constants import SUPPORTED_LANGUAGES


@pytest.mark.parametrize("language", [language for language in SUPPORTED_LANGUAGES])
def test_area_type_to_name_mapping(language):
    name_mapping = BaseAssetManagerTextGenerator(
        metadata=None, language=language
    ).area_type_to_name_mapping

    area_types = set(UnifiedClassificationScheme().leaf_area_types)
    area_types_hidden = {
        area_type for area_type in area_types if not name_mapping.get(area_type)
    }
    non_area_type_roomstamps = {
        a.name for a in set(name_mapping.keys()).difference(area_types)
    }

    assert area_types_hidden == {
        AreaType.SHAFT,
        AreaType.STAIRCASE,
        AreaType.MOTORCYCLE_PARKING,
    }
    assert non_area_type_roomstamps == {"LAUNDRY", "WC", "SHOWER"}


@pytest.mark.parametrize(
    "language,features,area_type,size,next_to_toilet,expected_name",
    [
        (
            SUPPORTED_LANGUAGES.DE,
            {SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SHOWER)},
            AreaType.BATHROOM,
            1,
            True,
            "Dusche",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.BATHTUB),
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SHOWER),
            },
            AreaType.BATHROOM,
            1,
            True,
            "Bad",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SINK),
            },
            AreaType.BATHROOM,
            1,
            True,
            "Bad",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.TOILET),
            },
            AreaType.BATHROOM,
            1,
            True,
            "WC",
        ),
        (
            SUPPORTED_LANGUAGES.EN,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SHOWER),
            },
            AreaType.BATHROOM,
            1,
            True,
            "Shower",
        ),
        (
            SUPPORTED_LANGUAGES.EN,
            set(),
            AreaType.BATHROOM,
            1,
            True,
            "Bath",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            set(),
            AreaType.ROOM,
            1,
            True,
            "Zimmer",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SINK),
            },
            AreaType.ROOM,
            1 / 3,
            True,
            "Zimmer",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SINK),
            },
            AreaType.STOREROOM,
            1 / 3,
            True,
            "WC",
        ),
        (
            SUPPORTED_LANGUAGES.EN,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SINK),
            },
            AreaType.STOREROOM,
            1 / 3,
            False,
            "Bath",
        ),
        (
            SUPPORTED_LANGUAGES.EN,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SINK),
            },
            AreaType.BATHROOM,
            1,
            True,
            "Bath",
        ),
        (
            SUPPORTED_LANGUAGES.EN,
            {
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SINK),
                SimFeature(footprint=box(0, 0, 1, 1), feature_type=FeatureType.SHOWER),
            },
            AreaType.BATHROOM,
            1,
            True,
            "Shower",
        ),
    ],
)
def test_apply_area_name_logic(
    language, features, area_type, size, next_to_toilet, expected_name
):
    name_mapping = BaseAssetManagerTextGenerator(
        metadata=None, language=language
    ).area_type_to_name_mapping

    area = SimArea(
        footprint=scale(geom=box(0, 0, 3, 3), xfact=size, yfact=size),
        area_type=area_type,
    )
    area.features = features

    assert (
        apply_area_name_logic(
            area=area,
            area_type_to_name_mapping=name_mapping,
            next_to_toilet=next_to_toilet,
        )
        == expected_name
    )


def test_spaces_with_door_to_toilet():
    feature = SimFeature(footprint=box(8, 8, 10, 10), feature_type=FeatureType.TOILET)
    area = SimArea(footprint=box(0, 0.2, 10, 10))
    area.features.add(feature)
    space = SimSpace(footprint=area.footprint)
    space.add_area(area=area)

    area2 = SimArea(footprint=box(0, -10, 10, -0.2))
    space2 = SimSpace(footprint=area2.footprint)
    space2.add_area(area=area2)

    area3 = SimArea(footprint=box(0, -18, 10, -10.4))
    space3 = SimSpace(footprint=area3.footprint)
    space3.add_area(area=area3)

    separator = SimSeparator(
        footprint=box(0, -0.2, 10, 0.2), separator_type=SeparatorType.WALL
    )
    opening = SimOpening(
        footprint=box(1, -0.2, 2, 0.2),
        height=(1, 2.5),
        separator=separator,
        opening_type=OpeningType.DOOR,
        separator_reference_line=get_center_line_from_rectangle(separator.footprint)[0],
    )
    separator.add_opening(opening=opening)

    separator2 = SimSeparator(
        footprint=box(0, -10.4, 10, -10), separator_type=SeparatorType.WALL
    )
    opening2 = SimOpening(
        footprint=box(1, -10.4, 2, -10),
        height=(1, 2.5),
        separator=separator2,
        opening_type=OpeningType.DOOR,
        separator_reference_line=get_center_line_from_rectangle(separator2.footprint)[
            0
        ],
    )
    separator2.add_opening(opening=opening2)

    layout = SimLayout(
        spaces={space, space2, space3}, separators={separator, separator2}
    )

    expected_spaces = layout.spaces_next_to_toilet_space()

    assert space.id not in expected_spaces
    assert space2.id in expected_spaces
    assert space3.id not in expected_spaces


def test_generate_room_texts_post_classification(mocker):
    from brooks.visualization.floorplans.patches import generators

    area = SimArea(
        footprint=box(0, 0, 2, 2),
        area_type=AreaType.CORRIDORS_AND_HALLS,
    )
    space = SimSpace(footprint=area.footprint)
    space.add_area(area)
    layout = SimLayout(spaces={space})
    mocker.patch.object(
        generators, "footprint_without_features", return_value=area.footprint
    )
    mocker.patch.object(
        SimLayout, "spaces_next_to_toilet_space", return_value={space.id}
    )

    room_texts = [
        room_text
        for room_text in generate_room_texts(
            layout=layout,
            area_type_to_name=None,
            axis=None,
            use_superscript_for_squaremeters=True,
        )
    ]
    assert len(room_texts) == 1
    assert room_texts[0][2] == "CORRIDORS_AND_HALLS\n4.0 m$^2$"


@pytest.mark.parametrize(
    "connecting_area_ids, unit_db_area_ids, expected_result",
    [(({1}, set(), 1)), ({1, 2}, {2}, 2), ({1, 2}, set(), None)],
)
def test_door_opening_direction(connecting_area_ids, unit_db_area_ids, expected_result):
    dummy_geometry = box(0, 0, 1, 1)
    areas = {
        SimArea(footprint=dummy_geometry, area_id=1, db_area_id=1),
        SimArea(footprint=dummy_geometry, area_id=2, db_area_id=2),
    }

    connecting_areas = [area for area in areas if area.id in connecting_area_ids]

    result = DoorPatches(
        door=dummy_geometry,
        connecting_areas=connecting_areas,
        public_area_ids=set(),
        unit_db_area_ids=unit_db_area_ids,
    )._space_door_should_open_into()

    assert getattr(result, "id", None) == expected_result


@pytest.fixture
def space_geometry() -> Polygon:
    return shape(
        {
            "type": "Polygon",
            "coordinates": (
                (
                    (4025.0730755931227, -3587.278081028462),
                    (4024.7398843809515, -3586.923114822939),
                    (4024.5677245157613, -3586.5295967861416),
                    (4024.5428901786977, -3586.1587614901837),
                    (4024.6245952028403, -3585.7133948667833),
                    (4024.904295363076, -3585.259541275919),
                    (4025.257469822883, -3584.927169162232),
                    (4025.675711590343, -3584.7917607903396),
                    (4026.3189411970047, -3584.8225577345665),
                    (4026.591034871017, -3584.946872759958),
                    (4026.586223818149, -3584.9528603963035),
                    (4026.9732243383355, -3585.263814478208),
                    (4027.2242499733156, -3585.6991438092987),
                    (4027.3462892946527, -3586.1585829171718),
                    (4027.245184957083, -3586.7069512286007),
                    (4027.257794506717, -3586.7092760897135),
                    (4027.0562842564186, -3587.0429636918607),
                    (4026.8134524926672, -3587.3027105960023),
                    (4025.1156550588553, -3587.305590335434),
                    (4025.0811515613586, -3587.2702060808806),
                    (4025.0730755931227, -3587.278081028462),
                ),
            ),
        }
    )


@pytest.fixture
def door_centerlines() -> List[LineString]:
    return [
        shape(
            {
                "type": "LineString",
                "coordinates": (
                    (4025.0334098034045, -3587.3167594885135),
                    (4024.3352697393802, -3586.600798280763),
                ),
            }
        ),
        shape(
            {
                "type": "LineString",
                "coordinates": (
                    (4025.126516542794, -3587.4122429266063),
                    (4025.8246566068183, -3588.128204134357),
                ),
            }
        ),
    ]


def test_empty_direction_intersections_doesnt_fail(
    mocker, space_geometry, door_centerlines
):
    """
    Somehow the algorithm which detects the space into the door should open works slightly different from the
    door centerline creation such that it can happen that they don't intersect which was the case here
    The fixtures are from plan 5519
    """
    placeholder_door = box(0, 0, 1, 1)
    mocker.patch.object(
        DoorPatches,
        "_space_door_should_open_into",
        return_value=SimSpace(footprint=space_geometry),
    )
    mocker.patch.object(
        DoorPatches, "_door_center_line_direction", side_effect=door_centerlines
    )
    door_patches = DoorPatches(
        door=placeholder_door,
        connecting_areas=[],
        public_area_ids=set(),
        unit_db_area_ids=set(),
    )
    assert door_patches.door_opening_direction is DoorOpeningDirection.UP

from collections import Counter
from pathlib import Path

import pytest
from PIL import Image
from shapely.geometry import MultiPolygon

from common_utils.exceptions import IfcEmptyStoreyException
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from ifc_reader.constants import (
    IFC_BUILDING,
    IFC_CURTAIN_WALL,
    IFC_DOOR,
    IFC_SPACE,
    IFC_STAIR,
    IFC_STOREY,
    IFC_WALL_STANDARD_CASE,
    IFC_WINDOW,
)
from ifc_reader.reader import IfcReader
from ifc_reader.types import Ifc2DEntity
from tests.utils import assert_image_phash


def test_storey_footprint(ifc_file_reader_sia_arc):
    storey_index = ifc_file_reader_sia_arc.storeys_by_building
    building_id = list(storey_index.keys())[0]
    storey_id = storey_index[building_id][0]
    footprint = IfcStoreyHandler(ifc_reader=ifc_file_reader_sia_arc).storey_footprint(
        storey_id=storey_id
    )
    assert footprint.area == pytest.approx(798.329, abs=10**-3)
    assert isinstance(footprint, MultiPolygon)
    assert footprint.bounds == (
        31.512116320941303,
        16.728661869526697,
        68.38384550827952,
        50.51720662516142,
    )


def test_get_storey_entities_by_ifc_type(ac20_fzk_haus_ifc_reader):
    annotations_by_ifc_type = IfcStoreyHandler(
        ifc_reader=ac20_fzk_haus_ifc_reader
    ).get_storey_entities_by_ifc_type(storey_id=479)
    counter = Counter()
    for ifc_type, list_of_annotations in annotations_by_ifc_type.items():
        counter[ifc_type] = len(list_of_annotations)
    assert counter == {
        IFC_SPACE: 6,
        IFC_STAIR: 1,
        IFC_WALL_STANDARD_CASE: 8,
        IFC_CURTAIN_WALL: 1,
        IFC_DOOR: 5,
        IFC_WINDOW: 9,
    }


@pytest.mark.parametrize(
    "floor_number, ifc_file_name, image_file",
    [
        (0, "AC20-FZK-Haus", "AC20-FZK-Haus-EG.png"),
        (1, "AC20-FZK-Haus", "AC20-FZK-Haus-1OG.png"),
        (0, "steiner_example", "steiner_example-2UG.png"),
        (3, "steiner_example", "steiner_example-EG.png"),
    ],
)
def test_create_storey_figure(
    fixtures_path,
    floor_number,
    image_file,
    ifc_file_name,
    ifc_file_reader_steiner_example,
    ac20_fzk_haus_ifc_reader,
):
    ifc_reader = {
        "steiner_example": ifc_file_reader_steiner_example,
        "AC20-FZK-Haus": ac20_fzk_haus_ifc_reader,
    }[ifc_file_name]
    storey_id = ifc_reader.wrapper.by_type(IFC_STOREY)[floor_number].id()
    building_id = ifc_reader.wrapper.by_type(IFC_BUILDING)[0].GlobalId
    storey_figure = IfcStoreyHandler(ifc_reader=ifc_reader).storey_figure(
        storey_id=storey_id,
        building_id=building_id,
    )
    new_image_content = Image.open(storey_figure)
    expected_image_file = fixtures_path.joinpath(f"images/{image_file}")

    assert_image_phash(
        expected_image_file=expected_image_file,
        new_image_content=new_image_content,
    )


def test_empty_storey_raises_exception(mocker):
    mocker.patch.object(
        IfcStoreyHandler, "get_storey_entities_by_ifc_type", return_value={}
    )
    with pytest.raises(IfcEmptyStoreyException) as e:
        IfcStoreyHandler(ifc_reader=None).storey_footprint(storey_id=1)
    assert str(e.value) == "ifc storey with id 1 doesn't contain any elements"


class TestPlanHeightsByAnnotationType:
    @staticmethod
    def test_get_relative_plan_heights_ac20_fzk_haus(ac20_fzk_haus_ifc_reader):
        storey_index = ac20_fzk_haus_ifc_reader.storeys_by_building
        building_id = list(storey_index.keys())[0]
        storey_id = storey_index[building_id][0]
        heights = IfcStoreyHandler(
            ifc_reader=ac20_fzk_haus_ifc_reader
        ).get_relative_plan_heights(storey_id=storey_id)
        assert heights == {
            "default_wall_height": 2.7,
            "default_door_height": 2.38,
            "default_window_upper_edge": 2.15,
            "default_window_lower_edge": 0.8,
            "default_ceiling_slab_height": 0.3,
        }

    @staticmethod
    def test_get_relative_plan_heights_difference_higher_floors_ac20_fzk_haus(
        ac20_fzk_haus_ifc_reader,
    ):
        storey_index = ac20_fzk_haus_ifc_reader.storeys_by_building
        building_id = list(storey_index.keys())[0]
        storey_id = storey_index[building_id][1]
        heights = IfcStoreyHandler(
            ifc_reader=ac20_fzk_haus_ifc_reader
        ).get_relative_plan_heights(storey_id=storey_id)

        assert heights == {
            "default_wall_height": 3.39,
            "default_door_height": 2.0,  # default value because there are no doors
            "default_window_upper_edge": 1.8,
            "default_window_lower_edge": 0.8,
            "default_ceiling_slab_height": 0.3,
        }

    @staticmethod
    def test_get_relative_plan_heights_underground(mocker):
        """
        ┌──────────────────────┐   10
        │                      │
        │                      │
        │                      │
        │       Window         │
        │  ┌──┐1               │
        ├──┼┼┼┼────────────────┤  Ground level
        │  └──┘-1              │
        │                      │
        │                      │
        │                      │
        │                      │
        └──────────────────────┘ -5
                   Wall
        """

        mocker.patch.object(
            IfcStoreyHandler,
            "get_storey_entities_by_ifc_type",
            return_value={
                IFC_WALL_STANDARD_CASE: [
                    Ifc2DEntity(
                        geometry=MultiPolygon(),
                        min_height=-5,
                        max_height=10.0,
                        ifc_type=IFC_WALL_STANDARD_CASE,
                    )
                ],
                IFC_WINDOW: [
                    Ifc2DEntity(
                        geometry=MultiPolygon(),
                        min_height=-1,
                        max_height=1,
                        ifc_type=IFC_WINDOW,
                    )
                ],
                IFC_DOOR: [
                    Ifc2DEntity(
                        geometry=MultiPolygon(),
                        min_height=-2,
                        max_height=2,
                        ifc_type=IFC_DOOR,
                    )
                ],
            },
        )
        heights = IfcStoreyHandler(
            ifc_reader=IfcReader(Path("will not load"))
        ).get_relative_plan_heights(storey_id=0)
        assert heights == {
            "default_wall_height": 15.0,
            "default_door_height": 4,  # Difference between minimum and maximum
            "default_window_upper_edge": 6,
            "default_window_lower_edge": 4,
            "default_ceiling_slab_height": 0.3,
        }

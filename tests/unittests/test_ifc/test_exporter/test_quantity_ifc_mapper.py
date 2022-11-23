import pytest

from dufresne import polygon
from handlers.ifc.types import IfcQuantityArea, IfcQuantityLength, IfcQuantityVolume


@pytest.fixture
def polygon_fake(mocker):
    return mocker.MagicMock(
        area=1.337,
        length=4.2,
    )


def test_property_ifc_mapper_add_area_quantities(mocker, ifc_file_dummy, polygon_fake):
    from handlers.ifc.exporter.generators import IfcRelationshipGenerator
    from handlers.ifc.exporter.mappers import QuantityIfcMapper

    add_quantities_to_object_mock = mocker.patch.object(
        IfcRelationshipGenerator, "add_quantities_to_object"
    )

    QuantityIfcMapper.add_area_quantities(
        ifc_file=ifc_file_dummy,
        ifc_space="IfcSpace_placeholder",
        polygon=polygon_fake,
        height=42,
    )

    assert add_quantities_to_object_mock.call_args_list == [
        mocker.call(
            ifc_file=ifc_file_dummy,
            ifc_entity="IfcSpace_placeholder",
            quantity_types=[
                IfcQuantityLength,
                IfcQuantityLength,
                IfcQuantityArea,
                IfcQuantityArea,
                IfcQuantityVolume,
            ],
            quantity_names=[
                "Height",
                "GrossPerimeter",
                "NetFloorArea",
                "GrossWallArea",
                "NetVolume",
            ],
            quantity_values=[
                42,
                polygon_fake.length,
                polygon_fake.area,
                polygon_fake.length * 42,
                polygon_fake.area * 42,
            ],
            quantity_descriptions=[
                "Total height (from base slab without flooring to ceiling without suspended ceiling) for this space (measured from top of slab below to bottom of slab above). To be provided only if the space has a constant height.",
                "Gross perimeter at the floor level of this space. It all sides of the space, including those parts of the perimeter that are created by virtual boundaries and openings (like doors).",
                "Sum of all usable floor areas covered by the space. It excludes the area covered by elements inside the space (columns, inner walls, built-in's etc.), slab openings, or other protruding elements. Varying heights are not taking into account (i.e. no reduction for areas under a minimum headroom).",
                "Sum of all wall (and other vertically bounding elements, like columns) areas bounded by the space. It includes the area covered by elements inside the wall area (doors, windows, other openings, etc.).",
                "Gross volume enclosed by the space, including the volume of construction elements inside the space.",
            ],
            quantity_set_name="Qto_SpaceBaseQuantities",
        )
    ]


def test_property_ifc_mapper_add_window_quantities(
    mocker, ifc_file_dummy, polygon_fake
):
    from handlers.ifc.exporter.generators import IfcRelationshipGenerator
    from handlers.ifc.exporter.mappers import QuantityIfcMapper

    add_quantities_to_object_mock = mocker.patch.object(
        IfcRelationshipGenerator, "add_quantities_to_object"
    )

    mocker.patch.object(
        polygon,
        "get_sides_as_lines_by_length",
        return_value=[mocker.MagicMock(length=i) for i in range(4)],
    )
    QuantityIfcMapper.add_window_quantities(
        ifc_file=ifc_file_dummy,
        ifc_window="IfcWindow_placeholder",
        polygon=polygon_fake,
        height=42,
    )

    assert add_quantities_to_object_mock.call_args_list == [
        mocker.call(
            ifc_file=ifc_file_dummy,
            ifc_entity="IfcWindow_placeholder",
            quantity_types=[
                IfcQuantityLength,
                IfcQuantityLength,
                IfcQuantityLength,
                IfcQuantityArea,
            ],
            quantity_names=["Width", "Height", "Perimeter", "Area"],
            quantity_values=[
                3,
                42,
                4.2,
                1.337,
            ],
            quantity_descriptions=[
                "Total outer width of the window lining. It should only be provided, if it is a rectangular window.",
                "Total outer heigth of the window lining. It should only be provided, if it is a rectangular window.",
                "Total perimeter of the outer lining of the window.",
                "Total area of the outer lining of the window.",
            ],
            quantity_set_name="Qto_WindowBaseQuantities",
        )
    ]


def test_property_ifc_mapper_add_door_quantities(mocker, ifc_file_dummy, polygon_fake):
    from handlers.ifc.exporter.generators import IfcRelationshipGenerator
    from handlers.ifc.exporter.mappers import QuantityIfcMapper

    add_quantities_to_object_mock = mocker.patch.object(
        IfcRelationshipGenerator, "add_quantities_to_object"
    )

    mocker.patch.object(
        polygon,
        "get_sides_as_lines_by_length",
        return_value=[mocker.MagicMock(length=i) for i in range(4)],
    )
    QuantityIfcMapper.add_door_quantities(
        ifc_file=ifc_file_dummy,
        ifc_door="IfcDoor_placeholder",
        polygon=polygon_fake,
        height=42,
    )

    assert add_quantities_to_object_mock.call_args_list == [
        mocker.call(
            ifc_file=ifc_file_dummy,
            ifc_entity="IfcDoor_placeholder",
            quantity_types=[
                IfcQuantityLength,
                IfcQuantityLength,
                IfcQuantityLength,
                IfcQuantityArea,
            ],
            quantity_names=["Width", "Height", "Perimeter", "Area"],
            quantity_values=[
                3,
                42,
                4.2,
                1.337,
            ],
            quantity_descriptions=[
                "Total outer width of the door lining. It should only be provided, if it is a rectangular door.",
                "Total outer heigth of the door lining. It should only be provided, if it is a rectangular door.",
                "Total perimeter of the outer lining of the door.",
                "Total area of the outer lining of the door.",
            ],
            quantity_set_name="Qto_DoorBaseQuantities",
        )
    ]

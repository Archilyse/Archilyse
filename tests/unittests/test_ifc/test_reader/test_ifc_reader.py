import uuid
from pathlib import Path

import pytest
from shapely.geometry import Point

from brooks.models import SimLayout
from brooks.types import OpeningType
from ifc_reader import reader as reader_module
from ifc_reader.constants import IFC_STAIR
from ifc_reader.exceptions import IfcValidationException


@pytest.fixture
def area_id_area_dict():
    return {"1pPHnf7cXCpPsNEnQf8_6B": 120.00, "2RGlQk4xH47RHK93zcTzUL": 99.84}


def count_layout_openings_by_type(opening_type: OpeningType, layout: SimLayout) -> int:
    return len([opening for opening in layout.openings if opening.type == opening_type])


def test_ifc_reader_get_building_storeys_index(ac20_fzk_haus_ifc_reader):
    storey_index = ac20_fzk_haus_ifc_reader.storeys_by_building
    assert (
        len(
            [
                ac20_fzk_haus_ifc_reader.wrapper.by_id(storey_id)
                for storey_ids in storey_index.values()
                for storey_id in storey_ids
            ]
        )
        == 2
    )


def test_ifc_get_storey_floor_number_index(ac20_fzk_haus_ifc_reader):
    assert ac20_fzk_haus_ifc_reader.storey_floor_numbers == {479: 0, 35065: 1}


def test_ifc_get_decomposed_elements(ifc_file_reader_sia_arc):
    composed_stairs = [
        stair
        for stair in ifc_file_reader_sia_arc.wrapper.by_type(IFC_STAIR)
        if stair.IsDecomposedBy
    ]
    stair_elements = [
        list(ifc_file_reader_sia_arc.get_decomposed_elements(element=composed_stair))
        for composed_stair in composed_stairs
    ]
    assert len(stair_elements) == 9
    assert sum([len(stair_element) for stair_element in stair_elements]) == 27

    assert {
        decomposed_element.is_a()
        for stair_element in stair_elements
        for decomposed_element in stair_element
    } == {"IfcSlab", "IfcStairFlight"}


def test_ifc_get_elevator(ifc_file_reader_sia_arc):
    elevators = ifc_file_reader_sia_arc.get_elevators()
    assert len(elevators) == 7
    assert {element.OperationType for element in elevators} == {"ELEVATOR"}


def test_ifc_get_elevator_missing_operation_type(mocker, ifc_file_reader_sia_arc):
    mocker.patch.object(reader_module.IfcReader, "get_items_of_type", return_value=[1])
    assert ifc_file_reader_sia_arc.get_elevators() == []


def test_ifc_get_elevator_operation_type_is_none(mocker, ifc_file_reader_sia_arc):
    class IfcTransportTest:
        OperationType = None

    mocker.patch.object(
        reader_module.IfcReader, "get_items_of_type", return_value=[IfcTransportTest]
    )
    assert ifc_file_reader_sia_arc.get_elevators() == []


def test_get_address_info_should_return_defaults_when_BuildingAddress_undefined(mocker):
    address_mock = mocker.Mock()
    address_mock.BuildingAddress = None
    address_mock.GlobalId = str(uuid.uuid4())
    address = reader_module.IfcReader(filepath=Path("")).get_address_info(
        ifc_building=address_mock, ifc_filename="filename"
    )
    assert all(address[key] == "N/A" for key in ["city", "zipcode", "street"])
    assert address["housenumber"] == address_mock.GlobalId
    assert address["client_building_id"] == "filename"


@pytest.mark.parametrize(
    "city,zipcode,street",
    [
        ("Zürich", "8005", ["Technoparkstrasse", "1"]),
        ("Baden", None, None),
        (None, None, None),
        (None, None, []),
    ],
)
def test_get_address_info_should_cascade_BuildingAddress_attributes(
    mocker, city, zipcode, street
):
    building_address_mock = mocker.Mock()
    address_data_mock = mocker.Mock()
    address_data_mock.Town = city
    address_data_mock.PostalCode = zipcode
    address_data_mock.AddressLines = street
    building_address_mock.BuildingAddress = address_data_mock
    building_address_mock.GlobalId = str(uuid.uuid4())
    address = reader_module.IfcReader(filepath=Path("")).get_address_info(
        ifc_building=building_address_mock, ifc_filename="filename"
    )
    assert address["city"] == city or "N/A"
    assert address["zipcode"] == zipcode or "N/A"
    assert address["street"] == " Technoparkstrasse 1" or "N/A"
    assert address["housenumber"] == building_address_mock.GlobalId
    assert address["client_building_id"] == "filename"


@pytest.mark.parametrize(
    "longitude_time, latitude_time, expected_reference",
    [
        ((1, 2, 3, 4), (5, 6, 7, 8), Point(1.0341666677777779, 5.101944446666667)),
        ((48, 7, 5), (6, 5, 1), Point(48.11805555555556, 6.083611111111111)),
        ((0, 0, 0), (0, 0, 0), Point(0, 0)),
    ],
)
def test_reference_point_should_have_minimum_hours_minutes_seconds(
    mocker, longitude_time, latitude_time, expected_reference
):
    site_mock = mocker.Mock()
    site_mock.RefLatitude = latitude_time
    site_mock.RefLongitude = longitude_time
    mocker.patch.object(reader_module.IfcReader, "site", site_mock)
    reference = reader_module.IfcReader(filepath=Path("")).reference_point
    assert reference == expected_reference


@pytest.mark.parametrize(
    "longitude_time,latitude_time",
    [
        ((1, 2), (1, 2)),
        ((), ()),
        ((1, 2), (3, 2, 1)),
    ],
)
def test_reference_point_raise_exception_when_hours_minutes_or_seconds_missing(
    mocker, longitude_time, latitude_time
):
    site_mock = mocker.Mock()
    site_mock.RefLatitude = latitude_time
    site_mock.RefLongitude = longitude_time
    mocker.patch.object(reader_module.IfcReader, "site", site_mock)
    with pytest.raises(IfcValidationException):
        reader_module.IfcReader(filepath=Path("")).reference_point


@pytest.mark.parametrize(
    "window_properties_args,operation_type",
    [
        (
            dict(
                Name=None,
                Description=None,
                LiningDepth=50.0,
                LiningThickness=100.0,
                TransomThickness=None,
                MullionThickness=100.0,
                FirstTransomOffset=None,
                SecondTransomOffset=None,
                FirstMullionOffset=0.812024,
                SecondMullionOffset=None,
                ShapeAspectStyle=None,
            ),
            "SINGLE_SWING_RIGHT",
        )
    ],
)
def test_get_relating_type_info_should_filter_out_offending_entity_instances(
    window_properties_args, operation_type
):
    import ifcopenshell

    from ifc_reader.reader import IfcReader

    test_ifc = ifcopenshell.file()
    owner_history = test_ifc.create_entity("IfcOwnerHistory")
    properties = test_ifc.create_entity(
        "IfcWindowLiningProperties",
        GlobalId=ifcopenshell.guid.new(),
        **window_properties_args,
        OwnerHistory=owner_history
    )
    ifc_door_style = test_ifc.create_entity(
        "IfcDoorStyle", HasPropertySets=(properties,), OperationType=operation_type
    )

    reader = IfcReader(filepath=Path("irrelevant"))
    returned_properties = reader.get_relating_type_info(ifc_door_style)

    assert returned_properties == {
        "IfcWindowLiningProperties": {
            **window_properties_args,
            "LiningOffset": None,
            "LiningToPanelOffsetX": None,
            "LiningToPanelOffsetY": None,
        },
        "OperationType": operation_type,
        "Name": None,
    }
    assert "OwnerHistory" not in returned_properties["IfcWindowLiningProperties"].keys()


def test_ifc_2d_sub_entities_from_element_filters_invalid_geometries(mocker):
    element_mock = mocker.Mock()
    element_mock.IsDecomposedBy = []
    mocker.patch.object(
        reader_module.IfcReader, "get_ifc_2d_entity_if_valid", return_value=False
    )
    entities = list(
        reader_module.IfcReader(
            filepath=Path("irrelevant")
        ).ifc_2d_sub_entities_from_element(element=element_mock)
    )
    assert not entities

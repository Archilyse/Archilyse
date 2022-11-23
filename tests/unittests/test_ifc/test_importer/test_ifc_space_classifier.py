import pytest

from handlers.ifc.importer.ifc_reader_space_classifiers import (
    UNDEFINED_CLASSIFICATION_TYPE,
    CustomPropertySetSpaceClassifier,
    LongNameSpaceClassifier,
    ObjectTypeSpaceClassifier,
    get_area_type_for_ifc_space,
)


class IfcSpace:
    LongName = None
    Name = None
    ObjectType = None


@pytest.mark.parametrize(
    "custom_property_name,property_value,area_type",
    [
        ("PSet_BiG_Typ", "Cellar", "Cellar"),
        ("ArchiCADProperties_Raumname", "Dining Room", "Dining Room"),
        (
            "unknown_property",
            "some_value",
            None,
        ),
    ],
)
def test_custom_property_set_classifier(
    custom_property_name, property_value, area_type
):
    assert area_type == CustomPropertySetSpaceClassifier.get_classification(
        space_properties={custom_property_name: property_value}
    )


@pytest.mark.parametrize(
    "classifier,ifc_attribute,area_type",
    [
        (ObjectTypeSpaceClassifier, "ObjectType", "Living Room"),
        (ObjectTypeSpaceClassifier, "ObjectType", None),
        (LongNameSpaceClassifier, "LongName", "Fap Cave"),
        (LongNameSpaceClassifier, "Name", "Bathroom"),
        (LongNameSpaceClassifier, "LongName", None),
    ],
)
def test_ifc_object_type_name_classifiers(classifier, ifc_attribute, area_type):
    ifc_element = IfcSpace()
    setattr(ifc_element, ifc_attribute, area_type)
    assert area_type == classifier.get_classification(ifc_space=ifc_element)


@pytest.mark.parametrize(
    "attributes,properties,expected_classification",
    [
        (
            {"ObjectType": "Schlafzimmer"},
            {},
            "Schlafzimmer",
        ),
        (
            {"LongName": "Schlafzimmer"},
            {},
            "Schlafzimmer",
        ),
        (
            {},
            {"PSet_BiG_Typ": "Schlafzimmer"},
            "Schlafzimmer",
        ),
        (
            {"ObjectType": "dummy"},
            {"RG-DWB_Raumtyp": "Schlafzimmer"},
            "Schlafzimmer",
        ),
        (
            {"LongName": "dummy"},
            {"RG-DWB_Nutzungstyp": "Schlafzimmer"},
            "Schlafzimmer",
        ),
        (
            {},
            {"RG-DWB_Raumtyp": "SLZ", "RG-DWB_Nutzungstyp": "WOH"},
            "Schlafzimmer_Wohnen",
        ),
    ],
)
def test_get_space_classification_priorities(
    attributes,
    properties,
    expected_classification,
):
    ifc_element = IfcSpace()
    for key, value in attributes.items():
        setattr(ifc_element, key, value)
    assert (
        get_area_type_for_ifc_space(ifc_space=ifc_element, space_properties=properties)
        == expected_classification
    )


def test_get_space_classification_not_defined():
    ifc_element = IfcSpace()
    assert UNDEFINED_CLASSIFICATION_TYPE == get_area_type_for_ifc_space(
        ifc_space=ifc_element, space_properties={}
    )

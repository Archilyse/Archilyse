import pytest


@pytest.mark.parametrize(
    "is_public,building_code",
    [
        (True, "BuildingCode_Placeholder1"),
        (False, "BuildingCode_Placeholder2"),
        (False, None),
    ],
)
def test_property_ifc_mapper_add_area_properties(
    mocker, ifc_file_dummy, is_public, building_code
):
    from handlers.ifc.exporter.generators import IfcRelationshipGenerator
    from handlers.ifc.exporter.mappers import PropertyIfcMapper

    add_properties_to_object_mock = mocker.patch.object(
        IfcRelationshipGenerator, "add_properties_to_object"
    )

    PropertyIfcMapper.add_area_properties(
        ifc_file=ifc_file_dummy,
        ifc_space="IfcSpace_placeholder",
        is_public=is_public,
        building_code_type=building_code,
    )

    if building_code:
        assert add_properties_to_object_mock.call_args_list == [
            mocker.call(
                ifc_file=ifc_file_dummy,
                ifc_object="IfcSpace_placeholder",
                property_set_name="Pset_SpaceCommon",
                property_names=["PubliclyAccessible", "Reference"],
                property_values=[is_public, building_code],
                property_descriptions=[
                    "Indication whether this space (in case of e.g., a toilet) is designed to serve as a publicly accessible space, e.g., for a public toilet (TRUE) or not (FALSE).",
                    "Category of space usage or utilization of the area. It is defined according to the presiding national building code.",
                ],
            )
        ]
    else:
        assert add_properties_to_object_mock.call_args_list == [
            mocker.call(
                ifc_file=ifc_file_dummy,
                ifc_object="IfcSpace_placeholder",
                property_set_name="Pset_SpaceCommon",
                property_names=["PubliclyAccessible"],
                property_values=[is_public],
                property_descriptions=[
                    "Indication whether this space (in case of e.g., a toilet) is designed to serve as a publicly accessible space, e.g., for a public toilet (TRUE) or not (FALSE).",
                ],
            )
        ]

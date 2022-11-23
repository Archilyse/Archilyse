from typing import Dict, List, Union

from brooks.types import AreaType

UNDEFINED_CLASSIFICATION_TYPE = "No type defined"

CUSTOM_CLASSIFICATION_PROPERTIES = [
    "PSet_BiG_Typ",
    "ArchiCADProperties_Raumname",
    "RG-DWB_Raumtyp",
    "RG-DWB_Nutzungstyp",
]
CUSTOM_CLASSIFICATION_VERBOSE_MAP = {
    "BFL": "Bürofläche",
    "BLA": "Büro-Lagerräume",
    "BLK": "Balkon/Loggia",
    "BUR": "Büro",
    "BWC": "Büro-WC",
    "EDU": "Schule, Kindergarten, KITA etc.",
    "ENT": "Entrée",
    "ERS": "Erschliessung",
    "FOY": "Foyer",
    "GAS": "Gastro",
    "GEM": "Gemeinschaftsraum",
    "HOB": "vermiet-/verkaufbare Hobbyräume",
    "HOT": "Hotel",
    "KCH": "Küche",
    "NEB": "Übrige Nebenräume (Keller zu Whg., Waschküche etc.)",
    "NGR": "Nasszelle Gross (WC, Lavabo, Bad)",
    "NKL": "Nasszelle Klein (WC, Lavabo, Dusche)",
    "NWC": "Nasszelle WC (WC, Lavabo)",
    "PAR": "Parking",
    "PPA": "Parkplatz im Freien",
    "PPB": "Parkplatz Besucher (Einstellhalle oder im Freien)",
    "PPI": "Parkplatz Einstellhalle",
    "PPM": "Parkplatz Motorrad",
    "PRA": "Parking-Rampe",
    "RED": "Reduit",
    "SLZ": "Schlafzimmer",
    "SON": "Sonstige (andere Nutzungstypen nach Abstimmung bei Fragenbeantwortung)",
    "TEC": "Technik",
    "VDL": "Verkauf, Dienstleistung",
    "VEL": "Veloabstellfläche",
    "WES": "Wohnzimmer mit Küche / Essbereich",
    "WHZ": "Wohnzimmer",
    "WOH": "Wohnen",
}
CUSTOM_CLASSIFICATION_BLACKLIST = {"(.)"}

IMPLENIA_PRE_CLASSIFICATION_MAP = {
    "BWC": AreaType.BATHROOM,
    "BLK": AreaType.LOGGIA,
    "ENT": AreaType.CORRIDOR,
    "FOY": AreaType.CORRIDOR,
    "KCH": AreaType.KITCHEN,
    "NEB": AreaType.STOREROOM,
    "NGR": AreaType.BATHROOM,
    "NKL": AreaType.BATHROOM,
    "NWC": AreaType.BATHROOM,
    "SLZ": AreaType.BEDROOM,
    "WES": AreaType.KITCHEN_DINING,
    "WHZ": AreaType.LIVING_ROOM,
    "WOH": AreaType.LIVING_ROOM,
}


class ObjectTypeSpaceClassifier:
    @staticmethod
    def get_classification(ifc_space) -> Union[str, None]:
        # This one is supposed to be official way of defining the functional category of the space
        # http://docs.buildingsmartalliance.org/MVD_WSIE/schema/ifcproductextension/lexical/ifcspace.htm
        if area_type := ifc_space.ObjectType:
            return area_type
        return None


class LongNameSpaceClassifier:
    @staticmethod
    def get_classification(ifc_space) -> Union[str, None]:
        if area_type := (ifc_space.LongName or ifc_space.Name):
            return area_type
        return None


class CustomPropertySetSpaceClassifier:
    @staticmethod
    def get_classification(space_properties: Dict) -> Union[str, None]:
        if classification_types := [
            str(space_properties.get(classification_name_field))
            for classification_name_field in CUSTOM_CLASSIFICATION_PROPERTIES
            if space_properties.get(classification_name_field)
        ]:
            return "_".join(
                [
                    CUSTOM_CLASSIFICATION_VERBOSE_MAP.get(
                        classification_type.upper(), classification_type
                    )
                    for classification_type in classification_types
                    if classification_type not in CUSTOM_CLASSIFICATION_BLACKLIST
                ]
            )
        return None


def get_area_type_for_ifc_space(ifc_space, space_properties: Dict) -> Union[str, None]:
    if area_type := CustomPropertySetSpaceClassifier.get_classification(
        space_properties=space_properties
    ):
        return area_type
    classifiers: List[Union[ObjectTypeSpaceClassifier, LongNameSpaceClassifier]] = [
        ObjectTypeSpaceClassifier(),
        LongNameSpaceClassifier(),
    ]
    for classifier in classifiers:
        if area_type := classifier.get_classification(ifc_space=ifc_space):
            return area_type
    return UNDEFINED_CLASSIFICATION_TYPE

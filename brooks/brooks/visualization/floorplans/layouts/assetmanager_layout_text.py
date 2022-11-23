from enum import Enum
from typing import Any, Dict, Optional, Union

from brooks.classifications import UnifiedClassificationScheme
from brooks.types import AreaType, SIACategory
from brooks.visualization.floorplans.assetmanager_style import (
    AssetManagerFloorOverviewStyle,
)
from brooks.visualization.floorplans.layouts.constants import (
    ROOM_VERBOSE_NAMES,
    LayoutLayers,
)
from common_utils.constants import SUPPORTED_LANGUAGES


class BaseAssetManagerTextGenerator:
    def __init__(
        self,
        metadata: Dict[str, Any],
        language: SUPPORTED_LANGUAGES,
    ):

        self._metadata = metadata
        self.language = language
        self._classification = UnifiedClassificationScheme()

    @property
    def metadata_upper_left(self) -> Dict[str, str]:
        raise NotImplementedError

    @property
    def metadata_bottom_left(self) -> Dict[str, str]:
        raise NotImplementedError

    @property
    def metadata_upper_right(self) -> Dict[str, str]:
        raise NotImplementedError

    @property
    def metadata_bottom_right(self) -> Dict[str, str]:
        raise NotImplementedError

    @property
    def metadata_title(self) -> str:
        raise NotImplementedError

    @property
    def legal_advise(self) -> str:
        return {
            SUPPORTED_LANGUAGES.DE: "Angaben ohne Gewähr. Änderungen\n bleiben vorbehalten.",
            SUPPORTED_LANGUAGES.EN: "All information is supplied without guarantee\nand subject to change.",
            SUPPORTED_LANGUAGES.FR: "Informations sans garantie. Nous nous réservons \nle droit d'apporter des modifications.",
            SUPPORTED_LANGUAGES.IT: "Tutte le informazioni sono fornite senza garanzia \ne sono soggette a modifiche.",
        }[self.language]

    def generate_metadata_texts(self, axis, w: float, h: float):
        info_font_height_inch = (
            AssetManagerFloorOverviewStyle.INFO_FONT_STYLE.get("size", 12) / 72
        )
        title_font_height_inch = (
            AssetManagerFloorOverviewStyle.TITLE_FONT_STYLE.get("size", 12) / 72
        )
        rows = [
            info_font_height_inch,
            info_font_height_inch * 2.5,
            h - title_font_height_inch * 1.5,  # title
        ]
        columns = [0, 0.2 * w, 0.65 * w, 0.9 * w]

        for key, value in self.metadata_upper_left.items():
            axis.text(
                columns[0],
                rows[1],
                key,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )
            axis.text(
                columns[1],
                rows[1],
                value,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )

        for key, value in self.metadata_bottom_left.items():
            axis.text(
                columns[0],
                rows[0],
                key,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )
            axis.text(
                columns[1],
                rows[0],
                value,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )

        for key, value in self.metadata_upper_right.items():
            axis.text(
                columns[2],
                rows[1],
                key,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )
            axis.text(
                columns[3],
                rows[1],
                value,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )

        for key, value in self.metadata_bottom_right.items():
            axis.text(
                columns[2],
                rows[0],
                key,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )
            axis.text(
                columns[3],
                rows[0],
                value,
                **AssetManagerFloorOverviewStyle.INFO_FONT_STYLE,
            )

        axis.text(
            columns[0],
            rows[2],
            self.metadata_title,
            **AssetManagerFloorOverviewStyle.TITLE_FONT_STYLE,
        )

    def _verbose_floor_number(self, floor_number: int):
        if floor_number == 0:
            return {
                SUPPORTED_LANGUAGES.DE: "Erdgeschoss",
                SUPPORTED_LANGUAGES.EN: "Ground Floor",
                SUPPORTED_LANGUAGES.FR: "Rez-de-chaussée",
                SUPPORTED_LANGUAGES.IT: "Piano terra",
            }[self.language]
        elif floor_number < 0:
            underground = {
                SUPPORTED_LANGUAGES.DE: "Untergeschoss",
                SUPPORTED_LANGUAGES.EN: "Basement",
                SUPPORTED_LANGUAGES.FR: "Sous-sols",
                SUPPORTED_LANGUAGES.IT: "Seminterrato",
            }
            return f"{abs(floor_number)}. {underground[self.language]}"

        return {
            SUPPORTED_LANGUAGES.DE: f"{floor_number}. Obergeschoss",
            SUPPORTED_LANGUAGES.EN: f"{floor_number}. Floor",
            SUPPORTED_LANGUAGES.FR: f"{floor_number}. Etage",
            SUPPORTED_LANGUAGES.IT: f"{floor_number}. Piano",
        }[self.language]

    def _verbose_floor(self):
        return {
            SUPPORTED_LANGUAGES.EN: "Floor",
            SUPPORTED_LANGUAGES.DE: "Geschoss",
            SUPPORTED_LANGUAGES.FR: "Etage",
            SUPPORTED_LANGUAGES.IT: "Piano",
        }[self.language]

    def _verbose_address(self):
        return {
            SUPPORTED_LANGUAGES.EN: "Address",
            SUPPORTED_LANGUAGES.DE: "Adresse",
            SUPPORTED_LANGUAGES.FR: "Adresse",
            SUPPORTED_LANGUAGES.IT: "Indirizzo",
        }[self.language]

    def _verbose_num_rooms(self):
        return {
            SUPPORTED_LANGUAGES.EN: "Rooms",
            SUPPORTED_LANGUAGES.DE: "Zimmer",
            SUPPORTED_LANGUAGES.FR: "Chambre",
            SUPPORTED_LANGUAGES.IT: "Camere",
        }[self.language]

    def _verbose_living_room(self):
        return {
            SUPPORTED_LANGUAGES.EN: "Usage Area",
            SUPPORTED_LANGUAGES.DE: "Nutzfläche",
            SUPPORTED_LANGUAGES.FR: "Espace à utiliser",
            SUPPORTED_LANGUAGES.IT: "Area di utilizzo",
        }[self.language]

    def _verbose_floor_plan(self):
        return {
            SUPPORTED_LANGUAGES.DE: "Grundriss",
            SUPPORTED_LANGUAGES.EN: "Floorplan",
            SUPPORTED_LANGUAGES.FR: "Plan",
            SUPPORTED_LANGUAGES.IT: "Planimetria",
        }[self.language]

    def _verbose_layer(self, layer: LayoutLayers) -> str:
        layers: Dict[Union[LayoutLayers, AreaType], Dict[SUPPORTED_LANGUAGES, str]] = {
            LayoutLayers.WALLS: {
                SUPPORTED_LANGUAGES.EN: "Walls",
                SUPPORTED_LANGUAGES.DE: "Wände",
                SUPPORTED_LANGUAGES.FR: "Murs",
                SUPPORTED_LANGUAGES.IT: "Pareti",
            },
            LayoutLayers.RAILINGS: {
                SUPPORTED_LANGUAGES.EN: "Railings",
                SUPPORTED_LANGUAGES.DE: "Geländer",
                SUPPORTED_LANGUAGES.FR: "Balustrades",
                SUPPORTED_LANGUAGES.IT: "Ringhiera",
            },
            LayoutLayers.WINDOWS: {
                SUPPORTED_LANGUAGES.EN: "Windows",
                SUPPORTED_LANGUAGES.DE: "Fenster",
                SUPPORTED_LANGUAGES.FR: "Fenêtres",
                SUPPORTED_LANGUAGES.IT: "Finestre",
            },
            LayoutLayers.DOORS: {
                SUPPORTED_LANGUAGES.EN: "Doors",
                SUPPORTED_LANGUAGES.DE: "Türen",
                SUPPORTED_LANGUAGES.FR: "Portes",
                SUPPORTED_LANGUAGES.IT: "Porte",
            },
            LayoutLayers.ROOM_POLYGONS: {
                SUPPORTED_LANGUAGES.EN: "Room Polygons",
                SUPPORTED_LANGUAGES.DE: "Raumpolygone",
                SUPPORTED_LANGUAGES.FR: "Polygone de la pièce",
                SUPPORTED_LANGUAGES.IT: "Perimetro abitativo",
            },
            LayoutLayers.ROOM_STAMP: {
                SUPPORTED_LANGUAGES.EN: "Room Stamp",
                SUPPORTED_LANGUAGES.DE: "Raumstempel",
                SUPPORTED_LANGUAGES.FR: "Marque de zone",
                SUPPORTED_LANGUAGES.IT: "Cartiglio locale",
            },
            LayoutLayers.TITLE_BLOCK: {
                SUPPORTED_LANGUAGES.EN: "Titleblock",
                SUPPORTED_LANGUAGES.DE: "Plankopf",
                SUPPORTED_LANGUAGES.FR: "En-tête",
                SUPPORTED_LANGUAGES.IT: "Cartiglio piano",
            },
            LayoutLayers.DIMENSIONING: {
                SUPPORTED_LANGUAGES.EN: "Dimensioning",
                SUPPORTED_LANGUAGES.DE: "Bemassung",
                SUPPORTED_LANGUAGES.FR: "Dimensions",
                SUPPORTED_LANGUAGES.IT: "Dimensionamento",
            },
            LayoutLayers.FEATURES: {
                SUPPORTED_LANGUAGES.EN: "Furniture",
                SUPPORTED_LANGUAGES.DE: "Möblierung",
                SUPPORTED_LANGUAGES.FR: "Meuble",
                SUPPORTED_LANGUAGES.IT: "Arredamento",
            },
            LayoutLayers.UNITS: {
                SUPPORTED_LANGUAGES.EN: "Residential Units",
                SUPPORTED_LANGUAGES.DE: "Wohneinheiten",
                SUPPORTED_LANGUAGES.FR: "L'unité",
                SUPPORTED_LANGUAGES.IT: "Unità abitative",
            },
            LayoutLayers.SHAFTS: {
                SUPPORTED_LANGUAGES.EN: "Shafts",
                SUPPORTED_LANGUAGES.DE: "Schächte",
                SUPPORTED_LANGUAGES.FR: "Cages",
                SUPPORTED_LANGUAGES.IT: "Condottos",
            },
            LayoutLayers.STAIRS_ELEVATORS: {
                SUPPORTED_LANGUAGES.EN: "Stairs and Elevators",
                SUPPORTED_LANGUAGES.DE: "Treppen und Aufzüge",
                SUPPORTED_LANGUAGES.FR: "Escaliers et Ascenseurs",
                SUPPORTED_LANGUAGES.IT: "Scale e Ascensori",
            },
            LayoutLayers.SANITARY_AND_KITCHEN: {
                SUPPORTED_LANGUAGES.EN: "Sanitary and Kitchen Appliances",
                SUPPORTED_LANGUAGES.DE: "Sanitär- und Kücheneinrichtung",
                SUPPORTED_LANGUAGES.FR: "Sanitaires et Appareils de cuisine",
                SUPPORTED_LANGUAGES.IT: "Sanitari e Elettrodomestici da cucina",
            },
        }
        sia_layers: Dict[SIACategory, Dict[SUPPORTED_LANGUAGES, str]] = {
            sia_area_type: {
                SUPPORTED_LANGUAGES.EN: f"SIA416-{sia_area_type.name}",
                SUPPORTED_LANGUAGES.DE: f"SIA416-{sia_area_type.name}",
                SUPPORTED_LANGUAGES.FR: f"SIA416-{sia_area_type.name}",
                SUPPORTED_LANGUAGES.IT: f"SIA416-{sia_area_type.name}",
            }
            for sia_area_type in {
                SIACategory.ANF,
                SIACategory.FF,
                SIACategory.VF,
                SIACategory.HNF,
                SIACategory.NNF,
            }
        }
        layers.update(sia_layers)  # type: ignore
        if layer not in layers:
            raise ValueError(f"No translation for layer {layer} found.")

        return self.remove_umlaut(string=layers[layer][self.language])

    @staticmethod
    def remove_umlaut(string: str) -> str:
        """
        Removes umlauts from strings and replaces them with the letter+e convention
        :param string: string to remove umlauts from
        :return: unumlauted string
        """
        string = string.replace("ü", "ue")
        string = string.replace("Ü", "Ue")
        string = string.replace("ä", "ae")
        string = string.replace("Ä", "Ae")
        string = string.replace("ö", "oe")
        string = string.replace("Ö", "Oe")
        string = string.replace("ß", "ss")

        return string

    @property
    def area_type_to_name_mapping(self) -> Dict[Enum, Optional[str]]:

        return ROOM_VERBOSE_NAMES[self.language]


class ApartmentAssetManagerTextGenerator(BaseAssetManagerTextGenerator):
    @property
    def metadata_upper_left(self):
        return {
            self._verbose_address(): f"{self._metadata['street']} "
            f"{self._metadata['housenumber']}, "
            f"{self._metadata['city']}"
        }

    @property
    def metadata_bottom_left(self):
        return {self._verbose_num_rooms(): f"{self._metadata['number_of_rooms']}"}

    @property
    def metadata_upper_right(self):
        return {self._verbose_living_room(): f"{self._metadata['net_area']:.0f} m²"}

    @property
    def metadata_bottom_right(self):
        return {
            self._verbose_floor(): f"{self._verbose_floor_number(self._metadata['level'])}"
        }

    @property
    def metadata_title(self):
        return self._verbose_floor_plan()


class FloorAssetManagerTextGenerator(BaseAssetManagerTextGenerator):
    @property
    def metadata_upper_left(self):
        return {
            self._verbose_address(): f"{self._metadata['street']} {self._metadata['housenumber']}, "
            f"{self._metadata['zipcode']} {self._metadata['city']}"
        }

    @property
    def metadata_bottom_left(self):
        return {
            self._verbose_floor(): f"{self._verbose_floor_number(self._metadata['level'])}"
        }

    @property
    def metadata_upper_right(self):
        return {}

    @property
    def metadata_bottom_right(self):
        return {}

    @property
    def metadata_title(self):
        return self._verbose_floor_plan()

from enum import Enum

STREET_TYPE_WIDTH = {  # all values in meters
    "Ausfahrt": 3.5,
    "Einfahrt": 3.5,
    "Autobahn": 2 * 3.5,
    "Raststaette": 3.5,
    "Zufahrt": 2 * 3.5,
    "Dienstzufahrt": 4,
    "10m Strasse": 10.20,
    "6m Strasse": 7,
    "4m Strasse": 5,
    "3m Strasse": 3.5,
    "2m Weg": 2,
    "1m Weg": 1,
    "1m Wegfragment": 1,
    "2m Wegfragment": 2,
    "8m Strasse": 9,
    "Autostrasse": 7,
}
STREETS_WO_CAR_TRAFFIC = {
    "Allgemeine Verkehrsbeschraenkung",  # generally limited
    "Allgemeines Fahrverbot",  # generally forbidden
    "Gesicherte Kletterpartie",  # climbing
    "Gesperrt",  # closed
}
PEDESTRIAN_STREET_TYPES = {
    "2m Weg": 2,
    "1m Weg": 1,
    "1m Wegfragment": 1,
    "2m Wegfragment": 2,
}
HIGHWAY_CONDITIONS = "Hochleistungsstrasse"
PRIMARY_CONDITIONS = "Durchgangsstrasse"
SECONDARY_CONDITIONS = "Verbindungsstrasse"
STREET_TYPES_TO_EXCLUDE = {
    "Verbindung",  # Link
    "Platz",  # Square",
    "Autozug",  # Car train
    "Faehre",  # Ferry
}


class STREET_CLASS(Enum):
    PEDESTRIAN = "PEDESTRIAN"
    HIGHWAY = "HIGHWAY"
    TERTIARY_STREET = "TERTIARY_STREET"
    SECONDARY_STREET = "SECONDARY_STREET"
    PRIMARY_STREET = "PRIMARY_STREET"

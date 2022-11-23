from enum import Enum
from typing import Dict, List

COMPETITION_SIZES_MARGIN = 0.95
MINIMUM_CORRIDOR_WIDTHS = (1.2, 1.5)
DEFAULT_MIN_STORE_ROOM_AREA = 3.0
DEFAULT_MIN_TOTAL_AREA = 12.0

# Defaults for min room sizes
BIG_ROOM_AREA_REQ = 14.0
SMALL_ROOM_AREA_REQ = 12.0
SMALL_ROOM_SIDE_REQ = 3.0
AREA_REQ_BATHROOM = 3.8
SMALLER_SIDE_REQ_BATHROOM = 1.7
DINING_AREA_TABLE_MIN_BIG_SIDE = 3
DINING_AREA_TABLE_MIN_SMALL_SIDE = 2


class CompetitionFeatures(Enum):
    RESIDENTIAL_USE = "evaluation_residential_use"
    RESIDENTIAL_USE_RATIO = "residential_commercial_ratio"
    RESIDENTIAL_TOTAL_HNF_REQ = "residential_total_hnf_requirement"
    BUILDING_AVG_MAX_RECT_ALL_APT_AREAS = "open_space_over_largest_possible_square"
    BUILDING_PCT_CIRCULATION_RESIDENTIAL = (
        "determination_of_the_non_usable_circulation_area"
    )
    BUILDING_BICYCLE_BOXES_AVAILABLE = "determining_whether_bicycle_boxes_are_available"
    BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE = "bicycle_boxes_count_check"
    BUILDING_MINIMUM_ELEVATOR_DIMENSIONS = "check_lift_size_according_to_sia_500"

    APT_RATIO_OUTDOOR_INDOOR = "calculation_ratio_of_floor_space"
    APT_PCT_W_OUTDOOR = "recording_outdoor_space_available"
    APT_MAX_RECT_IN_PRIVATE_OUTDOOR = (
        "spaciousness_outside_areas_with_largest_possible_square"
    )
    APT_MIN_OUTDOOR_REQUIREMENT = "minimum_outdoor_space_requirement"
    APT_RATIO_REDUIT_W_WATER_CONNEXION = "washing_machine_tumble_dryer_proximity"
    APT_HAS_WASHING_MACHINE = "determining_whether_a_washing_machine_is_available"
    APT_PCT_W_STORAGE = "determining_whether_reduit_is_available"
    APT_DISTRIBUTION_TYPES = "minor_deviations_from_the_specified_room_programme"
    APT_DISTRIBUTION_TYPES_AREA_REQ = "area_requirement_for_each_apt_type"
    APT_SHOWER_BATHTUB_DISTRIBUTION = "determining_the_distribution_of_shower_bathtub"
    APT_BATHROOMS_TOILETS_DISTRIBUTION = "bathrooms_toilets_distribution"
    APT_RATIO_NAVIGABLE_AREAS = "testing_of_all_aisle_widths"
    APT_RATIO_BATHROOM_MIN_REQUIREMENT = "apt_ratio_bathroom_minimum_requirement_sia500"
    APT_RATIO_BEDROOM_MIN_REQUIREMENT = "apt_ratio_bedroom_minimum_requirement_sia500"
    APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE = (
        "apt_living_dining_min_requirement_per_apt_type"
    )
    APT_SIZE_DINING_TABLE_REQ = "apt_size_dining_table_req"

    # JANITOR
    JANITOR_HAS_WC = "determining_whether_wc_is_available"
    JANITOR_HAS_STORAGE = "determination_whether_a_janitor_storage_room_is_available"
    JANITOR_OFFICE_MIN_SIZE_REQUIREMENT = (
        "janitor_room_determination_of_size_and_comparison_with_requirement"
    )
    JANITOR_STORAGE_MIN_SIZE_REQUIREMENT = "janitor_storage_min_size_requirement"
    JANITOR_WC_CLOSENESS = "determining_whether_wc_is_adjacent_or_adjoining"
    JANITOR_WATER_CONN_AVAILABLE = (
        "determining_whether_a_sink_water_connection_is_available"
    )

    # ARCHILYSE FEATURES
    ANALYSIS_GREENERY = "analysis_greenery"
    ANALYSIS_SKY = "analysis_sky"
    ANALYSIS_BUILDINGS = "analysis_buildings"
    ANALYSIS_WATER = "analysis_water"
    ANALYSIS_RAILWAY_TRACKS = "analysis_railway_tracks"
    ANALYSIS_STREETS = "analysis_streets"
    APT_AVG_DARKEST_ROOM_SUMMER = "darkest_room_detection"
    APT_AVG_BRIGHTEST_ROOM_WINTER = "brightest_room_detection"
    APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER = (
        "calculation_of_total_sunshine_hours_in_summer"
    )
    APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER = (
        "calculation_of_total_hours_of_sunshine_in_winter"
    )
    NOISE_STRUCTURAL = "structural_measures_assessment"
    NOISE_INSULATED_ROOMS = "ventilated_rooms"

    # Uploaded features
    DRYING_ROOM_SIZE = "drying_room_size"
    JANITOR_OFFICE_LIGHT = "janitor_office_natural_light"
    PRAMS_ROOM_BARRIER_FREE_ACCESS = (
        "determining_whether_barrier_free_access_is_guaranteed"
    )
    BIKE_BOXES_DIMENSIONS = "determining_whether_minimum_dimension_requirements_are_met"
    BIKE_BOXES_POWER_SUPPLY = "determining_whether_there_is_a_power_supply"
    PRAMS_AND_BIKES_CLOSE_TO_ENTRANCE = "prams_bikes_close_to_entrance"
    BASEMENT_COMPARTMENT_AVAILABLE = "basement_compartment_availability"
    BASEMENT_COMPARTMENT_SIZE_REQ = "basement_compartment_size_requirement"
    GUESS_ROOM_SIZE_REQ = "guess_room_size_requirement"

    # Uploaded feature counting
    KITCHEN_ELEMENTS_REQUIREMENT = "kitchen_elements_requirement"
    ENTRANCE_WARDROBE_ELEMENT_REQUIREMENT = "entrance_wardrobe_element_requirement"
    BEDROOM_WARDROBE_ELEMENT_REQUIREMENT = "bedroom_wardrobe_element_requirement"
    SINK_SIZES_REQUIREMENT = "sink_sizes_requirement"

    # Uploaded for Car, bicycle, bicycle parking
    CAR_PARKING_SPACES = "car_parking_spaces"
    TWO_WHEELS_PARKING_SPACES = "two_wheels_parking_spaces"
    BIKE_PARKING_SPACES = "bike_parking_spaces"
    SECOND_BASEMENT_FLOOR_AVAILABLE = "second_basement_available"
    AGF_W_REDUIT = "recording_of_the_agf_incl_reduit"


CATEGORIES: List[Dict] = [
    {
        "name_en": "Architecture – Overview",
        "name": "Architektur – Allgemein",
        "key": "architecture_usage",
        "sub_sections": [
            {
                "name_en": "Usage",
                "name": "Nutzung",
                "key": "residential_share",
                "sub_sections": [
                    {
                        "name_en": "Residential Share",
                        "name": "Wohnnutzung",
                        "key": CompetitionFeatures.RESIDENTIAL_USE.value,
                        "code": CompetitionFeatures.RESIDENTIAL_USE.name,
                        "editing_type": "competitors",
                        "info_en": """Indicates whether the project contains uses other than residential.""",
                        "info": """Angabe, ob das Projekt andere Nutzungen als eine Wohnnutzung enthält.""",
                    },
                    {
                        "name_en": "Residential Area",
                        "name": "Flächenanteil Wohnen",
                        "key": CompetitionFeatures.RESIDENTIAL_USE_RATIO.value,
                        "code": CompetitionFeatures.RESIDENTIAL_USE_RATIO.name,
                        "info_en": """Percentage of the total of all residential areas (m2) from the total of all residential and commercial areas (m2) of a project. """,
                        "info": """Prozentualer Anteil der Summe aller Wohnflächen (m2) von der Summe aller Wohn- und Gewerbeflächen (m2) eines Projektes.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Project development HNF",
                        "name": "Projektentwicklung HNF",
                        "key": CompetitionFeatures.RESIDENTIAL_TOTAL_HNF_REQ.value,
                        "code": CompetitionFeatures.RESIDENTIAL_TOTAL_HNF_REQ.name,
                        "info_en": """""",
                        "info": """""",
                        "unit": "m2",
                    },
                ],
            },
            {
                "name_en": "Noise",
                "name": "Lärm",
                "key": "noise",
                "sub_sections": [
                    {
                        "name_en": 'Analysis "Noise"',
                        "name": 'Analyse "Lärm"',
                        "key": CompetitionFeatures.NOISE_STRUCTURAL.value,
                        "code": CompetitionFeatures.NOISE_STRUCTURAL.name,
                        "info_en": "The noise simulation takes into account the direct road and railway noise (day and night) in the urban environment and gives the average of the noise exposure of all noise-sensitive rooms (entire project).",
                        "info": "Die Lärmsimulation berücksichtigt den direkten Strassen- und Eisenbahnverkehr (Tag und Nacht) in der urbanen Umgebung und gibt den Durchschnitt der Lärmbelastung aller lärmempfindlichen Räume (gesamtes Projekt) wieder.",
                        "unit": "dB",
                    },
                    {
                        "name_en": "Noise insulated rooms",
                        "name": "Lärm abgewandte Räume",
                        "key": CompetitionFeatures.NOISE_INSULATED_ROOMS.value,
                        "code": CompetitionFeatures.NOISE_INSULATED_ROOMS.name,
                        "info_en": """Percentage of all noise-sensitive rooms (entire project) with at least one window whose noise exposure to road and railway traffic (day and night) is below a defined threshold.""",
                        "info": """Prozentualer Anteil aller lärmempfindlichen Räume (gesamtes Projekt), welche mindestens ein Fenster aufweisen dessen Lärmbelastung für Strassen- und Eisenbahnverkehr (Tag)  unterhalb eines definierten Schwellenwertes liegt.""",
                        "unit": "%",
                    },
                ],
            },
        ],
    },
    {
        "name_en": "Architecture – Project Specific",
        "name": "Architektur – Projektspezifisch",
        "key": "architecture_room_programme",
        "sub_sections": [
            {
                "name_en": "Generosity",
                "name": "Grosszügigkeit",
                "key": "generosity",
                "sub_sections": [
                    {
                        "name_en": "Open Spaces Apartments",
                        "name": "Freiflächen Wohnung",
                        "key": CompetitionFeatures.BUILDING_AVG_MAX_RECT_ALL_APT_AREAS.value,
                        "code": CompetitionFeatures.BUILDING_AVG_MAX_RECT_ALL_APT_AREAS.name,
                        "info_en": """For every apartment the largest possible rectangle in the open space is calculated, which gives an indication for the small-scale of the floorplan design. The result is the average of all largest possible squares of the entire project in m².""",
                        "info": """Für jede Wohnung wird das grösstmögliche Quadrat im Freiraum berechnet, was einen Hinweis auf die Kleinteiligkeit der Grundrissgestaltung gibt. Das Ergebnis ist der Durchschnitt aller grösstmöglichen Quadrate des gesamten Projekts in m².""",
                        "unit": "m²",
                    },
                    {
                        "name_en": "Minimum room size",
                        "name": "Minimale Raumgrösse",
                        "key": CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value,
                        "code": CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.name,
                        "info_en": """The minimum room size controls the percentage of rooms from the entire project that fulfills the minimum room size criteria. The criteria is: At least one room of each apartment needs to have min. dimensions of 3 x 4.7m (14m2). In apartments with two ore more rooms all other rooms need to have min. dimensions of 3 x 4m (12m2)""",
                        "info": """Der prozentuale Anteil der Räume (gesamtes Projekt), welche die Kriterien für die Mindestraumgrösse erfüllen.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Minimum living/dining/kitchen size",
                        "name": "Minimale Wohnen/Essen/Küche-grösse",
                        "key": CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value,
                        "code": CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.name,
                        "info_en": """""",
                        "info": """""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Minimum outside surface size",
                        "name": "Minimale Aussenflächegrösse",
                        "key": CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value,
                        "code": CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.name,
                        "info_en": """""",
                        "info": """""",
                        "unit": "%",
                    },
                ],
            },
            {
                "name_en": "Exposure",
                "name": "Belichtung",
                "key": "exposure",
                "sub_sections": [
                    {
                        "name_en": "Solar Radiation per Room (Summer)",
                        "name": "Solare Einstrahlung je Zimmer (Sommer)",
                        "key": CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.value,
                        "code": CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.name,
                        "info_en": """Average solar radiation per room (entire project), calculated for summer (21st of June). Only bedrooms and living rooms are considered. For thermal comfort within the building, low solar radiation is desired in summer.""",
                        "info": """Durchschnittliche Sonneneinstrahlung pro Raum (gesamte Anlage), berechnet für den Sommer (21. Juni). Es werden nur Schlaf- und Wohnräume berücksichtigt. Für den thermischen Komfort innerhalb des Gebäudes ist im Sommer eine niedrige Sonneneinstrahlung gewünscht.""",
                        "unit": "lx",
                    },
                    {
                        "name_en": "Solar Radiation per Room (Winter)",
                        "name": "Solare Einstrahlung je Zimmer (Winter)",
                        "key": CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER.value,
                        "code": CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER.name,
                        "info_en": """Average solar radiation per room (entire project), calculated for winter (21st of December). Only bedrooms and living rooms are considered. For thermal comfort within the building, high solar radiation is desired in winter.""",
                        "info": """Durchschnittliche Sonneneinstrahlung pro Raum (gesamtes Projekt), berechnet für den Winter (21. Dezember). Es werden nur Schlaf- und Wohnräume berücksichtigt. Für den thermischen Komfort innerhalb des Gebäudes ist im Winter eine hohe Sonneneinstrahlung gewünscht.""",
                        "unit": "lx",
                    },
                ],
            },
            {
                "name_en": "Private outdoor areas",
                "name": "Private Aussenflächen",
                "key": "private_outdoor_areas",
                "sub_sections": [
                    {
                        "name_en": "Availability Private Outdoor Areas",
                        "name": "Verfügbarkeit Private Aussenflächen",
                        "key": CompetitionFeatures.APT_PCT_W_OUTDOOR.value,
                        "code": CompetitionFeatures.APT_PCT_W_OUTDOOR.name,
                        "info_en": """Percentage of all flats (entire project) with private outdoor area. Considered as private outdoor area are areas clearly attributed to a specific flat, such as outdoor seating area, loggia, terrace or balcony.""",
                        "info": """Prozentualer Anteil aller Wohnungen (gesamtes Projekt) mit privaten Aussenflächen. Als private Aussenflächen gelten alle einer spezifischen Wohnung eindeutig zuschlagbaren Aussenflächen wie Aussensitzplatz, Loggia, Terrasse oder Balkon.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Ratio between Outdoor Space and Indoor Space",
                        "name": "Verhältnis Innenraum zu Aussenraum",
                        "key": CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value,
                        "code": CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.name,
                        "info_en": """Ratio between the net indoor and outdoor area of a flat, percentage calculated for the entire project. """,
                        "info": """Verhältnis zwischen der Netto-Innen- und Aussenfläche einer Wohnung, prozentual berechnet für das gesamte Projekt. """,
                        "unit": "%",
                    },
                    {
                        "name_en": "Sun Hours Private Outdoor Areas (Summer)",
                        "name": "Sonnenstunden Private Aussenflächen (Sommer)",
                        "key": CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER.value,
                        "code": CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER.name,
                        "info_en": """Average daily duration of daylight exposure exceeding 18klx in private outdoor areas during summer (21st of June).""",
                        "info": """Durchschnittliche Stunden Tageslicht (mehr als 18 klx) auf privaten Aussenflächen im Sommer (21. Juni) für das ganze Projekt.""",
                        "unit": "time_delta",
                    },
                    {
                        "name_en": "Sun Hours Private Outdoor Areas (Winter)",
                        "name": "Sonnenstunden Private Aussenflächen (Winter)",
                        "key": CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER.value,
                        "code": CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER.name,
                        "info_en": """Average daily duration of daylight exposure exceeding 7klx in private outdoor areas during winter (21st of December).""",
                        "info": """Durchschnittliche Stunden Tageslicht (mehr als 7 klx) auf privaten Aussenflächen im Winter (21. Dezember) für das ganze Projekt.""",
                        "unit": "time_delta",
                    },
                    {
                        "name_en": "Open Spaces Private Outdoor Areas",
                        "name": "Freiflächen Private Aussenflächen",
                        "key": CompetitionFeatures.APT_MAX_RECT_IN_PRIVATE_OUTDOOR.value,
                        "code": CompetitionFeatures.APT_MAX_RECT_IN_PRIVATE_OUTDOOR.name,
                        "info_en": """Average size of the largest possible rectangle that can be placed on a private outdoor area per apartment.""",
                        "info": """Durchschnittliche Grösse des grösstmöglichen Rechtecks, welches auf einem privaten Aussenbereich pro Apartment platziert werden kann.""",
                        "unit": "m²",
                    },
                ],
            },
            {
                "name_en": "Furnishability",
                "name": "Möblierbarkeit",
                "key": "furnishability",
                "sub_sections": [
                    {
                        "name_en": "Dimensions of sanitary elements",
                        "name": "Abmessungen der Sanitärelemente",
                        "key": CompetitionFeatures.SINK_SIZES_REQUIREMENT.value,
                        "code": CompetitionFeatures.SINK_SIZES_REQUIREMENT.name,
                        "info_en": """""",
                        "info": """""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Dining Area Size",
                        "name": "Grösse Essbereich",
                        "key": CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value,
                        "code": CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.name,
                        "info_en": """""",
                        "info": """....""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Kitchen elements count",
                        "name": "Nummer Küchenelemente",
                        "key": CompetitionFeatures.KITCHEN_ELEMENTS_REQUIREMENT.value,
                        "code": CompetitionFeatures.KITCHEN_ELEMENTS_REQUIREMENT.name,
                        "info_en": """""",
                        "info": """....""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Number of wardrobe elements for entrance",
                        "name": "Nummer Schrank Elemente Eingang",
                        "key": CompetitionFeatures.ENTRANCE_WARDROBE_ELEMENT_REQUIREMENT.value,
                        "code": CompetitionFeatures.ENTRANCE_WARDROBE_ELEMENT_REQUIREMENT.name,
                        "info_en": """""",
                        "info": """....""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Number of wardrobe elements for beedroom",
                        "name": "Nummer Schrank Elemente Schlafzimmer",
                        "key": CompetitionFeatures.BEDROOM_WARDROBE_ELEMENT_REQUIREMENT.value,
                        "code": CompetitionFeatures.BEDROOM_WARDROBE_ELEMENT_REQUIREMENT.name,
                        "info_en": """""",
                        "info": """....""",
                        "unit": "%",
                    },
                ],
            },
            {
                "name_en": "Circulation Area Apartment",
                "name": "Verkehrsflächen Wohnung",
                "key": "flat_circulation_areas",
                "sub_sections": [
                    {
                        "name_en": "Circulation Area Share",
                        "name": "Verkehrsflächenanteil",
                        "key": CompetitionFeatures.BUILDING_PCT_CIRCULATION_RESIDENTIAL.value,
                        "code": CompetitionFeatures.BUILDING_PCT_CIRCULATION_RESIDENTIAL.name,
                        "info_en": """Ratio between the circulation areas such as stairs and corridors and the total area of a flat, percentage calculated for the entire project. """,
                        "info": """Verhältnis zwischen den Verkehrsflächen wie Treppen und Fluren und der Gesamtfläche einer Wohnung, prozentual berechnet für das gesamte Projekt. """,
                        "unit": "%",
                    }
                ],
            },
            {
                "name_en": "Apartment Mix",
                "name": "Wohnungsmix",
                "key": "flat_deviation",
                "sub_sections": [
                    {
                        "name_en": "Balance Apartment Mix",
                        "name": "Abgleich Wohnungsmix",
                        "key": CompetitionFeatures.APT_DISTRIBUTION_TYPES.value,
                        "code": CompetitionFeatures.APT_DISTRIBUTION_TYPES.name,
                        "info_en": """Percentage compliance with the predefined apartment mix.""",
                        "info": """Prozentuale Übereinstimmung mit dem vorgegebenen Wohnungsmix.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Comparison with the minimum main floor space per apartment type",
                        "name": "Vergleich mit den Mindesthauptnutzflächen pro Wohnungstyp",
                        "key": CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value,
                        "code": CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.name,
                        "info_en": """TODO""",
                        "info": """TODO""",
                        "unit": "%",
                    },
                ],
            },
            {
                "name_en": "Storage (in Apartment)",
                "name": "Abstellraum (in der Wohnung)",
                "key": "reduit",
                "sub_sections": [
                    {
                        "name_en": "Availability Storage",
                        "name": "Verfügbarkeit Abstellraum",
                        "key": CompetitionFeatures.APT_PCT_W_STORAGE.value,
                        "code": CompetitionFeatures.APT_PCT_W_STORAGE.name,
                        "info_en": """Percentage of all apartments that provide a storage as defined.""",
                        "info": """Prozentsatz aller Wohnungen, die einen Abstellraum gem. Definition enthalten.""",
                        "unit": "%",
                    },
                ],
            },
            {
                "name_en": "Washing Machine / Dryer",
                "name": "Waschmaschine / Trockner",
                "key": "wa_ma/tumble_dryer",
                "sub_sections": [
                    {
                        "name_en": "Connection Possibility for Washing Tower in Storage",
                        "name": "Anschlussmöglichkeit Waschturm in Abstellraum",
                        "key": CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value,
                        "code": CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.name,
                        "info_en": """Percentage of all apartments that offer at least one separated storage with connection possibility for a washing tower. The criteria are: a kitchen, bathroom or shaft is located within a radius of at least 1.0 m. The floor size of the Storage must be at least 1 x 2 m.""",
                        "info": """Prozentualer Anteil aller Wohnungen, die mindestens einen separaten Abstellraum mit Anschlussmöglichkeit für einen Waschturm bieten. Die Kriterien sind: eine Küche, ein Bad oder ein Schacht befindet sich in einem Radius von mindestens 1,0 m. Die Grösse des Abstellraums muss mindestens 1 x 2 m betragen.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Availability tumble dryer and washing machine",
                        "name": "Verfügbarkeit Tumbler und Waschmaschine",
                        "key": CompetitionFeatures.APT_HAS_WASHING_MACHINE.value,
                        "code": CompetitionFeatures.APT_HAS_WASHING_MACHINE.name,
                        "info_en": """....""",
                        "info": """....""",
                        "unit": "%",
                    },
                ],
            },
            {
                "name_en": "Distribution Wet Rooms",
                "name": "Verteilung Nasszellen",
                "key": "distribution_showers/bathtubs",
                "sub_sections": [
                    # This 2 have same definitions as they are meant to be used exclusively to each other
                    {
                        "name_en": "Distribution Shower/Bathtub",
                        "name": "Verteilung Dusche/Badewanne",
                        "key": CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value,
                        "code": CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.name,
                        "info_en": """Percentage compliance with the predefined distribution of shower and bathtubs""",
                        "info": """Prozentuale Einhaltung der vordefinierten Verteilung von Duschen und Badewannen""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Availability number of washrooms/WC per apartment",
                        "name": "Verfügbarkeit Anzahl Nasszellen pro Wohnung",
                        "key": CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value,
                        "code": CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.name,
                        "info_en": """Percentage of apartments that meet the required number of wet rooms (bath/shower/WC) per type and housing unit.""",
                        "info": """Prozentuale Angabe der Wohneinheiten, welche die angegebene Anzahl Nasszellen (Bad/Dusche/WC) je Typ und Wohneinheit erfüllen.""",
                        "unit": "%",
                    },
                ],
            },
            {
                "name_en": "Drying Rooms",
                "name": "Trockenräume",
                "key": "drying_rooms",
                "sub_sections": [
                    {
                        "name_en": "Requirements Drying Room",
                        "name": "Anforderungen Trocknungsräume",
                        "key": CompetitionFeatures.DRYING_ROOM_SIZE.value,
                        "code": CompetitionFeatures.DRYING_ROOM_SIZE.name,
                        "info_en": """Indicates whether there is at least one drying room with the specified minimum area for each building/main entrance/staircase.""",
                        "info": """Angabe, ob je Gebäude/Hauptzugang/Treppenhaus mindestens ein Trockenraum mit der angegebenen Mindestfläche vorhanden ist.""",
                    },
                ],
            },
            {
                "name_en": "Janitor storeroom",
                "name": "Hauswart Lager",
                "key": "janitor_storeroom",
                "sub_sections": [
                    {
                        "name_en": "Availability Janitor Storeroom",
                        "name": "Verfügbarkeit Hauswart Lager",
                        "key": CompetitionFeatures.JANITOR_HAS_STORAGE.value,
                        "code": CompetitionFeatures.JANITOR_HAS_STORAGE.name,
                        "info_en": """Indicates whether a janitor storeroom is available for the property. """,
                        "info": """Angabe, ob für die Liegenschaft ein Hauswart Lager vorhanden ist. """,
                    },
                    {
                        "name_en": "Size Janitor Storeroom",
                        "name": "Grösse Hauswart Lager ",
                        "key": CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value,
                        "code": CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.name,
                        "info_en": """Indicates whether the janitor storeroom meets the client's specific size requirements.""",
                        "info": """Angabe, ob das Hauswart Lager den kundenspezifischen Grössenanforderungen entspricht.""",
                    },
                    {
                        "name_en": "Water Connection Janitor Storeroom",
                        "name": "Wasseranschluss Hauswart Lager",
                        "key": CompetitionFeatures.JANITOR_WATER_CONN_AVAILABLE.value,
                        "code": CompetitionFeatures.JANITOR_WATER_CONN_AVAILABLE.name,
                        "info_en": """Indicates whether the janitor storeroom provides a water connection.""",
                        "info": """Angabe, ob das Hauswart Lager über einen Wasseranschluss verfügt.""",
                    },
                ],
            },
            {
                "name_en": "Janitor Office",
                "name": "Hauswart Büro",
                "key": "janitor_office",
                "sub_sections": [
                    {
                        "name_en": "Natural Lighting Janitor Office",
                        "name": "Natürliche Belichtung Hauswart Büro",
                        "key": CompetitionFeatures.JANITOR_OFFICE_LIGHT.value,
                        "code": CompetitionFeatures.JANITOR_OFFICE_LIGHT.name,
                        "info_en": """Indicates whether the janitor office provides a window facing the exterior space.""",
                        "info": """Angabe, ob das Hauswart Büro ein Fenster zum Aussenraum hat.""",
                    },
                    {
                        "name_en": "Size Janitor Office",
                        "name": "Grösse Hauswart Büro",
                        "key": CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value,
                        "code": CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.name,
                        "info_en": """Indicates whether the janitor office meets the client's specific size requirements.""",
                        "info": """Angabe, ob das Hauswart Büro den kundenspezifischen Grössenanforderungen entspricht.""",
                    },
                    {
                        "name_en": "WC Janitor Office",
                        "name": "WC Hauswart Büro",
                        "key": CompetitionFeatures.JANITOR_HAS_WC.value,
                        "code": CompetitionFeatures.JANITOR_HAS_WC.name,
                        "info_en": """Indicates whether there is a WC attached to the janitor office.""",
                        "info": """Angabe, ob dem Hauswart Büro ein WC angeschlossen ist.""",
                    },
                    {
                        "name_en": "Closeness of WC to Janitor’s Office",
                        "name": "Nähe WC zu Hauswart Büro",
                        "key": CompetitionFeatures.JANITOR_WC_CLOSENESS.value,
                        "code": CompetitionFeatures.JANITOR_WC_CLOSENESS.name,
                        "info_en": """Indicates whether there is a WC planned close (radius 5m) to the janitor’s office.""",
                        "info": """Angabe, ob in der Nähe (Radius 5 m) jedes Hausmeister Büros ein WC geplant ist.""",
                    },
                ],
            },
            {
                "name_en": "Office/ Guess Room",
                "name": "Büro-/Gästezimmer",
                "key": "guess_room",
                "sub_sections": [
                    {
                        "name_en": "Size office/guest room",
                        "name": "Grösse Büro/Gästezimmer",
                        "key": CompetitionFeatures.GUESS_ROOM_SIZE_REQ.value,
                        "code": CompetitionFeatures.GUESS_ROOM_SIZE_REQ.name,
                        "info_en": """""",
                        "info": """""",
                    },
                ],
            },
            {
                "name_en": "Storage Prams/Bikes",
                "name": "Abstellraum Kinderwagen/Fahrräder",
                "key": "storage_rooms_for_prams_bikes",
                "sub_sections": [
                    {
                        "name_en": "Closeness of Entrance to Storage Prams/Bikes",
                        "name": "Nähe Hauseingang zum Abstellraum für Kinderwagen/Fahrräder",
                        "key": CompetitionFeatures.PRAMS_AND_BIKES_CLOSE_TO_ENTRANCE.value,
                        "code": CompetitionFeatures.PRAMS_AND_BIKES_CLOSE_TO_ENTRANCE.name,
                        "info_en": """Indicates whether there is a storeroom for prams and bikes planned close (radius 7 m) to every housing main entrance.""",
                        "info": """Angabe, ob in der Nähe (Radius 7 m) jedes Hauseingangs ein Abstellraum für Kinderwagen und Fahrräder geplant ist.""",
                    },
                    {
                        "name_en": "Barrier-free Access Storage Room Prams/Bikes",
                        "name": "Barrierefreier Zugang Abstellraum Kinderwagen/Fahrräder",
                        "key": CompetitionFeatures.PRAMS_ROOM_BARRIER_FREE_ACCESS.value,
                        "code": CompetitionFeatures.PRAMS_ROOM_BARRIER_FREE_ACCESS.name,
                        "info_en": """Indicates whether the storerooms for prams and bikes are barrier free accessible (no steps).""",
                        "info": """Angabe, ob die Abstellräume für Kinderwagen und Fahrräder barrierefrei erschliessbar sind (keine Stufen).""",
                    },
                ],
            },
            {
                "name_en": "Bike boxes",
                "name": "Fahrradboxen",
                "key": "bike_boxes",
                "sub_sections": [
                    {
                        "name_en": "Availability Bike Boxes",
                        "name": "Verfügbarkeit Fahrradboxen",
                        "key": CompetitionFeatures.BUILDING_BICYCLE_BOXES_AVAILABLE.value,
                        "code": CompetitionFeatures.BUILDING_BICYCLE_BOXES_AVAILABLE.name,
                        "info_en": """Indicates whether there are bike boxes planned for the project.""",
                        "info": """Angabe, ob für das Projekt Fahrradboxen geplant sind.""",
                    },
                    {
                        "name_en": "Quantity Bike Boxes",
                        "name": "Anzahl Fahrradboxen",
                        "key": CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value,
                        "code": CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.name,
                        "info_en": """Indicates whether the number of bike boxes planned meets the client's specific requirements.""",
                        "info": """Angabe, ob die Anzahl der geplanten Fahrradboxen den kundenspezifischen Anforderungen entspricht.""",
                    },
                    {
                        "name_en": "Size Bike Boxes",
                        "name": "Grösse Fahrradboxen",
                        "key": CompetitionFeatures.BIKE_BOXES_DIMENSIONS.value,
                        "code": CompetitionFeatures.BIKE_BOXES_DIMENSIONS.name,
                        "info_en": """Indicates whether the bike boxes meet the client's specific size requirements.""",
                        "info": """Angabe, ob die Fahrradboxen den kundenspezifischen Grössenanforderungen entsprechen.""",
                    },
                    {
                        "name_en": "Availability Power Supply",
                        "name": "Verfügbarkeit Stromanschluss",
                        "key": CompetitionFeatures.BIKE_BOXES_POWER_SUPPLY.value,
                        "code": CompetitionFeatures.BIKE_BOXES_POWER_SUPPLY.name,
                        "info_en": """Indicates whether the bicycle boxes provide a power supply.""",
                        "info": """Angabe, ob die Fahrradboxen einen Stromanschluss bereitstellen.""",
                    },
                ],
            },
            {
                "name_en": "Disability Accessibility",
                "name": "Behindertengerechtigkeit",
                "key": "handicapped_accessible_building",
                "sub_sections": [
                    {
                        "name_en": "Handicapped Accessible Areas",
                        "name": "Erschliessbarkeit",
                        "key": CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value,
                        "code": CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.name,
                        "info_en": """Percentage of the total area of the project that is accessible to the disabled (1.20 m min. passage width)""",
                        "info": """Prozentualer Anteil der Gesamtfläche des Projekts, welcher behindertengerecht erschliessbar ist.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Size Bathroom",
                        "name": "Grösse Nasszellen",
                        "key": CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value,
                        "code": CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.name,
                        "info_en": """Percentage of all dwellings that offer at least one wet room that meets the required minimum dimensions (Fläche: 4.3 m², Länge: min. 2.35 m, Breite: min. 1.8 m).""",
                        "info": """Prozentualer Anteil der Wohnungen, die mindestens eine Nasszelle bieten, welche die geforderten Mindestabmessungen einhält.""",
                        "unit": "%",
                    },
                    {
                        "name_en": "Size Lift Cabin",
                        "name": "Grösse Aufzugkabine",
                        "key": CompetitionFeatures.BUILDING_MINIMUM_ELEVATOR_DIMENSIONS.value,
                        "code": CompetitionFeatures.BUILDING_MINIMUM_ELEVATOR_DIMENSIONS.name,
                        "info_en": """Indicates whether all elevator cabins in the project meet with the minimum size requirements (length: min. 1.1 m and width: min. 1.4 m).""",
                        "info": """Angabe, ob alle Aufzuganalagen des Projektes die Anforderungen an die Kabinengrösse erfüllen.""",
                    },
                ],
            },
            {
                "name_en": "Car, Two-Wheeler, Bicycle Parking",
                "name": "Auto-, Zweirad-, Fahrrad-Abstellplätze",
                "key": "car_bicycle_bicycle_parking",
                "sub_sections": [
                    {
                        "name_en": "Number of Parking Spaces",
                        "name": "Anzahl Autoabstellplätze",
                        "key": CompetitionFeatures.CAR_PARKING_SPACES.value,
                        "code": CompetitionFeatures.CAR_PARKING_SPACES.name,
                        "info_en": """Indicates whether the number of planned parking spaces corresponds to the number
                         required by law.""",
                        "info": """Angabe, ob die Anzahl geplanter Autoabstellplätze mit der gesetzlich geforderte
                         Anzahl korrespondiert.""",
                    },
                    {
                        "name_en": "Number of Two-Wheeler Parking Spaces",
                        "name": "Anzahl Zweiradabstellplätze",
                        "key": CompetitionFeatures.TWO_WHEELS_PARKING_SPACES.value,
                        "code": CompetitionFeatures.TWO_WHEELS_PARKING_SPACES.name,
                        "info_en": """Indicates whether the number of planned two-wheeler parking spaces corresponds to the number required by law. """,
                        "info": """Angabe, ob die Anzahl geplanter Zweiradabstellplätze mit der gesetzlich geforderten Anzahl korrespondiert. """,
                    },
                    {
                        "name_en": "Number of Bike Parking Spaces",
                        "name": "Anzahl Fahrradabstellplätze",
                        "key": CompetitionFeatures.BIKE_PARKING_SPACES.value,
                        "code": CompetitionFeatures.BIKE_PARKING_SPACES.name,
                        "info_en": """Indicates whether the number of planned bike parking spaces corresponds to the number required by law. """,
                        "info": """Angabe, ob die Anzahl geplanter Fahrradabstellplätze mit der gesetzlich
                         geforderten Anzahl korrespondiert. """,
                    },
                    {
                        "name_en": "Availability 2nd Basement",
                        "name": "Verfügbarkeit 2tes Untergeschoss",
                        "key": CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.value,
                        "code": CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.name,
                        "info_en": """Indicates whether a 2nd basement is planned.""",
                        "info": """Angabe, ob ein 2. Untergeschoss geplant ist.""",
                    },
                ],
            },
            {
                "name_en": "Basement Compartment",
                "name": "Kellerabteil",
                "key": "basement_compartment",
                "sub_sections": [
                    {
                        "name_en": "Availability Basement compartment",
                        "name": "Verfügbarkeit Kellerabteil pro Wohnung",
                        "key": CompetitionFeatures.BASEMENT_COMPARTMENT_AVAILABLE.value,
                        "code": CompetitionFeatures.BASEMENT_COMPARTMENT_AVAILABLE.name,
                        "info_en": """""",
                        "info": """""",
                    },
                    {
                        "name_en": "Basement compartment size requirement",
                        "name": "Grösse Kellerabteil",
                        "key": CompetitionFeatures.BASEMENT_COMPARTMENT_SIZE_REQ.value,
                        "code": CompetitionFeatures.BASEMENT_COMPARTMENT_SIZE_REQ.name,
                        "info_en": """""",
                        "info": """""",
                    },
                ],
            },
        ],
    },
    {
        "name_en": "Environment – Overview",
        "name": "Umgebung – Allgemein",
        "key": "environmental",
        "sub_sections": [
            {
                "name_en": "Environmental Analysis",
                "name": "Umgebung – Analysen",
                "key": "environmental_design",
                "sub_sections": [
                    {
                        "name_en": "Analysis Greenery",
                        "name": "Analyse Grünraum",
                        "key": CompetitionFeatures.ANALYSIS_GREENERY.value,
                        "code": CompetitionFeatures.ANALYSIS_GREENERY.name,
                        "info_en": """This simulation aggregates all elements which are either "trees" or "parks".""",
                        "info": """Die Simulation erfasst alle Elemente, die entweder "Bäume" oder "Parks" sind.""",
                        "unit": "sr",
                    },
                    {
                        "name_en": "Analysis Sky",
                        "name": "Analyse Himmel",
                        "key": CompetitionFeatures.ANALYSIS_SKY.value,
                        "code": CompetitionFeatures.ANALYSIS_SKY.name,
                        "info_en": """This simulation covers all sky areas of the observation angle that are not obscured.""",
                        "info": """Die Simulation erfasst alle Himmelsbereiche des Beobachtungswinkels, die nicht verdeckt sind.""",
                        "unit": "sr",
                    },
                    {
                        "name_en": "Analysis Water",
                        "name": "Analyse Gewässer",
                        "key": CompetitionFeatures.ANALYSIS_WATER.value,
                        "code": CompetitionFeatures.ANALYSIS_WATER.name,
                        "info_en": """The simulation covers all water elements such as river, stream, lake and sea.""",
                        "info": """Die Simulation erfasst alle Wasserelemente wie Fluss, Bach, See und Meer.""",
                        "unit": "sr",
                    },
                    {
                        "name_en": "Analysis Buildings",
                        "name": "Analyse Gebäude",
                        "key": CompetitionFeatures.ANALYSIS_BUILDINGS.value,
                        "code": CompetitionFeatures.ANALYSIS_BUILDINGS.name,
                        "info_en": """The simulation covers all buildings surrounding the site.""",
                        "info": """Die Simulation erfasst alle Gebäude, die das Objekt umgeben.""",
                        "unit": "sr",
                    },
                    {
                        "name_en": "Analysis Railway tracks",
                        "name": "Analyse Gleise",
                        "key": CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value,
                        "code": CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.name,
                        "info_en": """The simulation covers all track elements such as railroad or streetcar rails.""",
                        "info": """Die Simulation erfasst alle Gleiselemente wie Eisenbahn- oder Tram-Schienen.""",
                        "unit": "sr",
                    },
                    {
                        "name_en": "Analysis Streets",
                        "name": "Analyse Strassen",
                        "key": CompetitionFeatures.ANALYSIS_STREETS.value,
                        "code": CompetitionFeatures.ANALYSIS_STREETS.name,
                        "info_en": """The simulation covers the road network open for traffic.""",
                        "info": """Die Simulation erfasst das für Verkehr freigegebene Strassennetz.""",
                        "unit": "sr",
                    },
                ],
            },
        ],
    },
    {
        "name_en": "Architecture – Key Figures",
        "name": "Architektur – Kennzahlen",
        "key": "further_key_figures",
        "sub_sections": [
            {
                "name_en": "Areas",
                "name": "Flächen",
                "key": "areas",
                "sub_sections": [
                    {
                        "name_en": "Yield relevant area",
                        "name": "Ertragsrelevante Fläche",
                        "key": CompetitionFeatures.AGF_W_REDUIT.value,
                        "code": CompetitionFeatures.AGF_W_REDUIT.name,
                        "info_en": """Sum of the yield relevant area (HNF + NNF) for the entire project. """,
                        "info": """Summe der ertragsrelevanten Wohnflächen (HNF + NNF) für das gesamte Projekt.""",
                        "unit": "m²",
                    },
                ],
            },
        ],
    },
]


# HACK This is just to provide a complete list of
# features / scores even though we don't compute them all yet
FAKE_FEATURE_VALUES = {
    leaf_level["key"]: 0.0
    for category in CATEGORIES
    for sub_section in category["sub_sections"]
    for leaf_level in sub_section["sub_sections"]
}


ARCHILYSE_FEATURES = {
    CompetitionFeatures.ANALYSIS_GREENERY.value,
    CompetitionFeatures.ANALYSIS_SKY.value,
    CompetitionFeatures.ANALYSIS_BUILDINGS.value,
    CompetitionFeatures.ANALYSIS_WATER.value,
    CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value,
    CompetitionFeatures.ANALYSIS_STREETS.value,
    CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.value,
    CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER.value,
    CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER.value,
    CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER.value,
    CompetitionFeatures.NOISE_STRUCTURAL.value,
    CompetitionFeatures.NOISE_INSULATED_ROOMS.value,
}

UPLOADED_FEATURES = {
    CompetitionFeatures.DRYING_ROOM_SIZE.value,
    CompetitionFeatures.JANITOR_OFFICE_LIGHT.value,
    CompetitionFeatures.PRAMS_ROOM_BARRIER_FREE_ACCESS.value,
    CompetitionFeatures.BIKE_BOXES_DIMENSIONS.value,
    CompetitionFeatures.BIKE_BOXES_POWER_SUPPLY.value,
    CompetitionFeatures.PRAMS_AND_BIKES_CLOSE_TO_ENTRANCE.value,
    CompetitionFeatures.CAR_PARKING_SPACES.value,
    CompetitionFeatures.TWO_WHEELS_PARKING_SPACES.value,
    CompetitionFeatures.BIKE_PARKING_SPACES.value,
    CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.value,
    CompetitionFeatures.KITCHEN_ELEMENTS_REQUIREMENT.value,
    CompetitionFeatures.ENTRANCE_WARDROBE_ELEMENT_REQUIREMENT.value,
    CompetitionFeatures.BEDROOM_WARDROBE_ELEMENT_REQUIREMENT.value,
    CompetitionFeatures.SINK_SIZES_REQUIREMENT.value,
    CompetitionFeatures.BASEMENT_COMPARTMENT_AVAILABLE.value,
    CompetitionFeatures.BASEMENT_COMPARTMENT_SIZE_REQ.value,
    CompetitionFeatures.GUESS_ROOM_SIZE_REQ.value,
}


RED_FLAGS_FEATURES = {
    CompetitionFeatures.APT_PCT_W_OUTDOOR.value,
    CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value,
    CompetitionFeatures.APT_PCT_W_STORAGE.value,
    CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value,
    CompetitionFeatures.PRAMS_ROOM_BARRIER_FREE_ACCESS.value,
    CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value,
    CompetitionFeatures.BUILDING_MINIMUM_ELEVATOR_DIMENSIONS.value,
    CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.value,
}

DEFAULT_WEIGHTS = {
    "architecture_usage": 0.15,
    "architecture_room_programme": 0.35,
    "further_key_figures": 0.25,
    "environmental": 0.25,
}


class SERVICE_ROOM_TYPES(Enum):
    TOILET = "TOILET"
    BATHROOM = "BATHROOM"  # Includes a room with at least a shower or a bath

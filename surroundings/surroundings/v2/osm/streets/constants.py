from common_utils.constants import SurroundingType

STREET_TYPE_WIDTH = {  # all values in meters
    # national highways
    "motorway": 2 * 3.5,
    "motorway_link": 3.5,
    # express roads
    "trunk": 3.5,
    "trunk_link": 3.5,
    # primary municipal roads
    "primary": 2 * 3,
    "primary_link": 3,
    # secondary municipal roads
    "secondary": 2 * 3,
    "secondary_link": 3,
    # tertiary municipal roads
    "tertiary": 2 * 3,
    "tertiary_link": 3,
    # miscellaneous
    "service": 3.5,
    "residential": 2 * 3.5,
    "living_street": 4,
    "pedestrian": 6,
    "steps": 3,
    "cycleway": 3.5,
    "unknown": 2 * 3,
    "unclassified": 2 * 3,
    "footway": 3.5,
    "path": 3.5,
    "bridleway": 3.5,
    "sidewalk": 3.5,
    "crossing": 3.5,
    "track": 3.5,
    "track_grade1": 3.5,
    "track_grade2": 3.5,
    "track_grade3": 3.5,
    "track_grade4": 3.5,
    "track_grade5": 3.5,
}


STREET_TYPE_MAPPING = {
    "motorway": SurroundingType.HIGHWAY,
    "motorway_link": SurroundingType.HIGHWAY,
    "trunk": SurroundingType.HIGHWAY,
    "trunk_link": SurroundingType.HIGHWAY,
    "primary": SurroundingType.PRIMARY_STREET,
    "primary_link": SurroundingType.PRIMARY_STREET,
    "secondary": SurroundingType.SECONDARY_STREET,
    "secondary_link": SurroundingType.SECONDARY_STREET,
    "tertiary": SurroundingType.TERTIARY_STREET,
    "tertiary_link": SurroundingType.TERTIARY_STREET,
    "unknown": SurroundingType.TERTIARY_STREET,
    "unclassified": SurroundingType.TERTIARY_STREET,
    "service": SurroundingType.TERTIARY_STREET,
    "residential": SurroundingType.TERTIARY_STREET,
    "living_street": SurroundingType.TERTIARY_STREET,
    "pedestrian": SurroundingType.PEDESTRIAN,
    "steps": SurroundingType.PEDESTRIAN,
    "cycleway": SurroundingType.PEDESTRIAN,
    "footway": SurroundingType.PEDESTRIAN,
    "path": SurroundingType.PEDESTRIAN,
    "bridleway": SurroundingType.PEDESTRIAN,
    "sidewalk": SurroundingType.PEDESTRIAN,
    "crossing": SurroundingType.PEDESTRIAN,
    "track": SurroundingType.PEDESTRIAN,
    "track_grade1": SurroundingType.PEDESTRIAN,
    "track_grade2": SurroundingType.PEDESTRIAN,
    "track_grade3": SurroundingType.PEDESTRIAN,
    "track_grade4": SurroundingType.PEDESTRIAN,
    "track_grade5": SurroundingType.PEDESTRIAN,
}

from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, SurroundingType
from surroundings.v2.osm.railways import OSMNoisyRailwayGeometryProvider
from surroundings.v2.osm.streets import OSMNoisyStreetsGeometryProvider

GENERIC_NOISE_LEVELS_BY_TYPE_AND_TIME: dict[
    NOISE_SOURCE_TYPE, dict[str | SurroundingType, dict[NOISE_TIME_TYPE, float]]
] = {
    NOISE_SOURCE_TYPE.TRAFFIC: {
        SurroundingType.HIGHWAY: {
            NOISE_TIME_TYPE.DAY: 75,
            NOISE_TIME_TYPE.NIGHT: 70,
        },
        SurroundingType.PRIMARY_STREET: {
            NOISE_TIME_TYPE.DAY: 70,
            NOISE_TIME_TYPE.NIGHT: 65,
        },
        SurroundingType.SECONDARY_STREET: {
            NOISE_TIME_TYPE.DAY: 65,
            NOISE_TIME_TYPE.NIGHT: 60,
        },
        SurroundingType.TERTIARY_STREET: {
            NOISE_TIME_TYPE.DAY: 60,
            NOISE_TIME_TYPE.NIGHT: 55,
        },
    },
    NOISE_SOURCE_TYPE.TRAIN: {
        "rail": {
            NOISE_TIME_TYPE.DAY: 75,
            NOISE_TIME_TYPE.NIGHT: 70,
        }
    },
}

GENERIC_NOISE_PROVIDERS = {
    NOISE_SOURCE_TYPE.TRAFFIC: OSMNoisyStreetsGeometryProvider,
    NOISE_SOURCE_TYPE.TRAIN: OSMNoisyRailwayGeometryProvider,
}

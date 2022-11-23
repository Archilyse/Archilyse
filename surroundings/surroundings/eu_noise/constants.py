from enum import auto

from common_utils.classes import AutoNameEnum
from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, REGION

DATASET_EPSG_REGION = REGION.EUROPE


class DATASET_CONTENT_TYPE(AutoNameEnum):
    SOURCE_GEOMETRIES = auto()
    NOISE_LEVELS = auto()


DATASET_FILENAMES = {
    DATASET_CONTENT_TYPE.SOURCE_GEOMETRIES: {
        REGION.DE_HAMBURG: {
            NOISE_SOURCE_TYPE.TRAIN: [
                "DE_HH/DE_f_Mrail_Source.{}",
                "DE_SH/DE_o_Mrail_Source.{}",
                "DE_DB/DE_q_Mrail_Source.{}",
            ],
            NOISE_SOURCE_TYPE.TRAFFIC: [
                "DE_HH/DE_f_Mroad_Source.{}",
                "DE_SH/DE_o_Mroad_Source.{}",
            ],
        },
    },
    DATASET_CONTENT_TYPE.NOISE_LEVELS: {
        REGION.DE_HAMBURG: {
            NOISE_SOURCE_TYPE.TRAIN: {
                NOISE_TIME_TYPE.DAY: (
                    "DE_HH/DE_f_ag1_Aggrail_Lden.{}",
                    "DE_SH/DE_f_ag1_Aggrail_Lden.{}",
                    "DE_DB/DE_f_ag1_Aggrail_Lden.{}",
                ),
                NOISE_TIME_TYPE.NIGHT: (
                    "DE_HH/DE_f_ag1_Aggrail_Lnight.{}",
                    "DE_SH/DE_f_ag1_Aggrail_Lnight.{}",
                    "DE_DB/DE_f_ag1_Aggrail_Lnight.{}",
                ),
            },
            NOISE_SOURCE_TYPE.TRAFFIC: {
                NOISE_TIME_TYPE.DAY: (
                    "DE_HH/DE_f_ag1_Aggroad_Lden.{}",
                    "DE_SH/DE_f_ag1_Aggroad_Lden.{}",
                ),
                NOISE_TIME_TYPE.NIGHT: (
                    "DE_HH/DE_f_ag1_Aggroad_Lnight.{}",
                    "DE_SH/DE_f_ag1_Aggroad_Lnight.{}",
                ),
            },
        }
    },
}

from typing import Any, Dict, List, Literal, Tuple, TypedDict, get_args

from common_utils.constants import NOISE_SURROUNDING_TYPE

LocationTuple = Tuple[float, float, float]

FloorNumber = int
AreaID = int
UnitID = int
PLanID = int
Distance = float


class NoiseAreaResultsType(TypedDict, total=False):
    observation_points: List[LocationTuple]
    noise_TRAFFIC_DAY: List[float]
    noise_TRAFFIC_NIGHT: List[float]
    noise_TRAIN_DAY: List[float]
    noise_TRAIN_NIGHT: List[float]


NoiseTypeName = Literal[
    "noise_TRAFFIC_DAY", "noise_TRAFFIC_NIGHT", "noise_TRAIN_DAY", "noise_TRAIN_NIGHT"
]

assert set(get_args(NoiseTypeName)) == {
    member.value for member in NOISE_SURROUNDING_TYPE
}

SimulationResults = Dict[int, Any]

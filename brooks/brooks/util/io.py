import json
from abc import abstractmethod
from enum import Enum
from typing import Dict, Iterable, List, Union
from uuid import UUID

from numpy import array, ndarray, round
from shapely.geometry import MultiPolygon, Point, Polygon, mapping


class BrooksSerializable:
    def asdict(self) -> Dict:
        return BrooksJSONEncoder().default(self)

    @property
    @abstractmethod
    def __serializable_fields__(self) -> Iterable[str]:
        raise NotImplementedError()


class BrooksJSONEncoder(json.JSONEncoder):
    @staticmethod
    def map_ndarray(ar: ndarray) -> List:
        return round(array(ar), 2).tolist()

    @classmethod
    def map_point(cls, point: Point) -> Dict:
        mapped = mapping(point)
        mapped["coordinates"] = cls.map_ndarray(mapped["coordinates"])
        return cls.default(mapped)

    @classmethod
    def map_geometry(cls, geom: Union[Point, Polygon, MultiPolygon]) -> Dict:
        return cls.default(mapping(geom))

    @classmethod
    def map_brooks_serializable(cls, obj: BrooksSerializable) -> Dict:
        return {k: cls.default(getattr(obj, k)) for k in obj.__serializable_fields__}

    @classmethod
    def default(cls, obj):
        if isinstance(obj, bool):
            return int(obj)

        if isinstance(obj, (int, float, str)) or obj is None:
            return obj

        if isinstance(obj, (Enum, UUID)):
            return str(obj)

        if isinstance(obj, BrooksSerializable):
            return cls.map_brooks_serializable(obj)

        if isinstance(obj, ndarray):
            return cls.map_ndarray(obj)

        if isinstance(obj, (Polygon, MultiPolygon)):
            return cls.map_geometry(obj)

        if isinstance(obj, Point):
            return cls.map_point(obj)

        if isinstance(obj, dict):
            return {cls.default(k): cls.default(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple, set)):
            return [cls.default(k) for k in obj]

        return json.JSONEncoder.default(cls, obj)  # TypeError

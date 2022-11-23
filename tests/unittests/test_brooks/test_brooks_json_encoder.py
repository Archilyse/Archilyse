from collections import Counter

import deepdiff
from numpy import array
from shapely.geometry import MultiPolygon, Point, Polygon

from brooks.models import SimArea
from brooks.models.violation import Violation, ViolationType
from brooks.util.io import BrooksJSONEncoder, BrooksSerializable
from handlers import PlanLayoutHandler, ReactPlannerHandler


class OtherDummySerializable(BrooksSerializable):
    __serializable_fields__ = ["some_test_field"]

    @property
    def some_test_field(self):
        return None


class DummySerializable(BrooksSerializable):
    __serializable_fields__ = [
        "ndarray",
        "polygon",
        "multipolygon",
        "point",
        "violation",
        "tuple",
        "list",
        "set",
        "dict",
        "other_brooks_serializable",
    ]

    @property
    def ndarray(self):
        return array([[1.1111, 1.2222, 1], [2.5545, 100000, 0]])

    @property
    def polygon(self):
        return Polygon([(1, 0), (1, 1), (0, 1), (0, 0)])

    @property
    def multipolygon(self):
        return MultiPolygon([self.polygon, self.polygon])

    @property
    def point(self):
        return Point(1.2222, 5.555)

    @property
    def violation(self):
        area = SimArea(self.polygon)
        return Violation(
            violation_type=ViolationType.AREA_NOT_EVALUATED,
            position=area.footprint.centroid,
        )

    @property
    def other_brooks_serializable(self):
        return OtherDummySerializable()

    @property
    def tuple(self):
        return (self.point,)

    @property
    def list(self):
        return [self.point]

    @property
    def set(self):
        return {self.other_brooks_serializable}

    @property
    def dict(self):
        return dict(test=self.point)


def test_encode_ndarray():
    obj = DummySerializable().ndarray
    expected_result = [[1.11, 1.22, 1.0], [2.55, 100000.0, 0.0]]
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_polygon():
    obj = DummySerializable().polygon
    expected_result = dict(
        coordinates=[[[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]]],
        type="Polygon",
    )
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_multipolygon():
    obj = DummySerializable().multipolygon
    expected_result = dict(
        type="MultiPolygon",
        coordinates=[
            [[[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]]],
            [[[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]]],
        ],
    )
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_point():
    obj = DummySerializable().point
    expected_result = dict(coordinates=[1.22, 5.56], type="Point")
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_violation():
    obj = DummySerializable().violation
    expected_result = dict(
        type="AREA_NOT_EVALUATED",
        position=dict(type="Point", coordinates=[0.5, 0.5]),
        text="Area features were not included in the basic features simulation",
        object_id=None,
        human_id=None,
        is_blocking=1,
    )
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_other_brooks_serializable():
    obj = DummySerializable().other_brooks_serializable
    expected_result = dict(some_test_field=None)
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_tuple_list():
    expected_element = dict(coordinates=[1.22, 5.56], type="Point")
    dummy = DummySerializable()
    for obj in [dummy.tuple, dummy.list]:
        expected_result = [expected_element]
        actual_result = BrooksJSONEncoder().default(obj)
        assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_set():
    obj = DummySerializable().set
    expected_result = [dict(some_test_field=None)]
    actual_result = BrooksJSONEncoder().default(obj)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_dict():
    expected_element = dict(coordinates=[1.22, 5.56], type="Point")
    expected_result = dict(test=expected_element)
    actual_result = BrooksJSONEncoder().default(DummySerializable().dict)
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_encode_brooks_serializable():
    expected_result = {
        "ndarray": [[1.11, 1.22, 1.0], [2.55, 100000.0, 0.0]],
        "polygon": {
            "type": "Polygon",
            "coordinates": [
                [[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]]
            ],
        },
        "multipolygon": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]]],
                [[[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]]],
            ],
        },
        "point": {"type": "Point", "coordinates": [1.22, 5.56]},
        "violation": {
            "type": "AREA_NOT_EVALUATED",
            "position": {"type": "Point", "coordinates": [0.5, 0.5]},
            "text": "Area features were not included in the basic features simulation",
            "object_id": None,
            "human_id": None,
            "is_blocking": 1,
        },
        "tuple": [{"type": "Point", "coordinates": [1.22, 5.56]}],
        "list": [{"type": "Point", "coordinates": [1.22, 5.56]}],
        "set": [{"some_test_field": None}],
        "dict": {"test": {"type": "Point", "coordinates": [1.22, 5.56]}},
        "other_brooks_serializable": {"some_test_field": None},
    }
    actual_result = BrooksJSONEncoder().default(DummySerializable())
    assert not deepdiff.DeepDiff(actual_result, expected_result)


def test_regression_encode_layout(
    mocker,
    default_plan_info,
    annotations_plan_5690,
):
    mocker.patch.object(
        ReactPlannerHandler,
        "project",
        return_value={"data": annotations_plan_5690},
    )
    layout = PlanLayoutHandler(plan_id=-999, plan_info=default_plan_info).get_layout(
        validate=True
    )

    spy_encode = mocker.spy(BrooksJSONEncoder, "default")
    layout.asdict()

    expected_calls = Counter(
        {
            "float": 2818,
            "tuple": 1463,
            "str": 1159,
            "dict": 348,
            "list": 168,
            "Point": 166,
            "Polygon": 160,
            "set": 115,
            "NoneType": 75,
            "SimSeparator": 75,
            "SeparatorType": 75,
            "SimArea": 23,
            "AreaType": 23,
            "SimOpening": 23,
            "OpeningType": 23,
            "SimFeature": 22,
            "FeatureType": 22,
            "SimSpace": 17,
            "SpaceType": 17,
            "SpatialEntityViolation": 6,
            "bool": 6,
            "SimLayout": 1,
            "LayoutType": 1,
            "UUID": 1,
        }
    )

    actual_calls = Counter(
        [obj[0][0].__class__.__name__ for obj in spy_encode.call_args_list]
    )
    assert actual_calls == expected_calls

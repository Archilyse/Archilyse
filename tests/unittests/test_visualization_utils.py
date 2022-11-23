import pytest
from shapely import wkt
from shapely.affinity import rotate
from shapely.geometry import box

from brooks.util.geometry_ops import get_center_line_from_rectangle
from brooks.visualization.utils import RECTANGLE_SIDE, ScaleRectangle, get_visual_center


@pytest.mark.parametrize(
    "pol, is_centroid",
    [
        (
            "POLYGON ((3260.7853801968230982 -1091.0919806634749420, 3266.1429364014670682 "
            "-1091.0919806634749420, 3266.1429364014670682 -1091.0966210664869322, "
            "3263.4683768473378223 -1091.0966210664869322, 3260.7938172932081216 "
            "-1091.0966210664869322, 3260.7938172932081216 -1093.6568579645959289, "
            "3260.7853801968230982 -1093.6568579645959289, 3260.7853801968230982 -1091.0919806634749420))",
            True,
        ),
        (
            "POLYGON ((3260.7853801968230982 -1091.0919806634749420, 3266.1429364014670682 "
            "-1091.0919806634749420, 3266.1429364014670682 -1093.6652950609814070, "
            "3265.9404460882205967 -1093.6652950609814070, 3265.9404460882205967 "
            "-1093.7834144103749168, 3264.1939671364707465 -1093.7834144103749168, "
            "3264.1939671364707465 -1093.6568579645959289, 3262.9284026786804134 "
            "-1093.6568579645959289, 3262.9284026786804134 -1093.7665402176044154, "
            "3261.2156721124715659 -1093.7665402176044154, 3261.2156721124715659 "
            "-1093.6568579645959289, 3260.7853801968230982 -1093.6568579645959289, "
            "3260.7853801968230982 -1091.0919806634749420))",
            False,
        ),
    ],
)
def test_visual_center(pol, is_centroid):
    pol = wkt.loads(pol)
    visual_center = get_visual_center(pol)
    assert (
        visual_center == pol.centroid if is_centroid else visual_center != pol.centroid
    )


class TestScaleRectangle:
    @pytest.mark.parametrize(
        "side",
        [RECTANGLE_SIDE.LONG_SIDE, RECTANGLE_SIDE.SHORT_SIDE, RECTANGLE_SIDE.BOTH_SIDE],
    )
    @pytest.mark.parametrize("angle", [i for i in range(0, 360, 10)])
    def test_round_rectangle(self, side, angle):
        rectangle = rotate(geom=box(0, 0, 2.011, 1.073), angle=angle)

        rounded_rectangle = ScaleRectangle.round(rectangle=rectangle, applied_to=side)
        assert rectangle.symmetric_difference(rounded_rectangle).area < 0.01
        long, short = get_center_line_from_rectangle(
            polygon=rounded_rectangle, only_longest=False
        )

        if side == RECTANGLE_SIDE.LONG_SIDE:
            assert long.length == pytest.approx(expected=2.01, abs=1e-7)
            assert short.length == pytest.approx(expected=1.073, abs=1e-7)
        elif side == RECTANGLE_SIDE.SHORT_SIDE:
            assert long.length == pytest.approx(expected=2.011, abs=1e-7)
            assert short.length == pytest.approx(expected=1.07, abs=1e-7)

        else:
            assert long.length == pytest.approx(expected=2.01, abs=1e-7)
            assert short.length == pytest.approx(expected=1.07, abs=1e-7)

    @pytest.mark.parametrize(
        "side",
        [RECTANGLE_SIDE.LONG_SIDE, RECTANGLE_SIDE.SHORT_SIDE, RECTANGLE_SIDE.BOTH_SIDE],
    )
    @pytest.mark.parametrize("angle", [i for i in range(0, 360, 10)])
    def test_extend_rectangle(self, side, angle):
        rectangle = box(0, 0, 2, 1)
        scaled_rectangle = ScaleRectangle.extend_sides(
            rectangle=rectangle, applied_to=side, extension_value=0.1
        )
        long, short = get_center_line_from_rectangle(
            polygon=scaled_rectangle, only_longest=False
        )
        if side == RECTANGLE_SIDE.LONG_SIDE:
            assert long.length == pytest.approx(expected=2.1, abs=1e-7)
            assert short.length == pytest.approx(expected=1, abs=1e-7)
        elif side == RECTANGLE_SIDE.SHORT_SIDE:
            assert long.length == pytest.approx(expected=2, abs=1e-7)
            assert short.length == pytest.approx(expected=1.1, abs=1e-7)

        else:
            assert long.length == pytest.approx(expected=2.1, abs=1e-7)
            assert short.length == pytest.approx(expected=1.1, abs=1e-7)

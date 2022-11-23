"""
The workflow of matplotlib uses a strategy pattern to render a figure and
works as follows when a figure is saved:

1. The backend is chosen based on the file format specified in
   the savefig command. This backend can be defined for a format
   using `matplotlib.register_backend` or dynamically using
   the `matplotlib.use` command.

   For instance:
       `register_backend("dxf", "brooks.visualization.backends.dxf", "DXF Format")`

2. The variable `{backend_module}.FigureCanvas` is used to determine the
   FigureCanvasBase subclass.

   When a figure is saved, it instantiates the canvas. The canvas instantiates
   the renderer and calls `figure.draw(renderer)`.

3. The figure.draw command iterates over the paths, texts and images of itself
   and invokes `renderer.draw_path`, `renderer.draw_text`, etc., respectively.

   In order to provide styling information for each path, the figure uses
   `renderer.new_gc()` to create a GraphicsContextDXF object. This class
   provides color, line styles, etc. to the renderer for the particular element
   being drawn. Each context is passed to the respective render.draw_xxx command.

4. In our case the actual drawing to DXF is handled by the graphics context itself,
   following the example set by the cairo backend implementation. The alternative
   would be to do it like the PS renderer and handle everything in the renderer itself.
   The decision was made in order to take advantage that we have one stateful context
   for each object already which makes drawing paths etc. easier
   (one context -> one style, one context -> one drawn element).

DXF layers and groups are handled using the artists' gid attribute
(`artist.set_gid((layer, group))`) and passed to the graphics context upon its
initialization in the renderer.new_gc() method. The graphics context then sets the
proper dxf layer and dxf group upon creating the dxf entities.
"""
import io
from itertools import takewhile
from typing import Dict, List, Optional, Set, Tuple, Union

import ezdxf
from ezdxf import new, units
from ezdxf.document import Drawing
from ezdxf.entities import Hatch, Polyline, Spline
from ezdxf.layouts import Layout
from ezdxf.math import Matrix44, bspline
from matplotlib.backend_bases import (
    FigureCanvasBase,
    FigureManagerBase,
    GraphicsContextBase,
    RendererBase,
)
from matplotlib.font_manager import FontProperties
from matplotlib.image import AxesImage
from matplotlib.path import Path
from matplotlib.text import Text
from matplotlib.transforms import Affine2D, CompositeGenericTransform
from numpy import array

DXF_VERSION = "AC1032"  # must be AC1032 for autocad compatibility


class RendererDXF(RendererBase):
    def __init__(self, scale: float):
        super().__init__()
        self.dxf_drawing = new(dxfversion=DXF_VERSION)
        self.dxf_layout = self.dxf_drawing.modelspace()
        self.dxf_drawing.header[
            "$INSUNITS"
        ] = units.M  # doesn't seem to produce any effect in the document
        self.scale = scale
        self._groups: List[Tuple[str, Union[Tuple[str, str], Tuple[None, None]]]] = []

    def draw_path(
        self,
        gc: GraphicsContextBase,  # actually GraphicsContextDXF
        path: Path,
        transform: CompositeGenericTransform,
        rgbFace: Optional[Tuple] = None,
    ):
        gc.dxf_path(path=path, transform=transform, rgbaFace=rgbFace)

    def draw_image(self, gc: GraphicsContextBase, x: float, y: float, im: AxesImage):
        pass

    def draw_text(
        self,
        gc: GraphicsContextBase,
        x: float,
        y: float,
        s: str,
        prop: FontProperties,
        angle: float,
        ismath: Optional[bool] = False,
        mtext: Text = None,
    ):
        fontsize = self.points_to_pixels(prop.get_size_in_points()) * 0.9

        if self.flipy():
            _, height = self.get_canvas_width_height()
            y = height - y

        gc.dxf_text(x=x, y=y, text=s, fontsize=fontsize, angle=angle, prop=prop)

    def flipy(self) -> bool:
        return True

    def new_gc(self) -> GraphicsContextBase:
        return GraphicsContextDXF(
            dxf_drawing=self.dxf_drawing,
            dxf_layout=self.dxf_layout,
            dxf_layer=self.current_dxf_layer,
            dxf_group=self.current_dxf_group,
            scale=self.scale,
        )

    def open_group(
        self,
        s: str,
        gid: Union[Tuple[str, str], Tuple[None, None]] = None,
    ):
        # `gid` is a tuple (layer, group)
        if gid is None:
            gid = (None, None)
        # the label `s`is ignored since it is used for matplotlib internal usage
        self._groups.append((s, gid))

    def close_group(self, s: str):
        closed_label, _ = self._groups.pop()

        if closed_label != s:
            raise ValueError("Inconsistent matplotlib group stack.")

    @property
    def current_dxf_layer(self):
        _, (current_layer, _) = self._groups[-1]
        return current_layer if current_layer else None

    @property
    def current_dxf_group(self):
        _, (_, current_group) = self._groups[-1]
        return current_group if current_group else None


class GraphicsContextDXF(GraphicsContextBase):
    """
    Encapsulates all the styling of elements, each path / text / image has it's own
    GraphicsContextDXF object. The base class provides access to get_linewidth() etc.
    """

    # hatch patterns: https://ezdxf.readthedocs.io/en/master/tutorials/hatch.html#predefined-hatch-pattern
    _HATCH_STYLES = {
        "////": {"name": "ANSI31"},
        "//": {"name": "ANSI32"},
        "/.": {"name": "ANSI33"},
    }

    def __init__(
        self,
        dxf_drawing: Drawing,
        dxf_layout: Layout,
        dxf_layer: str,
        dxf_group: str,
        scale: float,
    ):
        super().__init__()
        self.dxf_drawing = dxf_drawing
        self.dxf_layout = dxf_layout
        self.dxf_layer = dxf_layer
        self.dxf_group = dxf_group

        self.dxf_entities: Set[Union[Polyline, Spline, Hatch]] = set()
        self.scale = scale

    @property
    def path_color(self) -> Tuple[int, int, int]:
        rgb_with_alpha = self.get_rgb()
        return (
            int(rgb_with_alpha[0] * 255),
            int(rgb_with_alpha[1] * 255),
            int(rgb_with_alpha[2] * 255),
        )

    # DXF PATH OPERATIONS

    def _draw_curved_path(self, segments):
        if self.has_fill or self.get_hatch():
            self._path_hatch_edge = self._path_hatch.paths.add_edge_path()

        for points, code in segments:
            if code == Path.MOVETO:
                self._dxf_path_move_to(points)

            elif code == Path.CLOSEPOLY:
                self._dxf_path_closepoly(points)

            elif code == Path.LINETO:
                self._dxf_path_line_to(points)

            elif code == Path.CURVE3:
                ctrl, nxt = points.reshape(2, 2)
                self._dxf_path_curve3_to(ctrl, nxt)

            elif code == Path.CURVE4:
                ctrl1, ctrl2, nxt = points.reshape(3, 2)
                self._dxf_path_curve4_to(ctrl1, ctrl2, nxt)
            else:
                raise ValueError("Unknown path segment type.")

    def _draw_polygon_path(self, segments, is_hole: bool = False):
        points = [
            point if code != Path.CLOSEPOLY else segments[0][0]
            for point, code in segments
        ]
        if self.has_stroke:
            dxfattribs = {"layer": self.dxf_layer} if self.dxf_layer else {}

            # NOTE: Last vertex is closepoly code
            polyline = self.dxf_layout.add_polyline2d(
                points=points, dxfattribs=dxfattribs
            )
            polyline.rgb = self.path_color
            self.dxf_entities.add(polyline)

        if self.has_fill or self.get_hatch():
            self._path_hatch.paths.add_polyline_path(
                points,
                is_closed=True,
                flags=ezdxf.const.BOUNDARY_PATH_EXTERNAL
                if not is_hole
                else ezdxf.const.BOUNDARY_PATH_OUTERMOST,
            )

    def _new_path(self, rgbaFace: Tuple, is_nested: bool = False):
        self._rgbaFace = rgbaFace
        self._path_start = None

        if self.has_fill or self.get_hatch():
            dxfattribs = {"layer": self.dxf_layer} if self.dxf_layer else {}

            if is_nested:
                dxfattribs["hatch_style"] = ezdxf.const.HATCH_STYLE_NESTED
            self._path_hatch = self.dxf_layout.add_hatch(dxfattribs=dxfattribs)

            # style hatch
            if hatch_style := self.get_hatch():
                self._path_hatch.set_pattern_fill(
                    **self._HATCH_STYLES[hatch_style], scale=self.scale
                )
                if self.has_fill:
                    self._path_hatch.bgcolor = [
                        int(255 * x) for x in self._rgbaFace[:-1]
                    ]
            else:
                # XXX: Librecad uses 0 to 1 range for rgb, autocad and reference use
                #      0 to 255.
                self._path_hatch.set_solid_fill(
                    style=0,
                    rgb=(
                        int(255 * self._rgbaFace[0]),
                        int(255 * self._rgbaFace[1]),
                        int(255 * self._rgbaFace[2]),
                    ),
                )

            self.dxf_entities.add(self._path_hatch)

    def dxf_path(
        self, path: Path, transform: CompositeGenericTransform, rgbaFace: Tuple
    ):
        # Scale the elements to be in meters
        transform += Affine2D().scale(self.scale)
        path = path.transformed(transform=transform)
        segments = self._get_path_segments(path=path)

        # NOTE: We split the path by its MOVETO operations because a poly-path is not
        #       supported by DXF.
        i = 0
        is_hole = False
        self._new_path(rgbaFace=rgbaFace, is_nested=True)
        while i < len(segments):
            sub_segments = [
                segments[i],
                *takewhile(lambda s: s[1] != Path.MOVETO, segments[i + 1 :]),
            ]
            i += len(sub_segments)

            if codes := {code for _, code in sub_segments}:
                if Path.CURVE3 in codes or Path.CURVE4 in codes:
                    self._draw_curved_path(segments=sub_segments)
                else:
                    self._draw_polygon_path(segments=sub_segments, is_hole=is_hole)

            # first polygon is not a hole, others are
            is_hole = True

        if self.dxf_group:
            if self.dxf_group not in self.dxf_drawing.groups:
                self.dxf_drawing.groups.new(name=self.dxf_group)

            self.dxf_drawing.groups.get(self.dxf_group).extend(self.dxf_entities)

        if self.dxf_layer and self.dxf_layer not in self.dxf_drawing.layers:
            self.dxf_drawing.layers.new(name=self.dxf_layer)

    @staticmethod
    def _get_path_segments(path: Path):
        """
        We need to reduce the simplify threshold here as the default one is 0.1
        which is too high for values in meters. An alternative is to set the keyword simplify to False
        in the iter_segments call
        """
        path.simplify_threshold = 0.001
        path_segments = list(path.iter_segments(simplify=None))
        return path_segments

    def _dxf_path_move_to(self, next_vertex: array):
        self._path_current = next_vertex

        if self._path_start is None:
            self._path_start = self._path_current

    def _dxf_path_line_to(self, next_vertex: array):
        if self.has_stroke:
            dxfattribs = {"layer": self.dxf_layer} if self.dxf_layer else {}
            self.dxf_entities.add(
                self.dxf_layout.add_polyline2d(
                    points=(self._path_current, next_vertex), dxfattribs=dxfattribs
                )
            )

        if self.has_fill or self.get_hatch():
            self._path_hatch_edge.add_line(
                start=self._path_current,
                end=next_vertex,
            )

        self._path_current = next_vertex

    def _dxf_path_curve4_to(self, ctrl1: array, ctrl2: array, next_vertex: array):
        control_points = (self._path_current, ctrl1, ctrl2, next_vertex)

        if self.has_stroke:
            dxfattribs = {"layer": self.dxf_layer} if self.dxf_layer else {}
            spline = self.dxf_layout.add_open_spline(
                control_points=((*p, 0) for p in control_points),  # has to be 3d
                knots=bspline.open_uniform_knot_vector(count=4, order=4),
                dxfattribs=dxfattribs,
            )
            self.dxf_entities.add(spline)

        if self.has_fill:
            self._path_hatch_edge.add_spline(
                control_points=((*p, 0) for p in control_points),
                knot_values=(0, 0, 0, 0, 1, 1, 1, 1),
            )

        self._path_current = next_vertex

    def _dxf_path_curve3_to(self, ctrl_vertex: array, next_vertex: array):
        # we convert the order 3 spline to an order 4 spline
        ctrl1, ctrl2 = (
            self._path_current / 3 + ctrl_vertex * 2 / 3,
            ctrl_vertex * 2 / 3 + next_vertex / 3,
        )
        self._dxf_path_curve4_to(ctrl1=ctrl1, ctrl2=ctrl2, next_vertex=next_vertex)

    def _dxf_path_closepoly(self, next_vertex: array):
        self._dxf_path_line_to(next_vertex=self._path_start)

    # DXF TEXT OPERATIONS

    def dxf_text(
        self,
        x: float,
        y: float,
        text: str,
        fontsize: int,
        prop: FontProperties,
        angle: float,
    ):
        dxfattribs: Dict = {
            "height": fontsize,
            "rotation": angle,
        }
        if self.dxf_layer:
            dxfattribs["layer"] = self.dxf_layer
        dxf_text = self.dxf_layout.add_text(text, dxfattribs=dxfattribs).set_pos(
            (x, y), align="BOTTOM_LEFT"
        )
        # Scale fonts in meters as with the polygons
        dxf_text.transform(Matrix44.scale(self.scale))

        self.dxf_entities.add(dxf_text)

    # STYLE PROPERTIES

    @property
    def has_stroke(self):
        line_width = self.get_linewidth()
        line_alpha = (
            self.get_alpha()
            if self.get_forced_alpha() or len(self.get_rgb()) == 3
            else self.get_rgb()[3]
        )
        return line_width > 0 and line_alpha > 0

    @property
    def has_fill(self):
        return self._rgbaFace is not None and self._rgbaFace[3] > 0


class FigureCanvasDXF(FigureCanvasBase):
    def draw(self, scale: float):
        """Draw the figure using the renderer."""
        renderer = RendererDXF(scale=scale)
        self.figure.draw(renderer)

    filetypes = {**FigureCanvasBase.filetypes, "dxf": "DXF file format"}

    def print_dxf(self, file: io.StringIO, *args, **kwargs):
        renderer = RendererDXF(scale=kwargs["dxf_scale_factor"])
        self.figure.draw(renderer)

        renderer.dxf_drawing.write(stream=file)

    def get_default_filetype(self) -> str:
        return "dxf"


class FigureManagerDXF(FigureManagerBase):
    pass


FigureCanvas = FigureCanvasDXF
FigureManager = FigureManagerDXF

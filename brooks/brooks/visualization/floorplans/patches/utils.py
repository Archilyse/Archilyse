import numpy as np
from matplotlib.path import Path


def _ensure_path_unclosed(vertices: np.array):
    if all(vertices[0] == vertices[-1]):
        vertices = vertices[:-1]

    return vertices


def _iter_vertex_triplets(vertices: np.array):
    n = len(vertices)
    for i in range(n):
        yield vertices[i], vertices[(i + 1) % n], vertices[(i + 2) % n]


def make_rounded_path(patch, radius: float, buffer: float = 0) -> Path:
    vertices = _ensure_path_unclosed(vertices=patch.get_verts())

    path = []
    for i, (p1, p2, p3) in enumerate(_iter_vertex_triplets(vertices=vertices)):
        vec1, vec2 = p2 - p1, p3 - p2
        lvec1, lvec2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        vec1 /= lvec1
        vec2 /= lvec2

        p2 = p2 - vec1 * buffer + vec2 * buffer

        if i == 0:
            path = [(p2 - (lvec1 - radius - 2 * buffer) * vec1, Path.MOVETO)]

        path += [
            (p2 - radius * vec1, Path.LINETO),
            (p2, Path.CURVE3),
            (p2 + radius * vec2, Path.CURVE3),
        ]

    path_vertices, path_codes = zip(*path)
    return Path(path_vertices, path_codes)


def make_only_corners_path(patch, radius: float) -> Path:
    vertices = _ensure_path_unclosed(patch.get_verts())

    path = []
    for i, (p1, p2, p3) in enumerate(_iter_vertex_triplets(vertices=vertices)):
        vec1, vec2 = p2 - p1, p3 - p2
        vec1 /= np.linalg.norm(vec1)
        vec2 /= np.linalg.norm(vec2)

        if i == 0:
            path = [(p2 - radius * vec1, Path.MOVETO)]

        path += [
            (p2 - radius * vec1, Path.MOVETO),
            (p2, Path.LINETO),
            (p2 + radius * vec2, Path.LINETO),
        ]

    path_vertices, path_codes = zip(*path)
    return Path(path_vertices, path_codes, closed=False)

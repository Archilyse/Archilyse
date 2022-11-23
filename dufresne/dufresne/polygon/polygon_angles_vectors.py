import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from dufresne.points import get_points


def get_polygon_normed_vectors(polygon: Polygon):
    """calculate the interior angles of a polygon

    convention is counter-clockwise and the vectors start from the given
    point to the next.

    :param polygon:  a shapely polygon

    :returns angles: numpy array of the angles
    :returns vectors: numpy array of the vectors
    :returns normed_vectors: numpy array of the nomralize vectors
    """
    polygon = orient(polygon)
    points = np.array(get_points(polygon)[0])
    vectors = np.zeros_like(points)
    normed_vectors = np.zeros_like(vectors)
    length = len(points)
    for i in range(length - 1):
        vectors[i] = points[i + 1] - points[i]
        normed_vectors[i] = vectors[i] / np.linalg.norm(vectors[i])
    # boundary
    normed_vectors[-1] = normed_vectors[0]
    return normed_vectors

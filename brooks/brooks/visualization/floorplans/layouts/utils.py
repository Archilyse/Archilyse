def align_and_fit_axis(axis, alignment="C", autoscale=True):
    """Adjusts the position and limits of an axis such that it
    has an equal aspect ratio and is aligned according to `alignment`.

    Alignment can take the following values
    'NW'  'N' 'NE'
     'W'  'C'  'E'
    'SW'  'S' 'SE'
    e.g. SE for bottom-right alignemnt (south-east)
    """
    axis.set_aspect("equal")
    axis.set_anchor(alignment)

    if autoscale:
        axis.autoscale()


def cm_to_inch(cm: float) -> float:
    return 25 / 64 * cm

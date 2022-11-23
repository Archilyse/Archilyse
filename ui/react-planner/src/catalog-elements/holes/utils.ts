type DoorSweepingPoints = {
  angle_point: [number, number];
  closed_point: [number, number];
  opened_point: [number, number];
};

export function getArcSvgPathFromSweepingPoints(doorPoints: DoorSweepingPoints, holeLength: number) {
  /**
   * Parametrized the SVG path string as in http://xahlee.info/js/svg_path_ellipse_arc.html
   */
  const ellipseRadius = `${holeLength},${holeLength}`;
  const rotation = 0;
  const largeArcFlag = 0;
  const sweepFlag = getSweepFlag(doorPoints);
  const finishingPoint = `${doorPoints.opened_point}`;
  return `M${doorPoints.closed_point}  A${ellipseRadius} ${rotation} ${largeArcFlag},${sweepFlag} ${finishingPoint}`;
}

function getSweepFlag(doorPoints: DoorSweepingPoints) {
  /**
   * Specifies on which side of the path (from closed point -> opened point) the curve is drawn. Depends on where the angle (axis) point is.
   * A positive cross product between v1 & v2 corresponds to angle point on the left side of the path.
   */
  const v1 = [
    doorPoints.opened_point[0] - doorPoints.closed_point[0],
    doorPoints.opened_point[1] - doorPoints.closed_point[1],
  ]; //vector connecting closed point with opened point
  const v2 = [
    doorPoints.angle_point[0] - doorPoints.closed_point[0],
    doorPoints.angle_point[1] - doorPoints.closed_point[1],
  ]; //vector connecting closed point with angle point
  const cross_product = v1[0] * v2[1] - v1[1] * v2[0];
  if (cross_product > 0) {
    return 1;
  } else {
    return 0;
  }
}

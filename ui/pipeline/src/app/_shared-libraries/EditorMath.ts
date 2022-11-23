import { Vector2, ShapeUtils } from 'three-full/builds/Three.es';
import { COOR_X, COOR_Y } from './SimData';

export class EditorMath {
  /**
   * Calculate the distance between 2 points
   * @param x1
   * @param y1
   * @param x2
   * @param y2
   */
  public static distance(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  }
  public static distancePoints(p1, p2) {
    return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
  }

  /**
   * Given the brooks opening coordinates 'open', 'axis' and 'close'
   * We return coordinates making a curve to represent a door
   * @param opening_area
   */
  public static calculateDoorOpenings(opening_area) {
    const numPoints = 10;
    const points = [opening_area.axis];

    const distRef = EditorMath.distance(
      opening_area.open[COOR_X],
      opening_area.open[COOR_Y],
      opening_area.axis[COOR_X],
      opening_area.axis[COOR_Y]
    );

    for (let i = 0; i <= numPoints; i += 1) {
      const rectX =
        (opening_area.close[COOR_X] * i) / numPoints + (opening_area.open[COOR_X] * (numPoints - i)) / numPoints;
      const rectY =
        (opening_area.close[COOR_Y] * i) / numPoints + (opening_area.open[COOR_Y] * (numPoints - i)) / numPoints;

      const currentDist = this.distance(opening_area.axis[COOR_X], opening_area.axis[COOR_Y], rectX, rectY);

      const correction = 1 - currentDist / distRef;

      const newPoint = [
        rectX + (rectX - opening_area.axis[COOR_X]) * correction,
        rectY + (rectY - opening_area.axis[COOR_Y]) * correction,
      ];

      points.push(newPoint);
    }

    points.push(opening_area.axis);

    return points;
  }

  /**
   * Changes the position of an elements if the positions X or Y are not null
   * @param object
   * @param newPositionX
   * @param newPositionY
   */
  public static move(object, newPositionX, newPositionY) {
    if (newPositionX !== null) {
      object.position.x = newPositionX;
    }
    if (newPositionY !== null) {
      object.position.y = newPositionY;
    }
  }

  /**
   * Changes the element angle
   * @param object
   * @param newAngle
   */
  public static rotate(object, newAngle) {
    object.rotation.z = newAngle;
  }

  /**
   * Array with x and y components transformed into Vector2
   * @param array
   */
  public static arrayToVector(array): Vector2 {
    return new Vector2(array[COOR_X], array[COOR_Y]);
  }

  /**
   * Vector2 into array
   * @param vector
   */
  public static vectorToArray(vector: Vector2) {
    return [vector.x, vector.y];
  }

  public static calculateAreaFromPolygon(polygon) {
    let area = 0;
    if (polygon.type === 'Polygon') {
      area = this.polygonArea(polygon.coordinates);
    } else if (polygon.type === 'MultiPolygon') {
      for (let i = 0; i < polygon.coordinates.length; i += 1) {
        area += this.polygonArea(polygon.coordinates[i]);
      }
    }
    return area;
  }

  public static polygonArea(coords) {
    let area = 0;
    if (coords && coords.length > 0) {
      area += EditorMath.calculateAreaFromCoordinates(coords[0]);
      for (let i = 1; i < coords.length; i += 1) {
        area -= EditorMath.calculateAreaFromCoordinates(coords[i]);
      }
    }
    return area;
  }

  /**
   * Given the polygon coordinates we calculate the area
   * @param coordinates
   */
  public static calculateAreaFromCoordinates(coordinates) {
    const currentArrayVector = coordinates.map(coor => new Vector2(coor[COOR_X], coor[COOR_Y]));
    return Math.abs(ShapeUtils.area(currentArrayVector));
  }
}

import { EditorMath } from './EditorMath';
import { COOR_X, COOR_Y } from './SimData';
import { EditorCoordinates } from './EditorCoordinates';
import { Vector2 } from 'three-full/builds/Three.es';

describe('EditorMath.ts library', () => {
  beforeEach(() => {});

  it('should calculate the distance between 2 points', () => {
    expect(EditorMath.distance(0, 0, 0, 0)).toBe(0);
    expect(EditorMath.distance(0, 0, 2, 2)).toBeCloseTo(2.828, 2);
    expect(EditorMath.distance(1, 1, 2, 2)).toBeCloseTo(1.414, 2);
    expect(EditorMath.distance(1, 1, -2, -2)).toBeCloseTo(4.242, 2);
    expect(EditorMath.distance(-1, -1, 2, 2)).toBeCloseTo(4.242, 2);
    expect(EditorMath.distance(0, 1000, 0, 2000)).toBe(1000);
    expect(EditorMath.distance(100, 0, 200, 0)).toBe(100);
  });

  it('should calculate the door openings', () => {
    const opening_area = {
      open: [],
      axis: [],
      close: [],
    };

    const doorLength = 1;
    opening_area.open[COOR_X] = 0;
    opening_area.open[COOR_Y] = doorLength;
    opening_area.axis[COOR_X] = 0;
    opening_area.axis[COOR_Y] = 0;
    opening_area.close[COOR_X] = doorLength;
    opening_area.close[COOR_Y] = 0;

    const opening = EditorMath.calculateDoorOpenings(opening_area);
    expect(opening).toBeDefined();
    expect(opening.length).toBeGreaterThan(8);
    opening.forEach((point, i) => {
      if (i > 0 && i < opening.length - 1) {
        expect(
          EditorMath.distance(opening_area.axis[COOR_X], opening_area.axis[COOR_Y], point[COOR_X], point[COOR_Y])
        ).toBeCloseTo(doorLength, 0);
      } else {
        expect(opening_area.axis[COOR_X]).toBe(point[COOR_X]);
        expect(opening_area.axis[COOR_Y]).toBe(point[COOR_Y]);
      }
    });
  });

  it('should change the coordinates of the object', () => {
    const object = {
      position: new Vector2(1, 1),
    };
    const newPositionX = 5;
    const newPositionY = 10;
    EditorMath.move(object, newPositionX, newPositionY);

    expect(object.position.x).toBe(newPositionX);
    expect(object.position.y).toBe(newPositionY);
  });

  it('should change the angle of the given object', () => {
    const object = {
      rotation: {
        z: 0,
      },
    };
    const newAngle = 30;

    EditorMath.rotate(object, newAngle);

    expect(object.rotation.z).toBe(newAngle);
  });

  it('should create a rectangle and measure the area ', () => {
    // Rectangle 1x1, expected area 1
    const coordinates1x1 = EditorCoordinates.rectangle(1, 1);
    const area1x1 = EditorMath.calculateAreaFromCoordinates(coordinates1x1);
    expect(area1x1).toBe(1);

    // Rectangle 2x2, expected area 4
    const coordinates2x2 = EditorCoordinates.rectangle(2, 2);
    const area2x2 = EditorMath.calculateAreaFromCoordinates(coordinates2x2);
    expect(area2x2).toBe(4);

    // Rectangle 2x1, expected area 2
    const coordinates2x1 = EditorCoordinates.rectangle(2, 1);
    const area2x1 = EditorMath.calculateAreaFromCoordinates(coordinates2x1);
    expect(area2x1).toBe(2);
  });
});

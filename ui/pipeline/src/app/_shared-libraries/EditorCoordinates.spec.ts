import { EditorCoordinates } from './EditorCoordinates';
import { EditorMath } from './EditorMath';
import { COOR_X, COOR_Y } from './SimData';

describe('EditorCoordinates.ts library', () => {
  beforeEach(() => {});

  it('should create a rectangle collection of points', () => {
    const height = 10;
    const width = 20;
    const rectangle = EditorCoordinates.rectangle(height, width);

    // 5 points including the last to be the first again
    expect(rectangle.length).toBe(5);
    expect(
      EditorMath.distance(rectangle[0][COOR_X], rectangle[0][COOR_Y], rectangle[1][COOR_X], rectangle[1][COOR_Y])
    ).toBe(height);

    expect(
      EditorMath.distance(rectangle[1][COOR_X], rectangle[1][COOR_Y], rectangle[2][COOR_X], rectangle[2][COOR_Y])
    ).toBe(width);
  });
});

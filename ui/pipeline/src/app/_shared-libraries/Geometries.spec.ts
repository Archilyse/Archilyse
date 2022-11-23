import { drawError, drawGeometries } from './Geometries';

class MockContainer {
  added = 0;

  add() {
    this.added += 1;
  }
  getAdded() {
    return this.added;
  }
}

describe('Geometries.ts library', () => {
  beforeEach(() => {});

  it('should create a geometry', () => {
    const mockContainer = new MockContainer();
    const coordinates = {
      type: 'Polygon',
      coordinates: [
        [
          [1, 1],
          [0, 1],
          [0, 0],
          [1, 0],
        ],
        [
          [2, 2],
          [1, 2],
          [1, 1],
          [2, 1],
        ],
      ],
    };
    const lineColor = 0x333333;
    const lineWidth = 1.5;
    const zIndex = 0.1;
    drawGeometries(mockContainer, coordinates, lineColor, lineWidth, zIndex);
    expect(mockContainer.getAdded()).toBe(2);
  });

  it('should NOT create an error because no position was given', () => {
    const mockContainer = new MockContainer();

    const errorBad = {};
    drawError(mockContainer, null, errorBad, null, 0);
    expect(mockContainer.getAdded()).toBe(0);
  });
});

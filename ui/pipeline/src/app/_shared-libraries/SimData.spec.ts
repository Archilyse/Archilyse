import {
  getHexColorsAndLegend,
  getNumberToHexFunction,
  svgBoundingBox,
  polygonJsonBoundingBox,
  correctScale,
} from './SimData';

describe('SimConstants.ts library', () => {
  beforeEach(() => {});

  it('should create a function that provide colors from the gradient', () => {
    const min = 0;
    const max = 9;
    const functionNumberToHex = getNumberToHexFunction(min, max);

    expect(functionNumberToHex(min)).toBe('rgb(44, 123, 182)');
    expect(functionNumberToHex((max + min) / 2)).toBe('rgb(252, 232, 114)');
    expect(functionNumberToHex(max)).toBe('rgb(199, 0, 32)');
  });

  it('should provide scale to different simulation units', () => {
    expect(correctScale('m<sup>3</sup>')).toBe(1);
    expect(correctScale('steradians')).toBe(1);
    expect(correctScale('lux')).toBe(1000);
    expect(correctScale('Lux')).toBe(1000);
    expect(correctScale('Klux')).toBe(1);
  });

  it('should provide legend and hex colors functions', () => {
    const min = 0;
    const max = 9;
    const dataArray = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const numSteps = 10;

    const hexAndLegend = getHexColorsAndLegend(dataArray, min, max, numSteps);

    // Hex colors
    expect(hexAndLegend.hexColors).toBeDefined();
    expect(hexAndLegend.hexColors.length).toBe(dataArray.length);

    // Legend colors
    expect(hexAndLegend.legend).toBeDefined();
    expect(Object.keys(hexAndLegend.legend).length).toBe(numSteps);

    // Min max
    expect(hexAndLegend.max).toBe(max);
    expect(hexAndLegend.min).toBe(min);
  });

  it('should create the bounding box out of a polygon', () => {
    const polygonVertices = [
      [
        [1, 1],
        [1, 2],
        [2, 2],
        [2, 1],
        [1, 1],
      ],
    ];
    const boundingBox = svgBoundingBox(polygonVertices);
    expect(boundingBox.x1).toBe(1);
    expect(boundingBox.x2).toBe(2);
    expect(boundingBox.y1).toBe(1);
    expect(boundingBox.y2).toBe(2);
  });

  it('should create the bounding box out of a polygon', () => {
    const polygon = {
      type: 'Polygon',
      coordinates: [
        [
          [0, 0.5],
          [1, 2],
          [2, 2],
          [2, 1],
          [1, 1],
        ],
        [
          [1, 1],
          [1, 2],
          [2, 2],
          [2, 1],
          [1, 1],
        ],
      ],
    };
    const boundingBox = polygonJsonBoundingBox(polygon);
    expect(boundingBox.x1).toBe(0);
    expect(boundingBox.x2).toBe(2);
    expect(boundingBox.y1).toBe(0.5);
    expect(boundingBox.y2).toBe(2);
  });

  it('should create the bounding box out of a multi-polygon', () => {
    const multiPolygon = {
      type: 'MultiPolygon',
      coordinates: [
        [
          [
            [0, 0.5],
            [1, 2],
            [2, 2],
            [2, 1],
            [1, 1],
          ],
          [
            [1, 1],
            [1, 2],
            [2, 2],
            [2, 1],
            [1, 1],
          ],
        ],
        [
          [
            [1, 0],
            [1, 2],
            [3, 3],
            [2, 1],
            [1, 1],
          ],
        ],
      ],
    };
    const boundingBox = polygonJsonBoundingBox(multiPolygon);
    expect(boundingBox.x1).toBe(0);
    expect(boundingBox.x2).toBe(3);
    expect(boundingBox.y1).toBe(0);
    expect(boundingBox.y2).toBe(3);
  });
});

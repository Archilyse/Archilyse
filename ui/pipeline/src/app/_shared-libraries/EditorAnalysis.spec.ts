import { EditorAnalysis } from './EditorAnalysis';
import { TestingConstants } from './TestingConstants';
import { AreaService } from '../_services/area.service';

describe('EditorAnalysis.ts library', () => {
  beforeEach(() => {});

  it('should calculate the area of a standard brooks element', () => {
    const brooksElementSquare = {
      footprint: {
        type: 'Polygon',
        coordinates: [
          [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1],
            [0, 0],
          ],
        ],
      },
    };
    const areaSquare = EditorAnalysis.calculateAreaElement(brooksElementSquare);
    expect(areaSquare).toBe(1);

    const brooksElementTriangle = {
      footprint: {
        type: 'Polygon',
        coordinates: [
          [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 0],
          ],
        ],
      },
    };
    const areaTriangle = EditorAnalysis.calculateAreaElement(brooksElementTriangle);
    expect(areaTriangle).toBe(0.5);
  });

  it('should do a brooks analysis and find a room not defined', () => {
    const brooksModel = TestingConstants.brooksModel;
    const areaTypes = TestingConstants.areaTypes;

    const fallbackToBrooks = true;
    const areaService = new AreaService(null, null);
    areaService.setFallback(fallbackToBrooks);

    const result = EditorAnalysis.analyzeModelStructure(brooksModel, areaService, areaTypes);

    // We have a result
    expect(result).toBeDefined();

    // We have a not defined area
    expect(result['NOT_DEFINED'].length).toBe(1);

    // The not defined area has more than 10 m2
    expect(result['NOT_DEFINED'][0]).toBeGreaterThan(10);
  });
});

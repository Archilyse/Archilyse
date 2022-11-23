import { MOCK_STATE } from '../tests/utils';
import { Area } from './export';

describe('getAreaIntersectingCoordinates', () => {
  let state = MOCK_STATE;
  const coords = [
    [
      [0, 0],
      [0, 500],
      [500, 500],
      [500, 0],
      [0, 0],
    ],
  ];
  state = {
    ...state,
    scene: {
      ...state.scene,
      layers: {
        ...state.scene.layers,
        'layer-1': {
          ...state.scene.layers['layer-1'],
          areas: {
            ...state.scene.layers['layer-1'].areas,
            'area-1': {
              ...state.scene.layers['layer-1'].areas['area-1'],
              coords: coords,
            },
          },
        },
      },
    },
  };

  it('If there are no areas matching the coordinates null is returned', () => {
    const [x, y] = [-1, -1];
    const areaPolygon = Area.getAreaIntersectingCoordinates(state.scene, x, y);
    expect(areaPolygon).toBe(null);
  });
  it('If there are areas matching the coordinates the area is correctly returned', () => {
    const [x, y] = [100, 100];
    const areaPolygon = Area.getAreaIntersectingCoordinates(state.scene, x, y);
    expect(areaPolygon).toStrictEqual({
      geometry: { coordinates: coords, type: 'Polygon' },
      properties: {},
      type: 'Feature',
    });
  });
});

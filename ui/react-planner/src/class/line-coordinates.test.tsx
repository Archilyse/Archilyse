import { Line } from '../class/export';
import { REFERENCE_LINE_POSITION, SeparatorsType } from '../constants';
import { addLineToState, getMockState } from '../tests/utils/tests-utils';
import { cloneDeep, SnapSceneUtils } from '../utils/export';

describe('coordinates should be updated whenever manipulating a line', () => {
  const properties = {
    height: {
      unit: 'cm',
      value: 300,
    },
    referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
    width: {
      unit: 'cm',
      value: 20,
    },
  };
  const initialState = getMockState();
  it('should always set the line coordinates when finished drawing', () => {
    const expectedCoords = [
      [0, -20],
      [5, -20],
      [5, 0],
      [0, 0],
      [0, -20],
    ];
    let state = initialState;
    const updateCoordsSpy = jest.spyOn(Line, 'AddOrUpdateReferenceLineCoords');

    state = {
      ...state,
      snapMask: [],
      drawingSupport: {
        ...state.drawingSupport,
        layerID: 'layer-1',
      },
    };

    const linePoints = { x0: 0, y0: 0, x1: 5, y1: 0 };
    const { updatedState, line } = addLineToState(state, SeparatorsType.WALL, linePoints, properties);

    updatedState.scene.layers['layer-1'].lines[line.id] = line;
    updatedState.scene.layers['layer-1'].selected.lines = [line.id];

    const x = 5;
    const y = 0;
    const finalState = Line.endDrawingLine(cloneDeep(updatedState), x, y).updatedState;
    const mostRecentLineId = updateCoordsSpy.mock.calls[updateCoordsSpy.mock.calls.length - 1][1];
    const updatedCoordinates = finalState.scene.layers['layer-1'].lines[mostRecentLineId].coordinates;
    expect(updatedCoordinates[0]).toStrictEqual(expectedCoords);
    expect(updateCoordsSpy).toHaveBeenCalled();
  });
  it('should set coordinates when creating a new line', () => {
    const linePoints = { x0: 0, y0: 0, x1: 1, y1: 0 };
    const createdLine = addLineToState(initialState, SeparatorsType.WALL, linePoints, properties).line;
    const coordinates = createdLine.coordinates[0];
    expect(coordinates).toStrictEqual([
      [0, -20],
      [1, -20],
      [1, 0],
      [0, 0],
      [0, -20],
    ]);
  });

  it.each([
    [
      REFERENCE_LINE_POSITION.CENTER,
      [
        [0, 10],
        [1, 10],
        [1, -10],
        [0, -10],
        [0, 10],
      ],
    ],
    [
      REFERENCE_LINE_POSITION.INSIDE_FACE,
      [
        [0, 20],
        [1, 20],
        [1, 0],
        [0, 0],
        [0, 20],
      ],
    ],
  ])(
    'should update coordinates when changing reference of an already drawn line',
    (startingReferenceLine, expectedCoords) => {
      const linePoints = { x0: 0, y0: 0, x1: 1, y1: 0 };
      const propsWithReferenceLine = { ...properties, referenceLine: startingReferenceLine };
      const { updatedState, line } = addLineToState(
        initialState,
        SeparatorsType.WALL,
        linePoints,
        propsWithReferenceLine
      );
      const finalState = Line.changeReferenceLine(updatedState).updatedState;
      const updatedCoordinates = finalState.scene.layers['layer-1'].lines[line.id].coordinates;
      expect(updatedCoordinates[0]).toStrictEqual(expectedCoords);
    }
  );
  it('should update the line coordinates during drawing', () => {
    const snapElementsSpy = jest.spyOn(SnapSceneUtils, 'sceneSnapNearestElementsLine').mockImplementation(() => {});
    const expectedCoords = [
      [0, -20],
      [5, -20],
      [5, 0],
      [0, 0],
      [0, -20],
    ];
    let state = initialState;
    state = {
      ...state,
      snapMask: [],
      drawingSupport: {
        ...state.drawingSupport,
        layerID: 'layer-1',
      },
    };
    const linePoints = { x0: 0, y0: 0, x1: 1, y1: 0 };
    const { updatedState, line } = addLineToState(state, SeparatorsType.WALL, linePoints, properties);
    const x = 5;
    const y = 0;

    const finalUpdatedState = {
      ...updatedState,
      scene: {
        ...updatedState.scene,
        layers: {
          ...updatedState.scene.layers,
          'layer-1': {
            ...updatedState.scene.layers['layer-1'],
            selected: {
              ...updatedState.scene.layers['layer-1'].selected,
              lines: [line.id],
            },
          },
        },
      },
    };
    const finalState = Line.updateDrawingLine(finalUpdatedState, x, y).updatedState;
    const updatedCoordinates = finalState.scene.layers['layer-1'].lines[line.id].coordinates;
    expect(updatedCoordinates[0]).toStrictEqual(expectedCoords);
    expect(snapElementsSpy).toHaveBeenCalled();
  });
  it.each([
    [
      5,
      [
        [0, -25],
        [1, -25],
        [1, 0],
        [0, 0],
        [0, -25],
      ],
    ],
    [
      0,
      [
        [0, -20],
        [1, -20],
        [1, 0],
        [0, 0],
        [0, -20],
      ],
    ],
    [
      -12,
      [
        [0, -8],
        [1, -8],
        [1, 0],
        [0, 0],
        [0, -8],
      ],
    ],
  ])('should update line coordinates when changing its width', (increment, expectedCoords) => {
    const linePoints0 = { x0: 0, y0: 0, x1: 1, y1: 0 };
    const { updatedState, line } = addLineToState(getMockState(), SeparatorsType.WALL, linePoints0, properties);

    const finalState = {
      ...updatedState,
      scene: {
        ...updatedState.scene,
        layers: {
          ...updatedState.scene.layers,
          'layer-1': {
            ...updatedState.scene.layers['layer-1'],
            lines: {
              ...updatedState.scene.layers['layer-1'].lines,
              [line.id]: {
                ...updatedState.scene.layers['layer-1'].lines[line.id],
                selected: true,
              },
            },
          },
        },
      },
    };
    const returnedState = Line.updateWidthSelectedWalls(finalState, increment).updatedState;
    const updatedLineWidth = returnedState.scene.layers['layer-1'].lines[line.id].properties.width.value;
    expect(updatedLineWidth).toBe(properties.width.value + increment);
    const updatedCoordinates = returnedState.scene.layers['layer-1'].lines[line.id].coordinates;
    expect(updatedCoordinates[0]).toStrictEqual(expectedCoords);
  });
});

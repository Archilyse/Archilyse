import { MOCK_SCENE } from '../tests/utils';
import { Scene } from '../models';
import { cloneDeep, SnapSceneUtils } from '../utils/export';
import { SNAP_MASK } from './snap';

const RADIUS_LINES_CONSIDERED_CM = SnapSceneUtils.RADIUS_LINES_CONSIDERED_CM;
const SELECTED_LAYER_ID = 'layer-1';

describe('SnapSceneUtils', () => {
  let scene = null;
  let snapElements = null;
  const snapMask = SNAP_MASK;

  beforeEach(() => {
    scene = new Scene(MOCK_SCENE);
    snapElements = [];
  });

  it(`sceneSnapNearestCopyPasteElements should add the nearest line and point snaps for a copypasted selection of lines`, () => {
    const EXPECTED_POINT_SNAPS = [
      [471.274412042379, 7669.75126120076],
      [458.775119315981, 7669.618290001544],
      [483.773704768777, 7669.884232399977],
      [288.885526822847, 3804.59164611398],
      [276.444767785902, 3805.807176691406],
      [301.326285859793, 3803.376115536555],
    ];

    const EXPECTED_LINE_SEGMENT_SNAPS = [
      [490.446877587176, 5867.539499989791, 471.274412042379, 7669.75126120076],
      [477.947584860779, 5867.406528790574, 458.775119315981, 7669.618290001544],
      [483.773704768777, 7669.884232399977, 502.946170313574, 5867.672471189007],
      [288.885526822847, 3804.59164611398, 490.446877587176, 5867.539499989791],
      [276.444767785902, 3805.807176691406, 478.006118550231, 5868.755030567217],
      [502.887636624122, 5866.323969412365, 301.326285859793, 3803.376115536555],
    ];

    const MOCK_SELECTION = {
      lines: Object.keys(MOCK_SCENE.layers[SELECTED_LAYER_ID].lines).slice(0, 2), // Select the first two lines
    };

    snapElements = SnapSceneUtils.sceneSnapNearestCopyPasteElements(scene, snapMask, MOCK_SELECTION);

    const POINT_SNAPS = snapElements.filter(snap => snap.type === 'point');
    const LINE_SEGMENT_SNAPS = snapElements.filter(snap => snap.type === 'line-segment');

    POINT_SNAPS.forEach((snap, i) => {
      const [x, y] = EXPECTED_POINT_SNAPS[i];
      expect(x).toStrictEqual(snap.x);
      expect(y).toStrictEqual(snap.y);
    });

    LINE_SEGMENT_SNAPS.forEach((snap, i) => {
      const [x1, y1, x2, y2] = EXPECTED_LINE_SEGMENT_SNAPS[i];
      expect(x1).toStrictEqual(snap.x1);
      expect(y1).toStrictEqual(snap.y1);
      expect(x2).toStrictEqual(snap.x2);
      expect(y2).toStrictEqual(snap.y2);
    });
  });

  it(`sceneSnapNearestElementsLine should add the nearest line and point snaps to x,y within ${RADIUS_LINES_CONSIDERED_CM}cm radius`, () => {
    const x = 300;
    const y = 3760;

    const EXPECTED_POINT_SNAPS = [
      [282.834327818672, 3798.540447109805],
      [295.319544838304, 3797.932700474524],
      [270.34911079904, 3799.148193745087],
      [282.834327818672, 3798.540447109805],
      [288.885526822847, 3804.59164611398],
      [297.724361587679, 3795.752811349148],
      [291.673162583504, 3789.701612344973],
      [288.885526822847, 3804.59164611398],
      [301.326285859793, 3803.376115536555],
    ];
    const EXPECTED_LINE_SEGMENT_SNAPS = [
      [471.274412042379, 7669.75126120076, 282.834327818672, 3798.540447109805],
      [483.759629062011, 7669.143514565479, 295.319544838304, 3797.932700474524],
      [270.34911079904, 3799.148193745087, 458.789195022747, 7670.359007836042],
      [282.834327818672, 3798.540447109805, 288.885526822847, 3804.59164611398],
      [297.724361587679, 3795.752811349148, 291.673162583504, 3789.701612344973],
      [288.885526822847, 3804.59164611398, 490.446877587176, 5867.539499989791],
      [502.887636624122, 5866.323969412365, 301.326285859793, 3803.376115536555],
    ];

    snapElements = SnapSceneUtils.sceneSnapNearestElementsLine(scene, snapElements, snapMask, null, x, y);

    const POINT_SNAPS = snapElements.filter(snap => snap.type === 'point');
    const LINE_SEGMENT_SNAPS = snapElements.filter(snap => snap.type === 'line-segment');

    POINT_SNAPS.forEach((snap, i) => {
      const [x, y] = EXPECTED_POINT_SNAPS[i];
      expect(x).toStrictEqual(snap.x);
      expect(y).toStrictEqual(snap.y);
    });

    LINE_SEGMENT_SNAPS.forEach((snap, i) => {
      const [x1, y1, x2, y2] = EXPECTED_LINE_SEGMENT_SNAPS[i];
      expect(x1).toStrictEqual(snap.x1);
      expect(y1).toStrictEqual(snap.y1);
      expect(x2).toStrictEqual(snap.x2);
      expect(y2).toStrictEqual(snap.y2);
    });
  });

  it(`sceneSnapNearestElementsLine should not add any snaps if x,y are not close to any lines or vertices`, () => {
    const x = 350;
    const y = 3760;

    snapElements = SnapSceneUtils.sceneSnapNearestElementsLine(scene, snapElements, snapMask, null, x, y);

    expect(snapElements.length === 0).toBeTruthy();
  });

  it(`sceneSnapNearestElementsLine should add a snap point to create one line parallel to another`, () => {
    const newScene: any = cloneDeep(MOCK_SCENE);
    newScene.height = 5000;
    newScene.layers[SELECTED_LAYER_ID].vertices = {
      p1: { id: 'p1', x: 280, y: 4000 },
      p2: { id: 'p2', x: 450, y: 4000 },

      p3: { id: 'p3', x: 450, y: 4300 },
      p4: { id: 'p4', x: 300, y: 4300 },
    };

    newScene.layers[SELECTED_LAYER_ID].lines = {
      initial_line: { id: 'initial_line', type: 'wall', vertices: ['p1', 'p2'], auxVertices: [], properties: {} },
      drawing_line: { id: 'drawing_line', type: 'wall', vertices: ['p3', 'p4'], auxVertices: [], properties: {} },
    };
    const mockScene = new Scene(newScene);

    const MOCK_PERPENDICULAR_SNAPS = [
      { type: 'line-segment', x1: 300, y1: 4300, x2: 300, y2: 5000, metadata: { perpendicular: true } },
      { type: 'line-segment', x1: 300, y1: 4300, x2: 300, y2: 0, metadata: { perpendicular: true } },
      { type: 'line-segment', x1: 300, y1: 4300, x2: 3000, y2: 4300, metadata: { perpendicular: true } },
      { type: 'line-segment', x1: 300, y1: 4300, x2: 0, y2: 4300, metadata: { perpendicular: true } },
    ];

    // Start drawing on p4 vertex in the `drawing_line` that should be parallel to `initial_line`
    const x = newScene.layers[SELECTED_LAYER_ID].vertices.p4.x;
    const y = newScene.layers[SELECTED_LAYER_ID].vertices.p4.y;

    snapElements = SnapSceneUtils.sceneSnapNearestElementsLine(
      mockScene,
      MOCK_PERPENDICULAR_SNAPS,
      snapMask,
      'drawing_line',
      x,
      y
    );

    const EXPECTED_POINT_SNAPS = [[280, 4300]]; // Snap point parallel to the initial line

    const POINT_SNAPS = snapElements.filter(snap => snap.type === 'point');
    expect(POINT_SNAPS.length).toBe(EXPECTED_POINT_SNAPS.length);

    POINT_SNAPS.forEach((snap, i) => {
      const [x, y] = EXPECTED_POINT_SNAPS[i];
      expect(x).toStrictEqual(snap.x);
      expect(y).toStrictEqual(snap.y);
    });
  });

  it(`sceneSnapHoleNearestLine should not add any snaps if x,y are not close to any lines`, () => {
    const x = 350;
    const y = 3760;
    const allHoles = Object.values(scene.layers[SELECTED_LAYER_ID].holes) as any;
    const hole = allHoles[0];

    snapElements = SnapSceneUtils.sceneSnapHoleNearestLine(scene, snapElements, hole, x, y);
    expect(snapElements.length === 0).toBeTruthy();
  });

  it(`sceneSnapHoleNearestLine should add the nearest line snap to x,y and also 2 points at the line ends`, () => {
    const x = 300;
    const y = 3850;
    const allHoles = Object.values(scene.layers[SELECTED_LAYER_ID].holes) as any;
    const hole = allHoles[0];

    snapElements = SnapSceneUtils.sceneSnapHoleNearestLine(scene, snapElements, hole, x, y);

    const EXPECTED_POINT_SNAPS = [
      [293.261437, 3849.378379],
      [486.070968, 5822.752767],
    ];
    const EXPECTED_LINE_SEGMENT_SNAPS = [[...EXPECTED_POINT_SNAPS[0], ...EXPECTED_POINT_SNAPS[1]]];

    const POINT_SNAPS = snapElements.filter(snap => snap.type === 'point');
    const LINE_SEGMENT_SNAPS = snapElements.filter(snap => snap.type === 'line-segment');

    LINE_SEGMENT_SNAPS.forEach((snap, index) => {
      const [x1, y1, x2, y2] = EXPECTED_LINE_SEGMENT_SNAPS[index];
      expect(x1).toStrictEqual(snap.x1);
      expect(y1).toStrictEqual(snap.y1);
      expect(x2).toStrictEqual(snap.x2);
      expect(y2).toStrictEqual(snap.y2);
    });

    POINT_SNAPS.forEach((snap, index) => {
      const [x, y] = EXPECTED_POINT_SNAPS[index];
      expect(x).toStrictEqual(snap.x);
      expect(y).toStrictEqual(snap.y);
    });
  });
});

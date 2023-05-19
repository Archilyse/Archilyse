import { MOCK_SCENE, MOCK_STATE } from '../tests/utils';
import { MODE_COPY_PASTE, MODE_DRAWING_LINE, MODE_IDLE, OPENING_TYPE } from '../constants';
import { ProviderHash } from '../providers';
import { getMockState } from '../tests/utils/tests-utils';
import { Hole, Item, State } from '../types';
import { doorHasWings } from '../utils/state-utils';
import cloneDeep from '../utils/clone-deep';
import {
  MOCK_DEMO_SCENE,
  MOCK_PREDICTION,
  MOCK_SCENE_HISTORY,
  MOCK_SNAP_ELEMENTS,
  SELECTED_LAYER_ID,
} from './project.testMocks';
import Project from './project';

describe('Project class methods', () => {
  let state: State;

  beforeEach(() => {
    const mockState = {
      ...MOCK_STATE,
      mode: MODE_DRAWING_LINE,
      scene: MOCK_DEMO_SCENE,
      snapElements: MOCK_SNAP_ELEMENTS,
      sceneHistory: MOCK_SCENE_HISTORY,
    };
    state = getMockState(mockState);
  });

  it('Rollback should cancel drawing a line, unselect all elements and remove all snaps', async () => {
    expect(state.mode).toEqual(MODE_DRAWING_LINE);

    state = Project.rollback(state).updatedState;

    // Check if the state mode is IDLE
    expect(state.mode).toEqual(MODE_IDLE);

    // Check if everything is unselected
    const selected = state.scene.layers[SELECTED_LAYER_ID].selected;
    ['lines', 'vertices'].forEach(key => {
      expect(selected[key].length === 0).toEqual(true);
    });

    // Check if snaps are removed
    expect(state.snapElements.length === 0).toEqual(true);
    expect(state.activeSnapElement).toEqual(null);
  });

  it('Undo should revert the scene to a previous state', async () => {
    let selectedLayer = state.scene.layers[SELECTED_LAYER_ID];
    const LINES_BEFORE_UNDO = Object.values(selectedLayer.lines).length;
    const SCENE_HISTORY_HASH_BEFORE_UNDO = ProviderHash.hash(state.sceneHistory);

    expect(state.mode).toEqual(MODE_DRAWING_LINE);

    state = Project.undo(state).updatedState;
    selectedLayer = state.scene.layers[SELECTED_LAYER_ID];

    // Check if scene mode is IDLE
    expect(state.mode).toEqual(MODE_IDLE);

    // Check if Undo reverted the last drawn line
    expect(Object.values(selectedLayer.lines).length).toBeLessThan(LINES_BEFORE_UNDO);

    // Check if the history lists are updated after undo // @TODO: Use provider hash
    expect(ProviderHash.hash(state.sceneHistory)).not.toEqual(SCENE_HISTORY_HASH_BEFORE_UNDO);
  });

  it('Undo should revert the scene to a clean state', async () => {
    /**
     * Revert the project to the initial state
     * With our mock state the project initial state should be empty
     */
    while (state.sceneHistory.list.length !== 0) {
      state = Project.undo(state).updatedState;
    }

    const selectedLayer = state.scene.layers[SELECTED_LAYER_ID];

    expect(state.sceneHistory.list.length === 0).toEqual(true);
    expect(state.snapElements.length === 0).toEqual(true);
    expect(state.activeSnapElement).toEqual(null);
    expect(Object.values(selectedLayer.lines).length === 0).toEqual(true);
  });

  describe('rollback', () => {
    afterEach(() => {
      jest.clearAllMocks();
    });

    it(`Performs an undo and goes to ${MODE_IDLE} when modifying a copypaste selection`, () => {
      const MOCK_SELECTION = {
        startPosition: { x: 20, y: 20 },
        endPosition: { x: 20, y: 20 },
        draggingPosition: { x: 20, y: 20 },
      };
      state = {
        ...state,
        mode: MODE_COPY_PASTE,
        copyPaste: {
          ...state.copyPaste,
          selection: MOCK_SELECTION,
        },
      };

      const undo = jest.spyOn(Project, 'undo');

      const updatedState = Project.rollback(state).updatedState;

      expect(undo).toHaveBeenCalled();
      expect(updatedState.mode).toBe(MODE_IDLE);
    });

    it(`Goes back to ${MODE_IDLE} but doesn't perform an undo if the copypaste selection is pasted or not started`, () => {
      const MOCK_SELECTION = {
        startPosition: { x: -1, y: -1 },
        endPosition: { x: -1, y: -1 },
        draggingPosition: { x: -1, y: -1 },
      };
      state = {
        ...state,
        mode: MODE_COPY_PASTE,
        copyPaste: {
          ...state.copyPaste,
          selection: MOCK_SELECTION,
        },
      };
      const undo = jest.spyOn(Project, 'undo');

      const updatedState = Project.rollback(state).updatedState;

      expect(undo).not.toHaveBeenCalled();
      expect(updatedState.mode).toBe(MODE_IDLE);
    });
  });

  describe('loadPrediction', () => {
    let mockPrediction;

    const EXPECTED_HOLES = [
      { type: MOCK_PREDICTION.holes[0].properties.label.toLowerCase() },
      { type: MOCK_PREDICTION.holes[1].properties.label.toLowerCase() },
    ];

    const EXPECTED_ITEMS = [
      { type: MOCK_PREDICTION.items[0].properties.label.toLowerCase(), x: 758.5, y: 777.5 },
      { type: MOCK_PREDICTION.items[1].properties.label.toLowerCase(), x: 842, y: 667.5 },
    ];

    beforeEach(() => {
      state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });

      state.scene.layers[SELECTED_LAYER_ID].holes = {};
      state.scene.layers[SELECTED_LAYER_ID].items = {};
      Object.values(state.scene.layers[SELECTED_LAYER_ID].lines).forEach(line => {
        line.holes = [];
      });
      mockPrediction = cloneDeep(MOCK_PREDICTION); // Otherwise there will be side-effects
    });

    it('Add holes to the state: Always without sweeping points', () => {
      const updatedState = Project.loadPrediction(state, mockPrediction).updatedState;

      const addedHoles = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].holes);
      expect(addedHoles.length).toBe(EXPECTED_HOLES.length);

      addedHoles.forEach((Hole: Hole, index: number) => {
        const expectedHole = EXPECTED_HOLES[index];

        // Door with sweeping points should be rendered as sliding doors
        if (doorHasWings(expectedHole.type)) {
          expect(Hole.type).toBe(OPENING_TYPE.SLIDING_DOOR);
        } else {
          expect(Hole.type).toBe(expectedHole.type);
        }
      });
    });

    it('Add items to the state', () => {
      const updatedState = Project.loadPrediction(state, mockPrediction).updatedState;

      const addedItems = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].items);
      expect(addedItems.length).toBe(EXPECTED_ITEMS.length);

      addedItems.forEach((item: Item, index: number) => {
        const expectedItem = EXPECTED_ITEMS[index];

        expect(item.type).toBe(expectedItem.type);
        expect(item.x).toBe(expectedItem.x);
        expect(item.y).toBe(expectedItem.y);
      });
    });

    it('Does not add holes or items again if they are already added', () => {
      state = Project.loadPrediction(state, mockPrediction).updatedState;

      let addedHoles = Object.values(state.scene.layers[SELECTED_LAYER_ID].holes);
      let addedItems = Object.values(state.scene.layers[SELECTED_LAYER_ID].items);

      expect(addedHoles.length).toBe(EXPECTED_HOLES.length);
      expect(addedItems.length).toBe(EXPECTED_ITEMS.length);

      // If we load the prediction again
      state = Project.loadPrediction(state, mockPrediction).updatedState;

      // There should be the same number of items and holes as they are not added again
      addedHoles = Object.values(state.scene.layers[SELECTED_LAYER_ID].holes);
      addedItems = Object.values(state.scene.layers[SELECTED_LAYER_ID].items);
      expect(addedHoles.length).toBe(EXPECTED_HOLES.length);
      expect(addedItems.length).toBe(EXPECTED_ITEMS.length);
    });
  });
});

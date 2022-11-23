import { MOCK_STATE } from '../tests/utils';
import { MODE_COPY_PASTE, MODE_DRAWING_LINE, MODE_IDLE } from '../constants';
import { ProviderHash } from '../providers';
import { getMockState } from '../tests/utils/tests-utils';
import { MOCK_DEMO_SCENE, MOCK_SCENE_HISTORY, MOCK_SNAP_ELEMENTS, SELECTED_LAYER_ID } from './project.testMocks';
import { Project } from './export';

describe('Project class methods', () => {
  let state;

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
});

import clickedInsideSelection from './clicked-inside-selection';

const MOCK_INITIAL_EMPTY_SELECTION = {
  startPosition: { x: -1, y: -1 },
  endPosition: { x: -1, y: -1 },
  draggingPosition: { x: -1, y: -1 },
};

const MOCK_TOP_LEFT_BOTTOM_RIGHT = {
  startPosition: { x: 100, y: 200 },
  endPosition: { x: 200, y: 100 },
  draggingPosition: { x: -1, y: -1 },
};

const MOCK_BOTTOM_LEFT_TOP_RIGHT = {
  startPosition: { x: 100, y: 100 },
  endPosition: { x: 300, y: 200 },
  draggingPosition: { x: -1, y: -1 },
};

const MOCK_BOTTOM_RIGHT_TOP_LEFT = {
  startPosition: { x: 300, y: 100 },
  endPosition: { x: 100, y: 200 },
  draggingPosition: { x: -1, y: -1 },
};

const MOCK_TOP_RIGHT_BOTTOM_LEFT = {
  startPosition: { x: 300, y: 200 },
  endPosition: { x: 100, y: 100 },
  draggingPosition: { x: -1, y: -1 },
};

describe('clickedInsideSelection', () => {
  const NOT_DRAGGED_CASES: any = [
    ['inside of a selection drawn from top left to bottom right', true, MOCK_TOP_LEFT_BOTTOM_RIGHT, { x: 150, y: 150 }],
    ['outside of a selection drawn from top left to bottom right', false, MOCK_TOP_LEFT_BOTTOM_RIGHT, { x: 1, y: 150 }],

    ['inside of a selection drawn from bottom left to top right', true, MOCK_BOTTOM_LEFT_TOP_RIGHT, { x: 150, y: 150 }],
    ['outside of a selection drawn from bottom left to top right', false, MOCK_BOTTOM_LEFT_TOP_RIGHT, { x: 1, y: 150 }],

    ['inside of a selection drawn from bottom right to top left', true, MOCK_BOTTOM_RIGHT_TOP_LEFT, { x: 150, y: 150 }],
    ['outside of a selection drawn from bottom right to top left', false, MOCK_BOTTOM_RIGHT_TOP_LEFT, { x: 1, y: 150 }],

    ['inside of a selection drawn from top right to bottom left', true, MOCK_TOP_RIGHT_BOTTOM_LEFT, { x: 150, y: 150 }],
    ['outside of a selection drawn from top right to bottom left', false, MOCK_TOP_RIGHT_BOTTOM_LEFT, { x: 1, y: 150 }],
  ];

  const DRAGGED_CASES = NOT_DRAGGED_CASES.map(mockCase => {
    const [description, result, selection, clickCoordinates] = mockCase;
    const newSelection = { ...selection, draggingPosition: { x: 100, y: 100 } };
    return [description, result, newSelection, clickCoordinates];
  });

  describe('With a new (non dragged) selection', () => {
    it.each(NOT_DRAGGED_CASES)('Clicking %s returns %s', (description, result, selection, clickCoordinates) => {
      expect(clickedInsideSelection(clickCoordinates.x, clickCoordinates.y, selection)).toBe(result);
    });
  });

  describe('With an already dragged selection', () => {
    it.each(DRAGGED_CASES)('Clicking %s returns %s', (description, result, selection, clickCoordinates) => {
      expect(clickedInsideSelection(clickCoordinates.x, clickCoordinates.y, selection)).toBe(result);
    });
  });

  describe('With no selection', () => {
    it('Returns false', () => {
      const selection = MOCK_INITIAL_EMPTY_SELECTION;
      expect(clickedInsideSelection(100, 100, selection)).toBe(false);
    });
  });
});

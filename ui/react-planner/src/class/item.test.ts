import { MOCK_SCENE, MOCK_STATE } from '../tests/utils';
import { Area as AreaModel, HistoryStructure, Item as ItemModel } from '../models';
import MyCatalog from '../catalog-elements/mycatalog';
import { MODE_DRAGGING_ITEM, MODE_DRAWING_ITEM, MODE_IDLE } from '../constants';
import { addItemToState, getMockState } from '../tests/utils/tests-utils';
import { Item } from './export';
import { SELECTED_LAYER_ID } from './copyPaste.testMocks';

const LAYER_ID = 'layer-1';

describe('beginDraggingItem', () => {
  let state;
  let itemToDrag;
  const MOCK_INITIAL_DRAGGING_POSITION = { x: 100, y: 30 };

  beforeEach(() => {
    state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });
    const itemResult = addItemToState(state, 'kitchen', 80, 30);
    itemToDrag = itemResult.item;
    state = itemResult.updatedState;
  });

  it('Changes dragging support with the dragged item and initial position', () => {
    const { x, y } = MOCK_INITIAL_DRAGGING_POSITION;
    state = Item.beginDraggingItem(state, SELECTED_LAYER_ID, itemToDrag.id, x, y).updatedState;
    const newDraggingSupport = state.draggingSupport;

    const EXPECTED_DRAGGING_SUPPORT = {
      itemID: itemToDrag.id,
      layerID: SELECTED_LAYER_ID,
      startPointX: x,
      startPointY: y,
      originalX: itemToDrag.x,
      originalY: itemToDrag.y,
    };
    expect(newDraggingSupport).toStrictEqual(EXPECTED_DRAGGING_SUPPORT);
  });

  it('Explicitly selects the item', () => {
    const { x, y } = MOCK_INITIAL_DRAGGING_POSITION;
    state = Item.beginDraggingItem(state, SELECTED_LAYER_ID, itemToDrag.id, x, y).updatedState;
    const newSelectedItems = state.scene.layers[SELECTED_LAYER_ID].selected.items;

    expect(newSelectedItems.length).toBe(1);
    expect(newSelectedItems[0]).toBe(itemToDrag.id);

    const updatedItem = state.scene.layers[SELECTED_LAYER_ID].items[itemToDrag.id];
    expect(updatedItem.selected).toBe(true);
  });
});

describe('getItemAngle', () => {
  it('Item and snap are undefined so we have default angle of 0', () => {
    const item = undefined;
    const snap = undefined;
    const angle = Item.getItemAngle(item, snap);
    expect(angle).toBe(0);
  });
  it('Item have already previous rotation and snap is empty', () => {
    const item = { rotation: 90 };
    const snap = undefined;
    const angle = Item.getItemAngle(item, snap);
    expect(angle).toBe(90);
  });
  it('Item have already previous rotation and snap also has an angle, so snap has priority', () => {
    const item = { rotation: 90 };
    const snap = { snap: { metadata: { SnappingAngle: 77 } } };
    const angle = Item.getItemAngle(item, snap);
    expect(angle).toBe(77);
  });
});

describe('areaSnappingParameters', () => {
  it.each([['stairs'], ['elevator']])('Area snapping is called with the right parameters', async itemType => {
    const item = { type: itemType, properties: { width: { value: 10 }, length: { value: 20 } } };
    const state = MOCK_STATE;
    const { itemDimensions, snapAngle } = Item.areaSnappingParameters(state, item);
    expect(snapAngle).toBe(90);
    expect(itemDimensions.width).toBe(10);
    // the feature is actually returning the width of the item always
    expect(itemDimensions.length).toBe(10);
  });
  it('Area snapping is called with the right parameters if it is not a staircase', () => {
    const item = { type: 'kitchen', properties: { width: { value: 20 }, length: { value: 10 } } };
    const state = MOCK_STATE;
    const { itemDimensions, snapAngle } = Item.areaSnappingParameters(state, item);
    expect(snapAngle).toBe(180);
    expect(itemDimensions.width).toBe(20);
    expect(itemDimensions.length).toBe(10);
  });
});

describe('isSelectedItemInValidPosition', () => {
  let state = MOCK_STATE;
  const areaCoords = [
    [
      [0, 0],
      [0, 500],
      [500, 500],
      [500, 0],
      [0, 0],
    ],
  ];
  const itemInside = new ItemModel({
    id: 'item-inside',
    x: 100,
    y: 100,
    rotation: 90,
    properties: { width: { value: 10 }, length: { value: 10 } },
  });
  const itemBorder = new ItemModel({
    id: 'item-border',
    x: 0,
    y: 0,
    rotation: 90,
    properties: { width: { value: 1 }, length: { value: 1 } },
  });

  const itemRotatedOutside = new ItemModel({
    id: 'item-rotated-outside',
    x: 5,
    y: 5,
    rotation: 95,
    properties: { width: { value: 10 }, length: { value: 10 } },
  });

  const area1 = new AreaModel({
    id: 'area-1',
    coords: areaCoords,
  });
  state = {
    ...state,
    scene: {
      ...state.scene,
      layers: {
        ...state.scene.layers,
        ['layer-1']: {
          ...state.scene.layers['layer-1'],
          items: {
            ...state.scene.layers['layer-1'].items,
            'item-inside': itemInside,
            'item-border': itemBorder,
            'item-rotated-outside': itemRotatedOutside,
          },
          areas: {
            ...state.scene.layers['layer-1'].areas,
            'area-1': area1,
          },
        },
      },
    },
  };
  it.each([
    ['item-inside', true],
    ['item-border', false],
    ['item-rotated-outside', false],
  ])('The selected item is correctly validated', async (selectedItem, expectedValidation) => {
    state = {
      ...state,
      scene: {
        ...state.scene,
        layers: {
          ...state.scene.layers,
          ['layer-1']: {
            ...state.scene.layers['layer-1'],
            selected: {
              ...state.scene.layers['layer-1'].selected,
              items: [selectedItem],
            },
          },
        },
      },
    };

    const valid = Item.isSelectedItemInValidPosition(state.scene);
    expect(valid).toBe(expectedValidation);
  });
});

describe('invalidateCurrentItem', () => {
  let state = MOCK_STATE;
  state = {
    ...state,
    mode: MODE_IDLE,
    sceneHistory: new HistoryStructure(state.sceneHistory || { first: state.scene, last: state.scene }),
  };
  it('An item is correctly removed from the state and the mode is set as expected when the item is invalid', () => {
    const newMode = MODE_DRAWING_ITEM;
    const updatedState = Item.invalidateCurrentItem(state, newMode).updatedState;
    expect(updatedState.mode).toBe(MODE_DRAWING_ITEM);
  });
});

describe('invalidPositionToDraggingMode', () => {
  const state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE });

  it(`The viewer mode is set to "${MODE_DRAGGING_ITEM}" when the item position is invalid after updating the item properties or attributes`, () => {
    const allItems = Object.values(state.scene.layers[LAYER_ID].items) as any;
    let item = allItems[0];
    let ITEM_POSITION_VALIDITY = Item.isSelectedItemInValidPosition(state.scene, item.id);
    expect(ITEM_POSITION_VALIDITY).toBeTruthy();

    const newProperties = Object.entries(item.properties).reduce((acc, [key, properties]: any) => {
      if (properties != null) {
        properties = {
          ...properties,
          value: properties.value * 2,
        };
        acc[key] = properties;
      }
      return acc;
    }, {});
    item = {
      ...item,
      properties: newProperties,
    };

    let updatedState = {
      ...state,
      scene: {
        ...state.scene,
        layers: {
          ...state.scene.layers,
          [LAYER_ID]: {
            ...state.scene.layers[LAYER_ID],
            items: {
              ...state.scene.layers[LAYER_ID].items,
              [item.id]: item,
            },
          },
        },
      },
    };
    updatedState = Item.invalidPositionToDraggingMode(state, updatedState, item.id).updatedState;
    ITEM_POSITION_VALIDITY = Item.isSelectedItemInValidPosition(updatedState.scene, item.id);

    expect(updatedState.mode).toEqual(MODE_DRAGGING_ITEM);
    expect(ITEM_POSITION_VALIDITY).toBeFalsy();
  });
});

describe('Copying items', () => {
  it('Copying an item should have the same rotation and properties as the item thats being copied from', () => {
    jest.spyOn(Item, 'isSelectedItemInValidPosition');
    Item.isSelectedItemInValidPosition.mockImplementation(() => {
      return true;
    });

    let state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {}, catalog: MyCatalog });
    const layer = state.scene.layers[LAYER_ID];

    const itemID = Object.keys(layer.items)[0];
    const item = layer.items[itemID];

    state = Item.select(state, LAYER_ID, itemID).updatedState;
    state = Item.copySelectedItem(state).updatedState;

    let drawingSupport = state.drawingSupport;
    const attributes = drawingSupport.attributes;
    const properties = drawingSupport.properties;

    Object.entries(attributes).forEach(([key, value]) => expect(item[key]).toStrictEqual(value));
    Object.entries(properties).forEach(([key, value]) => expect(item.properties[key]).toStrictEqual(value));

    state = Item.updateDrawingItem(state, LAYER_ID, item.x, item.y).updatedState;
    drawingSupport = state.drawingSupport;

    expect(drawingSupport.attributes).toEqual(attributes);
    expect(drawingSupport.properties).toEqual(properties);

    const createdItemId = state.scene.layers[LAYER_ID].selected.items[0];
    const createdItem = state.scene.layers[LAYER_ID].items[createdItemId];

    Object.entries(attributes).forEach(([key, value]) => expect(createdItem[key]).toStrictEqual(value));
    Object.entries(properties).forEach(([key, value]) => expect(createdItem.properties[key]).toStrictEqual(value));
    const allItems = Object.values(state.scene.layers[LAYER_ID].items);
    expect(allItems.length).toBe(2);
  });
});

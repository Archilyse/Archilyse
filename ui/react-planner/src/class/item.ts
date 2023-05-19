import { Feature, Polygon } from 'geojson';
import * as GeometryUtils from '../utils/geometry';
import * as history from '../utils/history';
import cloneDeep from '../utils/clone-deep';
import IDBroker from '../utils/id-broker';
import NameGenerator from '../utils/name-generator';
import * as SnapSceneUtils from '../utils/snap-scene';
import * as SnapUtils from '../utils/snap';
import { getSelected, getSelectedLayer } from '../utils/state-utils';
import {
  METRICS_EVENTS,
  MIN_ITEM_LENGTH,
  MIN_ITEM_WIDTH,
  MODE_DRAGGING_ITEM,
  MODE_DRAWING_ITEM,
  MODE_IDLE,
  MODE_ROTATING_ITEM,
  PrototypesEnum,
} from '../constants';
import { Item as ItemType, Scene as SceneType, State as StateType, UpdatedStateObject } from '../types';
import { ProviderMetrics } from '../providers';
import Layer from './layer';
import Area from './area';

const MAXIMUM_OVERLAP_PERCENTAGE_ALLOWED = 0.005;

class Item {
  static create(state, layerID, type, x, y, rotation, properties = undefined): UpdatedStateObject & { item: ItemType } {
    const itemID = IDBroker.acquireID();

    const item = state.catalog.factoryElement(
      type,
      {
        id: itemID,
        name: NameGenerator.generateName('items', state.catalog.elements[type].info.title),
        type,
        x,
        y,
        rotation,
      },
      properties
    );

    state.scene.layers[layerID].items[itemID] = item;
    return { updatedState: state, item };
  }

  static duplicate(state, layerID, originalItem): UpdatedStateObject & { newElement: ItemType } {
    const { updatedState, item: newElement } = Item.create(
      state,
      layerID,
      originalItem.type,
      originalItem.x,
      originalItem.y,
      originalItem.rotation,
      originalItem.properties
    );

    return { updatedState, newElement };
  }

  static updateLengthMeasuresSelectedItems(state, { width = 0, length = 0 }): UpdatedStateObject {
    const item = getSelected(state.scene, PrototypesEnum.ITEMS);

    const currentWidth = item.properties.width.value;
    const currentLength = item.properties.length.value;

    const newWidth = currentWidth + width < MIN_ITEM_WIDTH ? currentWidth : currentWidth + width;
    const newLength = currentLength + length < MIN_ITEM_LENGTH ? currentLength : currentLength + length;

    const updatedLengthMeasures = {
      width: { value: newWidth },
      length: { value: newLength },
    };

    const selectedLayerID = state.scene.selectedLayer;
    state = this.updateProperties(state, selectedLayerID, item.id, updatedLengthMeasures).updatedState;

    return { updatedState: state };
  }

  static select(state, layerID, itemID, options = { unselectAllBefore: true }): UpdatedStateObject {
    if (options.unselectAllBefore) {
      state = Layer.select(state, layerID).updatedState;
    }
    state = Layer.selectElement(state, layerID, 'items', itemID).updatedState;

    return { updatedState: state };
  }

  static remove(state, layerID, itemID): UpdatedStateObject {
    state = this.unselect(state, layerID, itemID).updatedState;
    state = Layer.removeElement(state, layerID, 'items', itemID).updatedState;

    return { updatedState: state };
  }

  static unselect(state, layerID, itemID): UpdatedStateObject {
    state = Layer.unselect(state, layerID, 'items', itemID).updatedState;

    return { updatedState: state };
  }

  static selectToolDrawingItem(state, sceneComponentType): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    state = Layer.unselectAll(state, selectedLayer).updatedState;

    if (state.mode === MODE_DRAWING_ITEM) {
      const sceneHistory = state.sceneHistory;
      const isDrawing = state.drawingSupport.drawingStarted;
      const sceneHistoryIsNotEmpty = sceneHistory.list.length !== 0;

      if (sceneHistoryIsNotEmpty && isDrawing) {
        state.scene = sceneHistory.last;
        state.sceneHistory = history.historyPop(sceneHistory);
      }
    }

    state.mode = MODE_DRAWING_ITEM;
    state.drawingSupport = {
      type: sceneComponentType,
    };

    return { updatedState: state };
  }

  static isSelectedItemInValidPosition(scene: SceneType, itemID = null): boolean {
    let item;
    if (!itemID) {
      item = getSelected(scene, PrototypesEnum.ITEMS);
    } else {
      const layerID = scene.selectedLayer;
      item = scene.layers[layerID].items[itemID];
    }
    if (!item) {
      const selectedLayer = getSelectedLayer(scene);
      const selected = selectedLayer.selected[PrototypesEnum.ITEMS];
      const allItems: ItemType[] = Object.values(selectedLayer.items);
      const itemIDs = allItems.map(item => item.id);
      console.error(`No item while checking position, Selection: ${selected}, Layer items: ${itemIDs}`);
      return false;
    }

    const areaPolygon = Area.getAreaIntersectingCoordinates(scene, item.x, item.y);
    if (!areaPolygon) {
      return false;
    }
    const itemWidthInPx = GeometryUtils.getElementWidthInPixels(item, scene.scale);
    const itemLengthInPx = GeometryUtils.getElementLengthInPixels(item, scene.scale);

    const itemPolygon = GeometryUtils.getItemPolygon(
      item.x,
      item.y,
      item.rotation,
      itemWidthInPx,
      itemLengthInPx
    ) as Feature<Polygon>;

    const intersection = GeometryUtils.intersect(itemPolygon, areaPolygon);
    const intersectionSize = GeometryUtils.getFeatureSize(intersection);
    const itemSize = GeometryUtils.getFeatureSize(itemPolygon);
    const sizeDiff = Math.abs(intersectionSize - itemSize);
    const overlapPercentage = sizeDiff / itemSize;
    if (overlapPercentage > MAXIMUM_OVERLAP_PERCENTAGE_ALLOWED) {
      return false;
    }
    return true;
  }

  static updateDrawingItem(state, layerID, x, y): UpdatedStateObject {
    ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);

    const itemID = state.scene.layers[layerID].selected.items[0];
    state = this.addItemSnaps(state, layerID, itemID).updatedState;
    const snap = SnapUtils.nearestSnap(state.snapElements, x, y, state.snapMask);
    const itemAngle = this.getItemAngle(state.scene.layers[layerID].items[itemID], snap);

    if (snap) {
      ({ x, y } = snap.point);
    }

    if (itemID) {
      state.scene.layers[layerID].items[itemID].x = x;
      state.scene.layers[layerID].items[itemID].y = y;
      state.scene.layers[layerID].items[itemID].rotation = itemAngle;
    } else {
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      state.drawingSupport.drawingStarted = true;

      const { updatedState: stateI, item } = this.create(state, layerID, state.drawingSupport.type, x, y, itemAngle);
      state = Item.select(stateI, layerID, item.id).updatedState;

      const properties = state.drawingSupport.properties;
      if (properties) {
        state = this.setProperties(state, layerID, item.id, properties).updatedState;
      }

      const attributes = state.drawingSupport.attributes;
      if (attributes) {
        state = this.setAttributes(state, layerID, item.id, attributes).updatedState;
      }
    }
    return { updatedState: state };
  }

  static invalidateCurrentItem(state, newMode): UpdatedStateObject {
    const sceneHistory = state.sceneHistory;

    state.mode = newMode;
    state.scene = sceneHistory.last;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.sceneHistory = history.historyPop(sceneHistory);

    return { updatedState: state };
  }

  static endDrawingItem(state: StateType, layerID, x, y): UpdatedStateObject {
    if (!this.isSelectedItemInValidPosition(state.scene)) {
      return this.invalidateCurrentItem(state, MODE_DRAWING_ITEM);
    }
    state = this.updateDrawingItem(state, layerID, x, y).updatedState;
    state = Layer.unselectAll(state, layerID).updatedState;
    state = this.clearSnaps(state).updatedState;

    ProviderMetrics.endTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
    return { updatedState: state };
  }

  static areaSnappingParameters(
    state,
    item
  ): { itemDimensions: { width: number; length: number }; snapAngle: 90 | 180 } {
    const scale = state.scene.scale;

    const invertedCases = ['stairs', 'elevator'];
    if (invertedCases.includes(item.type)) {
      const width = GeometryUtils.getElementWidthInPixels(item, scale);
      const length = GeometryUtils.getElementWidthInPixels(item, scale);
      return {
        itemDimensions: { width, length },
        snapAngle: 90,
      };
    } else {
      const width = GeometryUtils.getElementWidthInPixels(item, scale);
      const length = GeometryUtils.getElementLengthInPixels(item, scale);
      return {
        itemDimensions: { width, length },
        snapAngle: 180,
      };
    }
  }

  static addAreaSnapping(state, snapElements, item): UpdatedStateObject {
    const { itemDimensions, snapAngle } = this.areaSnappingParameters(state, item);
    return SnapSceneUtils.sceneSnapAreasBordersItems(
      state.scene,
      snapElements,
      item.x,
      item.y,
      itemDimensions,
      snapAngle
    );
  }

  static addItemSnaps(state, layerID, itemID): UpdatedStateObject {
    const item = state.scene.layers[layerID].items[itemID];
    if (!item) {
      return { updatedState: state };
    }
    let snapElements = SnapSceneUtils.sceneSnapItemWithItems(state.scene, [], state.snapMask, item);

    if (item.type != 'shaft') {
      snapElements = this.addAreaSnapping(state, snapElements, item);
    }

    state.snapElements = snapElements;

    return { updatedState: state };
  }

  static clearSnaps(state): UpdatedStateObject {
    state.snapElements = [];

    return { updatedState: state };
  }

  static beginDraggingItem(state, layerID, itemID, x, y): UpdatedStateObject {
    const item = state.scene.layers[layerID].items[itemID];
    state.mode = MODE_DRAGGING_ITEM;
    state.draggingSupport = {
      layerID,
      itemID,
      startPointX: x,
      startPointY: y,
      originalX: item.x,
      originalY: item.y,
    };
    state = Item.select(state, layerID, itemID).updatedState;
    return { updatedState: state };
  }

  static updateDraggingItem(state, x, y): UpdatedStateObject {
    const { draggingSupport, scene } = state;

    const layerID = draggingSupport.layerID;
    const itemID = draggingSupport.itemID;
    state = this.addItemSnaps(state, layerID, itemID).updatedState;

    const snap = SnapUtils.nearestSnap(state.snapElements, x, y, state.snapMask);
    const itemAngle = this.getItemAngle(state.scene.layers[layerID].items[itemID], snap);
    if (snap) {
      ({ x, y } = snap.point);
    }

    const item = scene.layers[layerID].items[itemID];
    item.x = x;
    item.y = y;
    item.rotation = itemAngle;
    state.scene.layers[layerID].items[itemID] = item;

    return { updatedState: state };
  }

  static endDraggingItem(state, x, y): UpdatedStateObject {
    if (!this.isSelectedItemInValidPosition(state.scene)) {
      return this.invalidateCurrentItem(state, MODE_DRAGGING_ITEM);
    }
    state = this.updateDraggingItem(state, x, y).updatedState;
    state = this.clearSnaps(state).updatedState;
    state.draggingSupport = {};
    state.mode = MODE_IDLE;

    return { updatedState: state };
  }

  static beginRotatingItem(state, layerID, itemID, x, y): UpdatedStateObject {
    state.mode = MODE_ROTATING_ITEM;
    state.rotatingSupport = {
      layerID,
      itemID,
    };

    return { updatedState: state };
  }

  static updateRotatingItem(state, x, y): UpdatedStateObject {
    const { rotatingSupport } = state;

    const layerID = rotatingSupport.layerID;
    const itemID = rotatingSupport.itemID;
    const item = state.scene.layers[layerID].items[itemID];

    const deltaX = x - item.x;
    const deltaY = y - item.y;
    let rotation = (Math.atan2(deltaY, deltaX) * 180) / Math.PI - 90;

    if (-5 < rotation && rotation < 5) rotation = 0;
    if (-95 < rotation && rotation < -85) rotation = -90;
    if (-185 < rotation && rotation < -175) rotation = -180;
    if (85 < rotation && rotation < 90) rotation = 90;
    if (-270 < rotation && rotation < -265) rotation = 90;

    item.rotation = rotation;
    state.scene.layers[layerID].items[itemID] = item;

    return { updatedState: state };
  }

  static endRotatingItem(state, x, y): UpdatedStateObject {
    if (!this.isSelectedItemInValidPosition(state.scene)) {
      return this.invalidateCurrentItem(state, MODE_ROTATING_ITEM);
    }
    state = this.updateRotatingItem(state, x, y).updatedState;
    state.mode = MODE_IDLE;

    return { updatedState: state };
  }

  static copySelectedItem(state: StateType): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;

    const item = getSelected(state.scene, PrototypesEnum.ITEMS);
    if (!item) return { updatedState: state };

    /**
     * @TODO: this can be removed once DI-1055 is merged
     * since the unselect action will be done inside selectToolDrawingItem
     */
    state = this.unselect(state, layerID, item.id).updatedState;

    state = this.selectToolDrawingItem(state, item.type).updatedState;

    state.drawingSupport.properties = item.properties;
    state.drawingSupport.attributes = { rotation: item.rotation };

    return { updatedState: state };
  }

  static getItemAngle(item, snap): number {
    let defaultAngle = 0;
    if (item) {
      defaultAngle = item.rotation;
    }
    if (snap && snap.snap.metadata?.SnappingAngle) {
      defaultAngle = snap.snap.metadata.SnappingAngle;
    }
    return defaultAngle;
  }

  static invalidPositionToDraggingMode(prevState, updatedState, itemID): UpdatedStateObject {
    if (!this.isSelectedItemInValidPosition(updatedState.scene, itemID)) {
      // If the user modifies the size of a selected item, we need to re-enter the state in the history
      // as otherwise we will be 2 steps behind
      if (updatedState.mode === MODE_IDLE) {
        const selectedLayer = updatedState.scene.selectedLayer;
        updatedState = this.beginDraggingItem(updatedState, selectedLayer, itemID, 0, 0).updatedState;
        updatedState.sceneHistory = history.historyPush(updatedState.sceneHistory, prevState.scene);
      }
    }

    return { updatedState };
  }

  static setProperties(state, layerID, itemID, properties): UpdatedStateObject {
    const previousState = cloneDeep(state);
    state.scene.layers[layerID].items[itemID].properties = {
      ...state.scene.layers[layerID].items[itemID].properties,
      ...properties,
    };

    state = this.invalidPositionToDraggingMode(previousState, state, itemID).updatedState;
    return { updatedState: state };
  }

  static updateProperties(state, layerID, itemID, properties): UpdatedStateObject {
    const previousState = cloneDeep(state);

    Object.entries(properties).forEach(([k, v]) => {
      const itemHasProperty = state.scene.layers[layerID].items[itemID].properties.hasOwnProperty(k);
      if (itemHasProperty) {
        state.scene.layers[layerID].items[itemID].properties = {
          ...state.scene.layers[layerID].items[itemID].properties,
          [k]: v,
        };
      }
    });
    state = this.invalidPositionToDraggingMode(previousState, state, itemID).updatedState;
    return { updatedState: state };
  }

  static setAttributes(state, layerID, itemID, itemAttributes): UpdatedStateObject {
    const previousState = cloneDeep(state);

    state.scene.layers[layerID].items[itemID] = { ...state.scene.layers[layerID].items[itemID], ...itemAttributes };

    state = this.invalidPositionToDraggingMode(previousState, state, itemID).updatedState;
    return { updatedState: state };
  }

  static changeItemType(state, itemId, itemType): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    state.scene.layers[selectedLayer].items[itemId].type = itemType;

    return { updatedState: state };
  }

  static changeItemsType(state, itemIds, itemType): UpdatedStateObject {
    itemIds.forEach(itemId => {
      state = this.changeItemType(state, itemId, itemType).updatedState;
    });
    return { updatedState: state };
  }
}

export { Item as default };

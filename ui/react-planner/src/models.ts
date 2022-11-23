import { Position } from 'geojson';
import {
  INITIAL_BACKGROUND_HEIGHT,
  INITIAL_BACKGROUND_ROTATION,
  INITIAL_BACKGROUND_WIDTH,
  INITIAL_SCENE_HEIGHT,
  INITIAL_SCENE_WIDTH,
  MODE_IDLE,
  OPENING_TYPE,
  PAGE_SIZES,
  PrototypesEnum,
} from './constants';
import { Background, Selection as SelectionType } from './types';
import isObjectEmpty from './utils/is-object-empty';

import { SNAP_MASK } from './utils/snap';

const safeLoadMapList = (mapList: any, Model, defaultMap = undefined) => {
  if (!mapList) return defaultMap || {};
  const newMapList = Object.values(mapList).reduce((acc, current: any) => {
    acc[current.id || current.name] = new Model(current); // @TODO: Hack, all maps are initialized with the id but the elements one, who uses the name
    return acc;
  }, {});
  return newMapList;
};

export class Grid {
  id: string;
  type: string;
  properties: {
    step: number;
    colors: string[];
  };

  constructor(json: Partial<Grid> | any = {}) {
    return {
      ...json,
      properties: json.properties || {},
    };
  }
}

export const DefaultGrids = {
  h1: new Grid({
    id: 'h1',
    type: 'horizontal-streak',
    properties: {
      step: 20,
      colors: ['#808080', '#ddd', '#ddd', '#ddd', '#ddd'],
    },
  }),
  v1: new Grid({
    id: 'v1',
    type: 'vertical-streak',
    properties: {
      step: 20,
      colors: ['#808080', '#ddd', '#ddd', '#ddd', '#ddd'],
    },
  }),
};

export class ElementsSet {
  vertices: string[];
  lines: string[];
  holes: string[];
  areas: string[];
  items: string[];

  constructor(json: Partial<ElementsSet> = {}) {
    this.vertices = json.vertices || [];
    this.lines = json.lines || [];
    this.holes = json.holes || [];
    this.areas = json.areas || [];
    this.items = json.items || [];
  }
}

export class ElementPrototype {
  id: string;
  type: string;
  prototype: typeof PrototypesEnum[keyof typeof PrototypesEnum];
  name: string;
  selected: boolean;
  properties: any; // @TODO

  constructor({ id, type, prototype, name, selected, properties }: any) {
    // @TODO
    this.id = id || '';
    this.type = type || '';
    this.prototype = prototype || '';
    this.name = name || '';
    this.selected = selected || false;
    this.properties = properties || {};
  }
}

export class Vertex extends ElementPrototype {
  x: number;
  y: number;
  prototype: typeof PrototypesEnum.VERTICES = PrototypesEnum.VERTICES;
  lines: string[];

  constructor(json: Partial<Vertex> = {}) {
    super({ ...json });
    this.lines = json.lines || [];
    this.x = json.x;
    this.y = json.y;
  }
}

export class Line extends ElementPrototype {
  prototype: typeof PrototypesEnum.LINES = PrototypesEnum.LINES;
  vertices: string[];
  auxVertices: string[];
  holes: string[];
  coordinates: Position[][];

  constructor(json: Partial<Line> = {}) {
    super({ ...json });
    this.vertices = json.vertices || [];
    this.auxVertices = json.auxVertices || []; // @TODO: Put everything inside vertices again if needed after backend is compatible
    this.holes = json.holes || [];
    this.coordinates = json.coordinates || [];
  }
}

type OpeningType = typeof OPENING_TYPE[keyof typeof OPENING_TYPE];
export class Hole extends ElementPrototype {
  type: OpeningType; // @TODO: Override type in the rest of the prototypes also?
  prototype: typeof PrototypesEnum.HOLES = PrototypesEnum.HOLES;
  line: string;
  coordinates: Position[][];
  door_sweeping_points?: {
    angle_point: [number, number];
    closed_point: [number, number];
    opened_point: [number, number];
  };
  constructor(json: Partial<Hole> = {}) {
    super({ ...json });
    this.coordinates = json.coordinates;
    this.type = json.type;
    this.line = json.line;
    this.door_sweeping_points = json.door_sweeping_points;
  }
}

export class Area extends ElementPrototype {
  isScaleArea: boolean;
  prototype: typeof PrototypesEnum.AREAS = PrototypesEnum.AREAS;
  coords: Position[][];
  holes: number[]; // @TODO: Unused, erase it from the state

  constructor(json: Partial<Area> = {}) {
    super({ ...json });
    this.isScaleArea = json.isScaleArea || false;
    this.coords = json.coords || []; // Polygon geojson coordinates: https://datatracker.ietf.org/doc/html/rfc7946#appendix-A.3 @TODO: Rename to "coordinates"
  }
}

export class Item extends ElementPrototype {
  x: number;
  y: number;
  prototype: typeof PrototypesEnum.ITEMS = PrototypesEnum.ITEMS;
  rotation: number;

  constructor(json: Partial<Item> = {}) {
    super({ ...json });
    this.x = json.x;
    this.y = json.y;
    this.rotation = json.rotation;
  }
}

export class Layer {
  id: string;
  order: number; // @TODO: Not used, erase it
  opacity: number; // @TODO: Not used, erase it
  name: string;
  vertices: { [id: string]: Vertex };
  lines: { [id: string]: Line };
  holes: { [id: string]: Hole };
  areas: { [id: string]: Area };
  items: { [id: string]: Item };
  selected: ElementsSet;

  constructor(json: Layer | Record<string, any> = {}) {
    this.id = json.id || '';
    this.order = json.order || 0;
    this.opacity = json.opacity || 1;
    this.name = json.name || '';
    this.vertices = safeLoadMapList(json.vertices, Vertex);
    this.lines = safeLoadMapList(json.lines, Line);
    this.holes = safeLoadMapList(json.holes, Hole);
    this.areas = safeLoadMapList(json.areas, Area);
    this.items = safeLoadMapList(json.items, Item);
    this.selected = new ElementsSet(json.selected);
  }
}

export const DefaultLayers = { 'layer-1': new Layer({ id: 'layer-1', name: 'default' }) };

export class SiteStructure {
  client_site_id?: string;
  site: { id: number; name: string };
  building: { id: number; housenumber: string; street: string };
  floors: { plan_id: number; floor_number: number }[];
  planId: number;
  enforce_masterplan?: boolean;

  constructor(json: Partial<SiteStructure> = {}) {
    this.client_site_id = json.client_site_id || '';
    this.site = json.site;
    this.building = json.building;
    this.floors = json.floors;
    this.enforce_masterplan = json.enforce_masterplan || false;
  }
}

const DEFAULT_BACKGROUND = {
  width: INITIAL_BACKGROUND_WIDTH,
  height: INITIAL_BACKGROUND_HEIGHT,
  rotation: INITIAL_BACKGROUND_ROTATION,
  shift: {
    x: 0,
    y: 0,
  },
};
export class Scene {
  unit: string;
  scale: number;
  background: Background;
  paperFormat: keyof typeof PAGE_SIZES | '';
  scaleRatio: number | null;
  layers: { [key: string]: Layer };
  grids: { [key: string]: Grid };
  selectedLayer: string;
  groups: any; // @TODO: Deprecated
  width: number;
  height: number;
  meta: any;
  guides: any; // @TODO: Probably deprecated, check and delete
  version: string;

  constructor(json: Partial<Scene> = {}) {
    const layers: Scene['layers'] = safeLoadMapList(json.layers, Layer, DefaultLayers);
    this.unit = 'cm';
    this.scale = 1; // Initial scale, 1 for the sake of drawing with the `scale-tool` properly
    this.scaleRatio = null;
    this.paperFormat = '';
    this.width = INITIAL_SCENE_WIDTH;
    this.height = INITIAL_SCENE_HEIGHT;
    this.grids = safeLoadMapList(json.grids, Grid, DefaultGrids);
    this.layers = layers;
    this.selectedLayer = Object.values(layers)[0].id;
    this.background = json.background || DEFAULT_BACKGROUND;
    this.groups = {};
    this.meta = json.meta || {};
    this.guides = json.guides || { horizontal: {}, vertical: {}, circular: {} };
    this.version = 'V19';
    return {
      ...this,
      ...json,
    };
  }
}

export class CatalogElement {
  name = '';
  prototype = '';
  info: any = {};
  properties: any = {};

  // @TODO: CatalogElement type
  constructor(json: any = {}) {
    return {
      ...this, // Not sure if this is correct...
      ...json,
    };
  }
}

export class Catalog {
  ready: boolean;
  path: any[];
  elements: {};

  // @TODO: Catalog type
  constructor(json: any = {}) {
    const elements = safeLoadMapList(json.elements, CatalogElement);
    this.elements = elements;
    this.ready = !isObjectEmpty(elements);
    return {
      ready: this.ready,
      path: this.path,
      elements: this.elements,
      factoryElement: this.factoryElement,
    };
  }

  factoryElement(type, options, initialProperties) {
    if (!Object.keys(this.elements).includes(type)) {
      const catList = Object.keys(this.elements).toString();
      throw new Error(`Element ${type} does not exist in catalog ${catList}`);
    }

    const element = this.elements[type];
    const properties = Object.entries(element.properties).reduce((acc, [key, value]: [string, any]) => {
      const elementHasProperty = initialProperties && initialProperties[key];
      acc[key] = elementHasProperty ? initialProperties[key] : value.defaultValue;
      return acc;
    }, {});

    switch (element.prototype) {
      case 'lines':
        return { ...new Line(options), properties };

      case 'holes':
        return { ...new Hole(options), properties };

      case 'areas':
        return { ...new Area(options), properties };

      case 'items':
        return { ...new Item(options), properties };

      default:
        throw new Error('prototype not valid');
    }
  }
}

export class HistoryStructure {
  list: Scene[];
  first: Scene;
  last: Scene;

  constructor(json: HistoryStructure | Record<any, any> = {}, Model = Scene) {
    this.list = json.list || [];
    this.first = new Model(json.first);
    this.last = new Model(json.last);
  }
}
export class CopyPaste {
  selection: SelectionType = {
    startPosition: { x: -1, y: -1 }, // @TODO: Rename to `startDrawingPosition` or something like that
    endPosition: { x: -1, y: -1 }, // @TODO: Rename to `endDrawingPosition` or something like that
    draggingPosition: { x: -1, y: -1 }, // This is the center of the rectangle when dragging it
    lines: [],
    items: [],
    holes: [],
    rotation: 0,
  };
  drawing = false;
  dragging = false;
  rotating = false;

  constructor(json: Partial<CopyPaste> = {}) {
    return {
      ...this,
      ...json,
    };
  }
}

export class RectangleSelectTool {
  selection = {
    startPosition: { x: -1, y: -1 },
    endPosition: { x: -1, y: -1 },
  };
  drawing: false;
  constructor(json: Partial<RectangleSelectTool> = {}) {
    return {
      ...this,
      ...json,
    };
  }
}

export class State {
  // @TODO: Type this as much as possible
  availableAreaTypes = [];
  annotationFinished = false;
  floorplanImgUrl: string;
  floorplanDimensions: { width: null; height: null };
  mode = MODE_IDLE;
  scaleValidated = false;
  scaleTool = { distance: 0, areaSize: 0, userHasChangedMeasures: false };
  scene = new Scene();
  sceneHistory = new HistoryStructure();
  catalog = new Catalog();
  catalogToolbarOpened = false;
  viewer2D = {};
  zoom = 0;
  projectHashCode = null;
  snapMask = SNAP_MASK;
  snapElements = [];
  centered = false;
  copyPaste = new CopyPaste();
  rectangleTool = new RectangleSelectTool();
  showSnapElements = true; // Show snap elements as red lines while drawing
  activeSnapElement = null;
  drawingSupport:
    | {
        type: string;
        layerID: 'layer-1';
        drawingStarted: boolean;
        properties?: Item['properties'];
        attributes?: any; // Probably this attributes are item properties
      }
    | Record<string, any>;
  draggingSupport = {};
  rotatingSupport = {};
  errors = [];
  warnings = [];
  lastWidth = undefined;
  siteStructure = new SiteStructure();
  floorScales = [];
  clipboardProperties = {};
  selectedElementsHistory = [];
  misc = {}; //additional info // @TODO: Delete
  alterate = false;
  showBackgroundOnly = false;
  requestStatus = {};
  highlightedError = '';
  validationErrors = [];
  planInfo: any = {}; // @TODO: Type
  snackbar = { open: false, message: null, severity: '', duration: undefined };
  ctrlActive = false;
  mustImportAnnotations = false;

  constructor(json: Partial<State> = {}) {
    return {
      ...this, // Not sure if this is correct...
      ...json,
      floorplanImgUrl: json.floorplanImgUrl || '',
      floorplanDimensions: json.floorplanDimensions || { width: null, height: null },
      snapMask: json.snapMask ? json.snapMask : SNAP_MASK,
      scaleValidated: json.scaleValidated || false,
      planInfo: json.planInfo,
      mode: json.mode || MODE_IDLE,
      siteStructure: new SiteStructure(json.siteStructure),
      scene: new Scene(json.scene),
      sceneHistory: new HistoryStructure(json.sceneHistory || { first: json.scene, last: json.scene }, Scene),
      copyPaste: new CopyPaste(),
      rectangleTool: new RectangleSelectTool(),
      snapElements: json.snapElements || [],
      catalog: new Catalog(json.catalog || {}),
      viewer2D: json.viewer2D || {},
      drawingSupport: json.drawingSupport || {},
      draggingSupport: json.draggingSupport || {},
      rotatingSupport: json.rotatingSupport || {},
      misc: json.misc || {},
      mustImportAnnotations: json.mustImportAnnotations || false,
    };
  }
}
